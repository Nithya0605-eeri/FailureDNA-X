"""
AI hypothesis generation: the Nemotron investigator.

Each turn it receives the VIEW (see schemas.py), sends it to the model, and turns the reply into an Action:
  - run_tool:          with a hypothesis (current suspects) and a reason (what the test will show)
  - submit_diagnosis:  with a cause, confidence, cited result IDs and an explanation
Every reply is validated. An invalid reply gets ONE retry with the error message. If it still fails,
we return Action(tool="__invalid__") and the investigation loop falls back to its own choice.
"""
import json
import re
import time
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError

from .nemotron1 import make_client
from .schemas import Action

SYSTEM_PROMPT = """You are FailureDNA X, an expert GPU reliability engineer investigating a slow training job.

Goal: identify the root cause using the FEWEST and CHEAPEST diagnostic tests.
Possible causes are listed in "hypotheses": thermal_throttling, memory_pressure, network_congestion, no_fault.

Rules:
- Each turn, either run exactly ONE tool from "tools", or submit a diagnosis.
- Never run a tool listed in "already_run".
- Prefer cheap tests that best separate your top suspects; skip expensive tests that cannot change your conclusion.
- "beliefs" are probabilities from a deterministic evidence engine. Use them, but reason for yourself.
- Submit when one cause is clearly supported (near "stop_threshold") or when no affordable test could change the answer.
- Base the diagnosis only on the evidence and cite the result_id values that support it. Never invent measurements.
- no_fault is a valid answer when nothing abnormal is found.

Reply with ONE JSON object and nothing else, in one of these two forms:
{"action": "run_tool", "hypothesis": "<the 1-2 causes you suspect most, and why>", "tool": "<tool name>", "reason": "<what this test will confirm or rule out>"}
{"action": "submit_diagnosis", "cause": "<one of the hypotheses>", "confidence": <number 0-1>, "cited_result_ids": ["r1"], "explanation": "<two sentences max>"}
"""


class RunTool(BaseModel):
    action: Literal["run_tool"]
    tool: str
    hypothesis: str = ""
    reason: str = ""


class SubmitDiagnosis(BaseModel):
    action: Literal["submit_diagnosis"]
    cause: str
    confidence: float = Field(ge=0, le=1)
    cited_result_ids: list[str]
    explanation: str = ""


def extract_json(text: str) -> dict:
    """Find the first JSON object in a reply. Removes <think>...</think> and ``` fences first."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise ValueError("no JSON object found in the reply")


def build_state(view: dict) -> dict:
    """Exactly what the model sees each turn. Only whitelisted keys, so the truth can never leak."""
    return {
        "symptom": view["symptom"],
        "hypotheses": view["hypotheses"],
        "tools": view["tools"],
        "already_run": view["already_run"],
        "evidence": [{k: e[k] for k in ("result_id", "tool", "summary", "measurements")} for e in view["evidence"]],
        "beliefs": {h: round(p, 3) for h, p in view["beliefs"].items()},
        "steps_left": view["steps_left"],
        "cost_left": view["cost_left"],
        "stop_threshold": view["stop_threshold"],
    }


class NemotronPolicy:
    def __init__(self, client=None):
        self.client = client or make_client()
        self.name = self.client.label  # "nemotron" or "mock_llm"

    def check(self, data: dict, view: dict) -> tuple[Optional[Action], Optional[str]]:
        """Validate one parsed reply. Returns (action, None) or (None, error message for the retry)."""
        tools = {t["name"]: t["cost"] for t in view["tools"]}
        try:
            if data.get("action") == "run_tool":
                a = RunTool(**data)
                if a.tool not in tools:
                    return None, f"Unknown tool {a.tool!r}. Valid tools: {sorted(tools)}."
                if a.tool in view["already_run"]:
                    return None, f"{a.tool} was already run. Choose another tool or submit_diagnosis."
                if tools[a.tool] > view["cost_left"]:
                    return None, f"{a.tool} costs {tools[a.tool]} but only {view['cost_left']} is left."
                return Action(kind="run_tool", tool=a.tool, hypothesis=a.hypothesis, reason=a.reason,
                              source=self.name), None
            if data.get("action") == "submit_diagnosis":
                d = SubmitDiagnosis(**data)
                valid_ids = {e["result_id"] for e in view["evidence"]}
                if d.cause not in view["hypotheses"]:
                    return None, f"cause must be one of {view['hypotheses']}."
                if not valid_ids:
                    return None, "Run at least one tool before submitting a diagnosis."
                if not d.cited_result_ids or any(c not in valid_ids for c in d.cited_result_ids):
                    return None, f"cited_result_ids must be a non-empty subset of {sorted(valid_ids)}."
                return Action(kind="submit_diagnosis", source=self.name, reason="Submitted diagnosis.",
                              diagnosis=d.model_dump(exclude={"action"})), None
            return None, 'Field "action" must be "run_tool" or "submit_diagnosis".'
        except ValidationError as e:
            return None, f"Invalid fields: {e.errors()[0]['msg']}"

    def next_action(self, view: dict) -> Action:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "STATE:\n" + json.dumps(build_state(view))},
        ]
        tokens, notes, t0 = 0, [], time.time()
        for attempt in (1, 2):  # first try + one retry
            text = ""
            try:
                text, used = self.client.complete(messages)
                tokens += used
                action, error = self.check(extract_json(text), view)
            except ValueError as e:      # reply had no JSON
                action, error = None, str(e)
            except Exception as e:       # network / API problem: don't retry, let the loop fall back
                notes.append(f"LLM call failed: {type(e).__name__}: {e}"[:300])
                break
            if action:
                action.tokens, action.notes = tokens, notes
                action.latency_ms = int((time.time() - t0) * 1000)
                return action
            notes.append(f"attempt {attempt}: {error}")
            messages += [
                {"role": "assistant", "content": text[:2000]},
                {"role": "user", "content": f"That reply was invalid: {error} Reply with one corrected JSON object only."},
            ]
        return Action(kind="run_tool", tool="__invalid__", source=self.name, tokens=tokens, notes=notes,
                      latency_ms=int((time.time() - t0) * 1000))
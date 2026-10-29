"""
The investigation loop that connects everything (Option A).

  simulator.py (hidden fault)  ->  diagnostics1.py (runs a test)  ->  evidence1.py (updates beliefs)
                 ^                                                          |
                 |                                   view (no truth)        v
           Investigation  <---------- Action ----------  investigator1.py (Nemotron or mock)

Each step: the AI picks a test, Python checks it, runs it on the hidden scenario, updates beliefs.
The hidden fault is revealed only when the investigation is complete.
"""
import time
import uuid
from typing import Optional

from . import evidence1
from .config import settings
from .diagnostics1 import FIXED_ORDER, TOOLS, execute_tool, tool_catalog
from .schemas import Action
from .simulator import FAULTS, generate_scenario


class InfoGainPolicy:
    """Non-LLM policy: the test with the most expected information per unit of cost. Also the AI's fallback."""
    name = "infogain"

    def next_action(self, view: dict) -> Action:
        cause, conf = evidence1.top(view["beliefs"])
        ranked = view["ranked_tools"]
        if view["evidence"] and (conf >= view["stop_threshold"] or not ranked):
            return Action(kind="submit_diagnosis", source="infogain",
                          diagnosis=supporting_diagnosis(view, cause, conf))
        best = ranked[0]
        return Action(kind="run_tool", tool=best["tool"], source="infogain",
                      reason=f"Most information per cost: {best['info_gain_bits']} bits for {best['cost']} units.")


class FixedPolicy:
    """Baseline: runs every test in a fixed checklist order, then reports the top belief."""
    name = "fixed"

    def next_action(self, view: dict) -> Action:
        for tool in FIXED_ORDER:
            if tool not in view["already_run"] and TOOLS[tool].cost <= view["cost_left"]:
                return Action(kind="run_tool", tool=tool, source="fixed", reason="Next item on the checklist.")
        cause, conf = evidence1.top(view["beliefs"])
        return Action(kind="submit_diagnosis", source="fixed", diagnosis=supporting_diagnosis(view, cause, conf))


def supporting_diagnosis(view: dict, cause: str, conf: float) -> dict:
    """A diagnosis citing the results whose observation favours `cause`."""
    cited = []
    for e in view["evidence"]:
        lik = evidence1.likelihoods()[e["tool"]].get(e["observation"])
        if lik:
            others = [lik[h] for h in FAULTS if h != cause]
            if lik[cause] > sum(others) / len(others):
                cited.append(e["result_id"])
    if not cited and view["evidence"]:
        cited = [view["evidence"][-1]["result_id"]]
    return {"cause": cause, "confidence": round(conf, 3), "cited_result_ids": cited,
            "explanation": f"Evidence engine: {cause} at {conf:.0%}."}


class Investigation:
    def __init__(self, seed: int, mode: str = "nemotron", fault: Optional[str] = None, severity: Optional[str] = None):
        self.id = uuid.uuid4().hex[:10]
        self.seed, self.mode = seed, mode
        self.scenario = generate_scenario(seed, fault, severity)
        self.beliefs = evidence1.uniform_prior()
        self.steps: list[dict] = []
        self.total_cost = 0
        self.status = "running"
        self.diagnosis: Optional[dict] = None
        self.correct: Optional[bool] = None
        self.baseline: Optional[dict] = None
        self.fallbacks = 0
        self.total_tokens = 0
        self.max_steps, self.max_cost, self.threshold = settings.max_steps, settings.max_cost, settings.stop_threshold

    # ---- what the AI may see (exactly the keys in schemas.py; never the truth) ----
    def view(self) -> dict:
        run = {s["tool"] for s in self.steps}
        cost_left = self.max_cost - self.total_cost
        return {
            "symptom": self.scenario.public().symptom,
            "hypotheses": FAULTS,
            "tools": tool_catalog(),
            "already_run": sorted(run),
            "evidence": [{k: s[k] for k in ("result_id", "tool", "summary", "measurements", "observation")}
                         for s in self.steps],
            "beliefs": self.beliefs,
            "steps_left": self.max_steps - len(self.steps),
            "cost_left": cost_left,
            "stop_threshold": self.threshold,
            "ranked_tools": evidence1.rank_tools(self.beliefs, run, cost_left),  # used by InfoGainPolicy only
        }

    def _valid_tool(self, tool: Optional[str]) -> bool:
        return (tool in TOOLS and tool not in {s["tool"] for s in self.steps}
                and TOOLS[tool].cost <= self.max_cost - self.total_cost)

    def _valid_diagnosis(self, d: Optional[dict]) -> bool:
        ids = {s["result_id"] for s in self.steps}
        return bool(d and d.get("cause") in FAULTS and ids and d.get("cited_result_ids")
                    and all(c in ids for c in d["cited_result_ids"]))

    def step(self, policy) -> None:
        if self.status == "complete":
            return
        view = self.view()
        if len(self.steps) >= self.max_steps or not view["ranked_tools"]:  # budget used up
            cause, conf = evidence1.top(self.beliefs)
            self._finish(supporting_diagnosis(view, cause, conf) | {"forced": True}, "engine")
            return

        action = policy.next_action(view)
        self.total_tokens += action.tokens

        if action.kind == "submit_diagnosis" and self._valid_diagnosis(action.diagnosis):
            self._finish(action.diagnosis, action.source, action.latency_ms)
            return
        if action.kind != "run_tool" or not self._valid_tool(action.tool):  # includes tool == "__invalid__"
            notes = action.notes + [f"rejected {action.kind} {action.tool!r}; used info-gain fallback"]
            action = InfoGainPolicy().next_action(view)
            action.source, action.notes = "fallback", notes
            self.fallbacks += 1
            if action.kind == "submit_diagnosis":
                self._finish(action.diagnosis, "fallback")
                return

        before = dict(self.beliefs)
        measurements, summary = execute_tool(action.tool, self.scenario)
        obs = evidence1.observe(action.tool, measurements)
        self.beliefs = evidence1.update(self.beliefs, action.tool, obs)
        self.total_cost += TOOLS[action.tool].cost
        self.steps.append({
            "index": len(self.steps) + 1, "result_id": f"r{len(self.steps) + 1}",
            "tool": action.tool, "cost": TOOLS[action.tool].cost,
            "hypothesis": action.hypothesis, "reason": action.reason, "source": action.source, "notes": action.notes,
            "measurements": measurements, "summary": summary, "observation": obs,
            "beliefs_before": before, "beliefs_after": self.beliefs,
            "latency_ms": action.latency_ms, "tokens": action.tokens,
        })

    def run(self, policy) -> None:
        for _ in range(self.max_steps + 2):
            if self.status == "complete":
                return
            self.step(policy)
        if self.status != "complete":
            cause, conf = evidence1.top(self.beliefs)
            self._finish(supporting_diagnosis(self.view(), cause, conf) | {"forced": True}, "engine")

    def _finish(self, diagnosis: dict, source: str, latency_ms: int = 0) -> None:
        self.diagnosis = dict(diagnosis) | {"source": source, "latency_ms": latency_ms}
        self.status = "complete"
        self.correct = self.diagnosis["cause"] == self.scenario.truth.fault

    # ---- what the API returns (truth only after completion) ----
    def public(self) -> dict:
        out = {
            "id": self.id, "seed": self.seed, "mode": self.mode, "status": self.status,
            "symptom": self.scenario.public().symptom, "steps": self.steps, "beliefs": self.beliefs,
            "total_cost": self.total_cost, "max_cost": self.max_cost, "stop_threshold": self.threshold,
            "tests_run": len(self.steps), "fallbacks": self.fallbacks, "total_tokens": self.total_tokens,
            "diagnosis": self.diagnosis, "truth": None, "correct": None, "baseline": self.baseline,
        }
        if self.status == "complete":
            t = self.scenario.truth
            out["truth"] = {"fault": t.fault, "gpu_id": t.gpu_id,
                            "severity": None if t.fault == "no_fault" else t.severity}
            out["correct"] = self.correct
        return out

    def attach_baseline(self) -> None:
        """Replay the SAME hidden scenario with the fixed checklist, for a side-by-side comparison."""
        if self.status != "complete" or self.baseline is not None:
            return
        t = self.scenario.truth
        base = Investigation(self.seed, "fixed", t.fault, t.severity)
        base.run(FixedPolicy())
        self.baseline = {"tests_run": len(base.steps), "total_cost": base.total_cost,
                         "predicted": base.diagnosis["cause"], "correct": base.correct}
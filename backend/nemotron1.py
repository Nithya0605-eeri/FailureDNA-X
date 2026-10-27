"""
How we talk to the language model.

TokenFactoryClient: NVIDIA Nemotron on Nebius Token Factory (OpenAI-compatible API).
MockLLMClient:      offline stand-in used when no API key is set. Always labelled "mock_llm".

Both have the same method:  complete(messages) -> (reply_text, tokens_used)
"""
import json

from .config import settings


class TokenFactoryClient:
    label = "nemotron"

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        from openai import OpenAI  # only needed when we really call the API

        self.model = model or settings.nemotron_model
        self.client = OpenAI(
            api_key=api_key or settings.nebius_api_key,
            base_url=base_url or settings.nebius_base_url,
            timeout=settings.llm_timeout_s,
            max_retries=2,
        )

    def complete(self, messages: list[dict]) -> tuple[str, int]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        text = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        return text, tokens


class MockLLMClient:
    """Answers in the same JSON format as Nemotron using simple rules, so everything works offline."""
    label = "mock_llm"

    def complete(self, messages: list[dict]) -> tuple[str, int]:
        state = json.loads(messages[-1]["content"].split("STATE:\n", 1)[1])
        ranked = sorted(state["beliefs"].items(), key=lambda kv: kv[1], reverse=True)
        (top, p_top), (second, _) = ranked[0], ranked[1]
        untried = [t for t in state["tools"]
                   if t["name"] not in state["already_run"] and t["cost"] <= state["cost_left"]]
        if state["evidence"] and (p_top >= state["stop_threshold"] or not untried):
            ids = [e["result_id"] for e in state["evidence"]]
            return json.dumps({"action": "submit_diagnosis", "cause": top, "confidence": round(p_top, 2),
                               "cited_result_ids": ids[-2:], "explanation": f"[mock] Evidence points to {top}."}), 0
        cheapest = min(untried, key=lambda t: t["cost"])  # rule: cheapest test first
        return json.dumps({"action": "run_tool",
                           "hypothesis": f"[mock] Leading suspects: {top} and {second}.",
                           "tool": cheapest["name"],
                           "reason": f"[mock] {cheapest['name']} is the cheapest test not yet run."}), 0


def make_client():
    """Real Nemotron if NEBIUS_API_KEY is set, otherwise the mock."""
    return TokenFactoryClient() if settings.nebius_api_key else MockLLMClient()
"""Tests that the halves work together: simulator + tests + beliefs + your AI + the API logic."""
import json

from backend import sim_service1
from backend.investigation1 import FixedPolicy, InfoGainPolicy, Investigation
from backend.investigator1 import NemotronPolicy
from backend.nemotron1 import MockLLMClient


class BrokenLLM:
    label = "broken"

    def complete(self, messages):
        raise TimeoutError("down")


class SpyLLM(MockLLMClient):
    """The mock AI, but it records everything it was sent."""
    def __init__(self):
        self.sent = []

    def complete(self, messages):
        self.sent.append(messages[-1]["content"])
        return super().complete(messages)


def test_full_investigation_with_mock_ai():
    inv = Investigation(seed=1, mode="nemotron")
    policy = NemotronPolicy(MockLLMClient())
    inv.step(policy)
    assert inv.public()["truth"] is None                      # hidden while running
    inv.run(policy)
    assert inv.status == "complete"
    assert inv.public()["truth"]["fault"] == "no_fault"       # seed 1 is no_fault (Step 3)
    assert all(s["hypothesis"] for s in inv.steps if s["source"] == "mock_llm")


def test_ai_never_sees_the_answer():
    spy = SpyLLM()
    inv = Investigation(seed=5, mode="nemotron", fault="memory_pressure", severity="severe")
    inv.run(NemotronPolicy(spy))
    assert spy.sent
    for text in spy.sent:
        assert "severe" not in text and "gpu_id" not in text and "truth" not in text


def test_ai_failure_still_finishes_with_fallback():
    inv = Investigation(seed=2, mode="nemotron")
    inv.run(NemotronPolicy(BrokenLLM()))
    assert inv.status == "complete"
    assert inv.fallbacks >= 1 and all(s["source"] == "fallback" for s in inv.steps)


def test_steps_have_what_the_charts_need():
    inv = Investigation(seed=3, mode="infogain")
    inv.run(InfoGainPolicy())
    for s in inv.steps:
        for key in ("result_id", "tool", "summary", "measurements", "observation", "beliefs_after"):
            assert key in s
    json.dumps(inv.public())  # the API response must be valid JSON


def test_fixed_runs_all_six_tests():
    inv = Investigation(seed=4, mode="fixed")
    inv.run(FixedPolicy())
    assert len(inv.steps) == 6 and inv.total_cost == 18


def test_service_flow_and_baseline():
    created = sim_service1.create("nemotron", seed=123)
    assert created["status"] == "running" and created["truth"] is None
    done = sim_service1.run(created["id"])
    assert done["status"] == "complete" and done["truth"] is not None
    assert done["baseline"]["tests_run"] == 6


def test_service_rejects_bad_mode():
    try:
        sim_service1.create("magic")
        assert False, "should have raised"
    except ValueError:
        pass
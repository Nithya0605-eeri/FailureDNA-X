import json

from backend.investigator1 import NemotronPolicy, build_state, extract_json
from backend.nemotron1 import MockLLMClient
from backend.simulator import FAULTS

TOOLS = [
    {"name": "get_job_summary", "description": "", "cost": 1},
    {"name": "check_thermals", "description": "", "cost": 1},
    {"name": "check_memory", "description": "", "cost": 2},
    {"name": "run_gpu_stress_test", "description": "", "cost": 8},
]


def make_view(evidence=None, beliefs=None, cost_left=18):
    """A hand-made view, so these tests don't need your teammate's code."""
    evidence = evidence or []
    return {
        "symptom": "Training job step time is 1.84x its normal baseline on a 4-GPU node. Find the root cause.",
        "hypotheses": FAULTS, "tools": TOOLS,
        "already_run": [e["tool"] for e in evidence], "evidence": evidence,
        "beliefs": beliefs or {f: 0.25 for f in FAULTS},
        "steps_left": 6 - len(evidence), "cost_left": cost_left, "stop_threshold": 0.9,
    }


R1 = {"result_id": "r1", "tool": "check_thermals", "summary": "Hottest GPU2 at 91.0C; throttle active on GPUs [2].",
      "measurements": {"temps_c": [64, 66, 91, 63]}, "observation": "hot|throttle"}


class ScriptedLLM:
    """A fake model that returns the replies we give it, in order."""
    label = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)

    def complete(self, messages):
        return (self.replies.pop(0) if self.replies else "no idea"), 10


class BrokenLLM:
    label = "broken"

    def complete(self, messages):
        raise TimeoutError("token factory timed out")


def test_valid_tool_choice_with_hypothesis():
    llm = ScriptedLLM(['{"action": "run_tool", "hypothesis": "thermal or network", "tool": "check_thermals", "reason": "cheap"}'])
    a = NemotronPolicy(llm).next_action(make_view())
    assert (a.kind, a.tool, a.hypothesis, a.source) == ("run_tool", "check_thermals", "thermal or network", "scripted")


def test_unknown_tool_retries_then_succeeds():
    llm = ScriptedLLM(['{"action": "run_tool", "tool": "rm -rf /"}',
                       '{"action": "run_tool", "tool": "check_memory", "reason": "ok"}'])
    a = NemotronPolicy(llm).next_action(make_view())
    assert a.tool == "check_memory" and "Unknown tool" in a.notes[0]


def test_repeated_tool_rejected():
    llm = ScriptedLLM(['{"action": "run_tool", "tool": "check_thermals"}'] * 2)
    a = NemotronPolicy(llm).next_action(make_view([R1]))
    assert a.tool == "__invalid__" and len(a.notes) == 2


def test_garbage_twice_means_invalid():
    a = NemotronPolicy(ScriptedLLM(["hello", "still no json"])).next_action(make_view())
    assert a.tool == "__invalid__"


def test_api_error_means_invalid_without_retry():
    a = NemotronPolicy(BrokenLLM()).next_action(make_view())
    assert a.tool == "__invalid__" and "timed out" in a.notes[0]


def test_unaffordable_tool_rejected():
    llm = ScriptedLLM(['{"action": "run_tool", "tool": "run_gpu_stress_test"}'] * 2)
    assert NemotronPolicy(llm).next_action(make_view(cost_left=3)).tool == "__invalid__"


def test_good_diagnosis_accepted():
    llm = ScriptedLLM(['{"action": "submit_diagnosis", "cause": "thermal_throttling", "confidence": 0.95, '
                       '"cited_result_ids": ["r1"], "explanation": "GPU2 is hot and throttling."}'])
    a = NemotronPolicy(llm).next_action(make_view([R1]))
    assert a.kind == "submit_diagnosis" and a.diagnosis["cause"] == "thermal_throttling"


def test_fake_citation_rejected():
    bad = ('{"action": "submit_diagnosis", "cause": "thermal_throttling", "confidence": 0.9, '
           '"cited_result_ids": ["r7"], "explanation": "x"}')
    assert NemotronPolicy(ScriptedLLM([bad, bad])).next_action(make_view([R1])).tool == "__invalid__"


def test_unknown_cause_rejected():
    bad = '{"action": "submit_diagnosis", "cause": "aliens", "confidence": 0.9, "cited_result_ids": ["r1"]}'
    assert NemotronPolicy(ScriptedLLM([bad, bad])).next_action(make_view([R1])).tool == "__invalid__"


def test_confidence_out_of_range_rejected():
    bad = '{"action": "submit_diagnosis", "cause": "no_fault", "confidence": 7, "cited_result_ids": ["r1"]}'
    assert NemotronPolicy(ScriptedLLM([bad, bad])).next_action(make_view([R1])).tool == "__invalid__"


def test_extract_json_handles_think_and_fences():
    text = '<think>{"not": "this"}</think>Sure!\n```json\n{"action": "run_tool", "tool": "check_power"}\n```'
    assert extract_json(text)["tool"] == "check_power"


def test_state_sent_to_model_has_no_truth():
    view = make_view([R1])
    view["truth"] = {"fault": "thermal_throttling", "severity": "mild"}  # even if the loop leaked it...
    sent = json.dumps(build_state(view))
    assert "truth" not in sent and "mild" not in sent and "observation" not in sent  # ...it is never sent


def test_mock_runs_cheapest_then_submits():
    policy = NemotronPolicy(MockLLMClient())
    first = policy.next_action(make_view())
    assert first.kind == "run_tool" and first.tool == "get_job_summary" and first.source == "mock_llm"
    done = policy.next_action(make_view([R1], beliefs={"thermal_throttling": 0.95, "memory_pressure": 0.02,
                                                       "network_congestion": 0.02, "no_fault": 0.01}))
    assert done.kind == "submit_diagnosis" and done.diagnosis["cause"] == "thermal_throttling"
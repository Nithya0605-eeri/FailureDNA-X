"""
The contract between the two halves of FailureDNA X. Agree on this file with your teammate.

1) Action: what the AI (investigator.py) returns each turn.
2) The VIEW: the dict the investigation loop gives the AI each turn. It never contains the truth.

VIEW keys (built by your teammate's Investigation.view()):
    symptom        str               "Training job step time is 1.84x its normal baseline ..."
    hypotheses     list[str]          the 4 possible causes (simulator.FAULTS)
    tools          list[dict]         [{"name", "description", "cost"}, ...]
    already_run    list[str]          tool names already used
    evidence       list[dict]         [{"result_id": "r1", "tool", "summary", "measurements", "observation"}, ...]
    beliefs        dict[str, float]   probability of each cause, sums to 1
    steps_left     int
    cost_left      int
    stop_threshold float
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Action:
    kind: str                          # "run_tool" or "submit_diagnosis"
    tool: Optional[str] = None         # for run_tool; "__invalid__" means "the AI failed, please fall back"
    hypothesis: str = ""               # the AI's current suspects and why
    reason: str = ""                   # what this test should confirm or rule out
    source: str = "policy"             # "nemotron", "mock_llm", "fixed", "infogain", "fallback"
    diagnosis: Optional[dict] = None   # for submit_diagnosis: cause, confidence, cited_result_ids, explanation
    tokens: int = 0
    latency_ms: int = 0
    notes: list[str] = field(default_factory=list)  # validation problems, retries, API errors
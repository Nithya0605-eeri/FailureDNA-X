"""
Diagnostic tool registry.

The agent may ONLY call tools listed in TOOLS. Each tool has a fixed simulated
cost (GPU time lost while testing). `execute_tool` reads the hidden scenario
state, adds small measurement noise, and returns structured measurements.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .simulator import NUM_GPUS, Scenario, _rng


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    cost: int


TOOLS: dict[str, ToolSpec] = {
    t.name: t
    for t in [
        ToolSpec("get_job_summary",
                 "Job-level view: step time vs. baseline, step-time variability, average GPU utilization.", 1),
        ToolSpec("check_thermals",
                 "Per-GPU temperature (C), SM clock (MHz) and whether a thermal-throttle flag is active.", 1),
        ToolSpec("check_power",
                 "Per-GPU power draw vs. power cap (W).", 1),
        ToolSpec("check_memory",
                 "Per-GPU memory used (%) and allocator retry counts.", 2),
        ToolSpec("run_nccl_bandwidth_test",
                 "Runs an all-reduce benchmark across GPUs: bus bandwidth (GB/s) and all-reduce latency (ms). Pauses the job.", 5),
        ToolSpec("run_gpu_stress_test",
                 "Runs a sustained compute load and reports how far the SM clock drops under heat. Pauses the job.", 8),
    ]
}

# Order used by the fixed-checklist baseline (what an engineer might do by habit)
FIXED_ORDER = [
    "get_job_summary",
    "check_thermals",
    "check_memory",
    "check_power",
    "run_nccl_bandwidth_test",
    "run_gpu_stress_test",
]


def tool_catalog() -> list[dict]:
    """Tool list in the shape we show to the LLM and the frontend."""
    return [{"name": t.name, "description": t.description, "cost": t.cost} for t in TOOLS.values()]


def execute_tool(name: str, scenario: Scenario) -> tuple[dict, str]:
    """Run a tool against the scenario. Returns (measurements, one-line summary)."""
    if name not in TOOLS:
        raise ValueError(f"unknown tool {name!r}")
    s = scenario.state
    rng = _rng(scenario.seed, "tool:" + name)

    def jitter(values, sd):
        arr = np.asarray(values, dtype=float)
        return (arr + rng.normal(0, sd, arr.shape)).round(1).tolist()

    if name == "get_job_summary":
        m = {
            "step_time_ratio": round(s["step_time_ratio"] + float(rng.normal(0, 0.03)), 2),
            "step_time_cv": round(max(0.0, s["step_time_cv"] + float(rng.normal(0, 0.01))), 3),
            "gpu_util_pct": round(s["gpu_util_pct"] + float(rng.normal(0, 1.5)), 1),
        }
        summary = (f"Step time {m['step_time_ratio']}x baseline, variability (CV) {m['step_time_cv']}, "
                   f"avg utilization {m['gpu_util_pct']}%.")
    elif name == "check_thermals":
        temps = jitter(s["temps_c"], 0.6)
        clocks = [round(c) for c in jitter(s["sm_clock_mhz"], 8)]
        m = {"temps_c": temps, "sm_clock_mhz": clocks, "throttle_thermal": list(s["throttle_thermal"])}
        hot = int(np.argmax(temps))
        summary = (f"Hottest GPU{hot} at {temps[hot]}C, clock {clocks[hot]} MHz; "
                   f"thermal throttle active on GPUs {[i for i, t in enumerate(m['throttle_thermal']) if t] or 'none'}.")
    elif name == "check_power":
        power = jitter(s["power_w"], 6)
        m = {"power_w": power, "power_cap_w": s["power_cap_w"]}
        summary = f"Power draw {min(power):.0f}-{max(power):.0f} W against a {s['power_cap_w']:.0f} W cap."
    elif name == "check_memory":
        mem = [min(100.0, v) for v in jitter(s["mem_used_pct"], 0.3)]
        m = {"mem_used_pct": mem, "alloc_retries": list(s["alloc_retries"])}
        top = int(np.argmax(mem))
        summary = (f"Highest memory use GPU{top} at {mem[top]}%; "
                   f"max allocator retries {max(m['alloc_retries'])}.")
    elif name == "run_nccl_bandwidth_test":
        m = {
            "busbw_gbps": round(s["busbw_gbps"] + float(rng.normal(0, 2)), 1),
            "allreduce_ms": round(max(1.0, s["allreduce_ms"] + float(rng.normal(0, 0.5))), 1),
        }
        summary = f"All-reduce bus bandwidth {m['busbw_gbps']} GB/s, latency {m['allreduce_ms']} ms."
    else:  # run_gpu_stress_test
        drop = max(0.0, s["stress_clock_drop"] + float(rng.normal(0, 0.01)))
        worst = int(np.argmax(s["temps_c"]))
        m = {"sustained_clock_drop_pct": round(drop * 100, 1), "worst_gpu": worst,
             "peak_temp_c": round(s["temps_c"][worst] + 4 + drop * 20, 1)}
        summary = (f"Under sustained load GPU{worst} lost {m['sustained_clock_drop_pct']}% clock, "
                   f"peaking at {m['peak_temp_c']}C.")
    assert len(s["temps_c"]) == NUM_GPUS
    return m, summary
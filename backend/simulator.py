"""
GPU fault simulator.

Creates a reproducible "scenario" from a seed: one node with several GPUs running a
training job, plus exactly one hidden ground-truth cause (or no fault).

The investigator NEVER sees `Scenario.truth`. It only sees `PublicScenario`
(the symptom) and whatever the diagnostic tools return.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

FAULTS = ["thermal_throttling", "memory_pressure", "network_congestion", "no_fault"]
SEVERITIES = ["mild", "severe"]
NUM_GPUS = 4

# Healthy reference values (what a normal node looks like)
NORMAL_SM_CLOCK_MHZ = 1980
NORMAL_BUSBW_GBPS = 165.0
NORMAL_ALLREDUCE_MS = 10.0
POWER_CAP_W = 700.0


@dataclass
class Truth:
    fault: str
    severity: str
    gpu_id: Optional[int]  # affected GPU (None for network / no_fault)


@dataclass
class Scenario:
    seed: int
    truth: Truth
    # Ground-state parameters the tools read from (before measurement noise)
    state: dict = field(default_factory=dict)

    def public(self) -> "PublicScenario":
        return PublicScenario(
            seed=self.seed,
            symptom=(
                f"Training job step time is {self.state['step_time_ratio']:.2f}x its normal baseline "
                f"on a {NUM_GPUS}-GPU node. Find the root cause."
            ),
        )


@dataclass
class PublicScenario:
    """The only view of a scenario the investigator is allowed to see."""
    seed: int
    symptom: str


def _rng(seed: int, salt: str = "") -> np.random.Generator:
    """Deterministic RNG per (seed, salt) so every tool result is reproducible."""
    # Python's built-in hash() changes between runs, so use a simple stable hash
    mix = sum((i + 1) * ord(c) for i, c in enumerate(salt)) % (2**31)
    return np.random.default_rng([seed, mix])


def generate_scenario(seed: int, fault: Optional[str] = None, severity: Optional[str] = None) -> Scenario:
    """Build a scenario. If fault/severity are None they are drawn from the seed."""
    rng = _rng(seed, "scenario")
    # Always draw both values so the random stream (and every later value) stays the same
    # whether or not a fault/severity is forced (used for demos and baseline comparisons).
    drawn_fault = FAULTS[int(rng.integers(0, len(FAULTS)))]
    drawn_severity = SEVERITIES[int(rng.integers(0, 2))]
    fault = fault or drawn_fault
    severity = severity or drawn_severity
    if fault not in FAULTS:
        raise ValueError(f"unknown fault {fault!r}")
    severe = severity == "severe"

    gpu_id = int(rng.integers(0, NUM_GPUS)) if fault in ("thermal_throttling", "memory_pressure") else None

    # ---- healthy baseline per GPU ----
    temps = rng.uniform(58, 72, NUM_GPUS)
    clocks = np.full(NUM_GPUS, float(NORMAL_SM_CLOCK_MHZ)) - rng.uniform(0, 40, NUM_GPUS)
    mem_pct = rng.uniform(62, 86, NUM_GPUS)
    alloc_retries = rng.integers(0, 4, NUM_GPUS).astype(float)
    power = rng.uniform(520, 650, NUM_GPUS)
    throttle = [False] * NUM_GPUS
    busbw = NORMAL_BUSBW_GBPS + rng.uniform(-15, 20)
    allreduce = NORMAL_ALLREDUCE_MS + rng.uniform(-2, 2)
    # step-time coefficient of variation; ~15% of healthy jobs are jittery anyway (data loader)
    step_cv = rng.uniform(0.08, 0.14) if rng.random() < 0.15 else rng.uniform(0.02, 0.07)
    stress_clock_drop = rng.uniform(0.0, 0.05)  # fraction lost under sustained load

    # ---- red herrings: confusing but harmless signals ----
    if fault != "thermal_throttling" and rng.random() < 0.3:
        temps[int(rng.integers(0, NUM_GPUS))] = rng.uniform(77, 86)  # warm but not throttling
    if fault != "memory_pressure" and rng.random() < 0.3:
        mem_pct[int(rng.integers(0, NUM_GPUS))] = rng.uniform(89, 96)  # busy but fine
        if rng.random() < 0.4:
            alloc_retries[int(rng.integers(0, NUM_GPUS))] = rng.integers(5, 12)
    if fault != "network_congestion" and rng.random() < 0.25:
        busbw -= rng.uniform(25, 55)  # a bit low, still acceptable
        allreduce += rng.uniform(1, 5)

    # ---- apply the hidden fault ----
    if fault == "thermal_throttling":
        g = gpu_id
        temps[g] = rng.uniform(86, 94) if severe else rng.uniform(80, 87)
        clocks[g] *= 1 - (rng.uniform(0.22, 0.38) if severe else rng.uniform(0.06, 0.16))
        throttle[g] = bool(rng.random() < 0.9) if severe else bool(rng.random() < 0.45)
        power[g] = rng.uniform(380, 480) if severe else rng.uniform(450, 560)
        stress_clock_drop = rng.uniform(0.22, 0.4) if severe else rng.uniform(0.07, 0.2)
        step_ratio = rng.uniform(1.6, 2.2) if severe else rng.uniform(1.3, 1.6)
    elif fault == "memory_pressure":
        g = gpu_id
        mem_pct[g] = rng.uniform(96.5, 99.6) if severe else rng.uniform(92.5, 97)
        alloc_retries[g] = rng.integers(40, 200) if severe else rng.integers(4, 25)
        step_cv = rng.uniform(0.15, 0.35) if severe else rng.uniform(0.05, 0.14)
        step_ratio = rng.uniform(1.5, 2.1) if severe else rng.uniform(1.25, 1.55)
    elif fault == "network_congestion":
        busbw = rng.uniform(40, 90) if severe else rng.uniform(95, 130)
        allreduce = rng.uniform(28, 60) if severe else rng.uniform(13, 22)
        power = power - (rng.uniform(80, 160) if severe else rng.uniform(20, 90))  # GPUs idle waiting
        step_ratio = rng.uniform(1.6, 2.3) if severe else rng.uniform(1.3, 1.6)
    else:  # no_fault: a noisy-neighbour style slowdown that looks worrying but isn't a fault
        step_ratio = rng.uniform(1.15, 1.5)
        if rng.random() < 0.3:
            power = power - rng.uniform(30, 120)  # light phase of the job

    util = float(np.clip(96 / step_ratio + rng.uniform(-4, 4), 30, 99))

    state = {
        "temps_c": temps.round(1).tolist(),
        "sm_clock_mhz": clocks.round(0).tolist(),
        "throttle_thermal": throttle,
        "mem_used_pct": mem_pct.round(1).tolist(),
        "alloc_retries": alloc_retries.astype(int).tolist(),
        "power_w": power.round(0).tolist(),
        "power_cap_w": POWER_CAP_W,
        "busbw_gbps": round(float(busbw), 1),
        "allreduce_ms": round(float(allreduce), 1),
        "step_time_ratio": round(float(step_ratio), 2),
        "step_time_cv": round(float(step_cv), 3),
        "gpu_util_pct": round(util, 1),
        "stress_clock_drop": round(float(stress_clock_drop), 3),
    }
    return Scenario(seed=seed, truth=Truth(fault=fault, severity=severity, gpu_id=gpu_id), state=state)


if __name__ == "__main__":
    # Quick manual check: python -m backend.simulator
    for s in [1, 2, 3, 4]:
        sc = generate_scenario(s)
        print(s, sc.truth, sc.public().symptom)
        print("   ", sc.state)
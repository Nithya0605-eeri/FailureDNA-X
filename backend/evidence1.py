"""
Evidence engine: deterministic belief tracking (no LLM here).

1. Each tool result is reduced to a small discrete *observation* (e.g. "hot|throttle").
2. P(observation | hypothesis) tables are estimated once from CALIBRATION seeds
   (10000-11999), which never overlap the dev/test seeds used for evaluation.
3. Beliefs are updated with Bayes' rule after every result.
4. Expected information gain per unit cost tells us which test is most useful next.
"""
from __future__ import annotations

import math
from collections import defaultdict
from functools import lru_cache

from .diagnostics1 import TOOLS, execute_tool
from .simulator import FAULTS, generate_scenario

CALIBRATION_SEEDS = range(10_000, 12_000)
SMOOTHING = 1.0  # Laplace smoothing so no observation ever has probability 0


def _bucket(x: float, cuts: list[float], labels: list[str]) -> str:
    for cut, label in zip(cuts, labels):
        if x < cut:
            return label
    return labels[-1]


def observe(tool: str, m: dict) -> str:
    """Turn raw measurements into a discrete observation key."""
    if tool == "get_job_summary":
        return (_bucket(m["step_time_ratio"], [1.3, 1.6], ["small", "moderate", "large"]) + "|" +
                ("erratic" if m["step_time_cv"] >= 0.08 else "steady"))
    if tool == "check_thermals":
        return (_bucket(max(m["temps_c"]), [78, 85], ["normal", "warm", "hot"]) + "|" +
                ("throttle" if any(m["throttle_thermal"]) else "no_throttle"))
    if tool == "check_power":
        return _bucket(min(m["power_w"]) / m["power_cap_w"], [0.6, 0.75], ["low", "reduced", "normal"])
    if tool == "check_memory":
        return (_bucket(max(m["mem_used_pct"]), [90, 95], ["ok", "high", "critical"]) + "|" +
                ("retries" if max(m["alloc_retries"]) >= 8 else "no_retries"))
    if tool == "run_nccl_bandwidth_test":
        return (_bucket(m["busbw_gbps"], [100, 135], ["low", "degraded", "normal"]) + "|" +
                ("slow_allreduce" if m["allreduce_ms"] > 14 else "fast_allreduce"))
    if tool == "run_gpu_stress_test":
        return _bucket(m["sustained_clock_drop_pct"], [8, 20], ["stable", "dropping", "collapsing"])
    raise ValueError(tool)


@lru_cache(maxsize=1)
def likelihoods() -> dict[str, dict[str, dict[str, float]]]:
    """table[tool][observation][hypothesis] = P(observation | hypothesis)."""
    counts: dict = {t: defaultdict(lambda: defaultdict(float)) for t in TOOLS}
    totals: dict = {t: defaultdict(float) for t in TOOLS}
    for seed in CALIBRATION_SEEDS:
        sc = generate_scenario(seed)
        h = sc.truth.fault
        for tool in TOOLS:
            m, _ = execute_tool(tool, sc)
            counts[tool][observe(tool, m)][h] += 1
            totals[tool][h] += 1
    table: dict = {}
    for tool in TOOLS:
        obs_keys = list(counts[tool].keys())
        k = len(obs_keys)
        table[tool] = {
            o: {h: (counts[tool][o][h] + SMOOTHING) / (totals[tool][h] + SMOOTHING * k) for h in FAULTS}
            for o in obs_keys
        }
    return table


def uniform_prior() -> dict[str, float]:
    return {h: 1.0 / len(FAULTS) for h in FAULTS}


def entropy(beliefs: dict[str, float]) -> float:
    return -sum(p * math.log2(p) for p in beliefs.values() if p > 0)


def update(beliefs: dict[str, float], tool: str, obs: str) -> dict[str, float]:
    table = likelihoods()[tool]
    # An observation never seen in calibration gets a small equal likelihood (no information)
    lik = table.get(obs, {h: 1.0 for h in FAULTS})
    post = {h: beliefs[h] * lik[h] for h in FAULTS}
    z = sum(post.values()) or 1.0
    return {h: round(p / z, 6) for h, p in post.items()}


def expected_info_gain(beliefs: dict[str, float], tool: str) -> float:
    """Expected reduction in entropy (bits) if we ran `tool` now."""
    table = likelihoods()[tool]
    h_now = entropy(beliefs)
    expected_after = 0.0
    for obs, lik in table.items():
        p_obs = sum(beliefs[h] * lik[h] for h in FAULTS)
        if p_obs <= 0:
            continue
        post = {h: beliefs[h] * lik[h] / p_obs for h in FAULTS}
        expected_after += p_obs * entropy(post)
    return max(0.0, h_now - expected_after)


def rank_tools(beliefs: dict[str, float], already_run: set[str], cost_left: float) -> list[dict]:
    """Untried, affordable tools ranked by information gain per unit cost."""
    out = []
    for name, spec in TOOLS.items():
        if name in already_run or spec.cost > cost_left:
            continue
        ig = expected_info_gain(beliefs, name)
        out.append({"tool": name, "info_gain_bits": round(ig, 3), "cost": spec.cost,
                    "gain_per_cost": round(ig / spec.cost, 4)})
    return sorted(out, key=lambda r: r["gain_per_cost"], reverse=True)


def top(beliefs: dict[str, float]) -> tuple[str, float]:
    h = max(beliefs, key=beliefs.get)
    return h, beliefs[h]
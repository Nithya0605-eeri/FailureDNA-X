"""
Logic behind the simulated-investigation API (kept separate from FastAPI so it is easy to test).
Investigations are kept in memory; restarting the server clears them.
"""
import random
from typing import Optional

from .config import settings
from .investigation1 import FixedPolicy, InfoGainPolicy, Investigation
from .investigator1 import NemotronPolicy
from .simulator import FAULTS, SEVERITIES

MODES = ["nemotron", "infogain", "fixed"]
_store: dict[str, Investigation] = {}
_policies: dict = {}


def _policy(mode: str):
    if mode not in _policies:
        _policies[mode] = {"nemotron": NemotronPolicy, "infogain": InfoGainPolicy, "fixed": FixedPolicy}[mode]()
    return _policies[mode]


def create(mode: str = "nemotron", seed: Optional[int] = None,
           fault: Optional[str] = None, severity: Optional[str] = None) -> dict:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if fault is not None and fault not in FAULTS:
        raise ValueError(f"fault must be one of {FAULTS}")
    if severity is not None and severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}")
    if seed is None:
        seed = random.randint(100_000, 999_999)  # never overlaps the dev/test seed files
    inv = Investigation(seed, mode, fault, severity)
    _store[inv.id] = inv
    return inv.public()


def get(inv_id: str) -> Investigation:
    if inv_id not in _store:
        raise KeyError(inv_id)
    return _store[inv_id]


def step(inv_id: str) -> dict:
    inv = get(inv_id)
    inv.step(_policy(inv.mode))
    inv.attach_baseline()
    return inv.public()


def run(inv_id: str) -> dict:
    inv = get(inv_id)
    inv.run(_policy(inv.mode))
    inv.attach_baseline()
    return inv.public()


def state(inv_id: str) -> dict:
    return get(inv_id).public()


def info() -> dict:
    return {"llm_mode": settings.llm_mode, "model": settings.nemotron_model if settings.llm_mode == "nemotron" else None,
            "modes": MODES, "faults": FAULTS, "stop_threshold": settings.stop_threshold,
            "max_steps": settings.max_steps, "max_cost": settings.max_cost}
"""
Create balanced seed lists (equal number of each hidden fault).

  python -m backend.make_seeds

seeds/dev.txt  : seeds 1-999,     15 per fault (60) -> use freely while tuning prompts/thresholds
seeds/test.txt : seeds 2000-2999, 12 per fault (48) -> FREEZE before the final run; never tune on it
Calibration of the evidence engine uses seeds 10000-11999, so nothing overlaps.
"""
from pathlib import Path

from .simulator import FAULTS, generate_scenario

ROOT = Path(__file__).resolve().parent.parent


def pick(start: int, stop: int, per_fault: int) -> list[tuple[int, str, str]]:
    chosen, counts = [], {f: 0 for f in FAULTS}
    for seed in range(start, stop):
        t = generate_scenario(seed).truth
        if counts[t.fault] < per_fault:
            counts[t.fault] += 1
            chosen.append((seed, t.fault, t.severity))
        if all(c == per_fault for c in counts.values()):
            break
    return chosen


def write(name: str, rows: list[tuple[int, str, str]]) -> None:
    path = ROOT / "seeds" / name
    path.parent.mkdir(exist_ok=True)
    # The truth is written as a comment so YOU can check balance; the agent never reads this file.
    path.write_text("".join(f"{s}  # {f} {sev}\n" for s, f, sev in rows))
    print(f"wrote {path} ({len(rows)} seeds)")


if __name__ == "__main__":
    write("dev.txt", pick(1, 1000, 15))
    write("test.txt", pick(2000, 3000, 12))
"""
Check that Nemotron on Nebius Token Factory works with your key.   Run:  python -m backend.smoke_nemotron

1) lists the NVIDIA / Nemotron models your key can use
2) sends one chat message
3) asks the investigator for ONE decision on a sample scenario
"""
import time

from .config import settings
from .investigator1 import NemotronPolicy
from .nemotron1 import TokenFactoryClient
from .simulator import FAULTS, generate_scenario

if not settings.nebius_api_key:
    raise SystemExit("NEBIUS_API_KEY is empty. Put your key in the .env file in the repo root.")

client = TokenFactoryClient()

print("1) Models your key can use (nvidia / nemotron):")
ids = sorted(m.id for m in client.client.models.list().data)
for mid in ids:
    if "nemotron" in mid.lower() or mid.lower().startswith("nvidia/"):
        print("    ", mid)
if settings.nemotron_model not in ids:
    print(f"\n!! NEMOTRON_MODEL={settings.nemotron_model!r} is not available. Copy one ID from above into .env")
    raise SystemExit(1)

print(f"\n2) Chat test with {settings.nemotron_model}")
t0 = time.time()
text, tokens = client.complete([{"role": "user", "content": "In one sentence: what is GPU thermal throttling?"}])
print("    ", text.strip()[:300])
print(f"     tokens={tokens}  seconds={time.time() - t0:.1f}")

print("\n3) One investigation decision on sample seed 1")
SAMPLE_TOOLS = [  # same names and costs as your teammate's diagnostics.py
    {"name": "get_job_summary", "description": "Step time vs baseline, variability, utilization.", "cost": 1},
    {"name": "check_thermals", "description": "Per-GPU temperature, SM clock, throttle flag.", "cost": 1},
    {"name": "check_power", "description": "Per-GPU power draw vs cap.", "cost": 1},
    {"name": "check_memory", "description": "Per-GPU memory used and allocator retries.", "cost": 2},
    {"name": "run_nccl_bandwidth_test", "description": "All-reduce bandwidth and latency. Pauses the job.", "cost": 5},
    {"name": "run_gpu_stress_test", "description": "Clock drop under sustained load. Pauses the job.", "cost": 8},
]
view = {
    "symptom": generate_scenario(1).public().symptom,
    "hypotheses": FAULTS, "tools": SAMPLE_TOOLS, "already_run": [], "evidence": [],
    "beliefs": {f: 0.25 for f in FAULTS}, "steps_left": 6, "cost_left": 18, "stop_threshold": settings.stop_threshold,
}
action = NemotronPolicy(client).next_action(view)
print(f"     kind={action.kind} tool={action.tool} source={action.source}")
print(f"     hypothesis: {action.hypothesis}")
print(f"     reason:     {action.reason}")
print(f"     tokens={action.tokens} latency={action.latency_ms} ms notes={action.notes}")
print("\nReady!" if action.tool != "__invalid__" else "\nThe model's replies were invalid; see notes above.")
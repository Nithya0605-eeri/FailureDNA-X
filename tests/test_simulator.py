from backend.simulator import FAULTS, generate_scenario


def test_same_seed_same_scenario():
    a, b = generate_scenario(42), generate_scenario(42)
    assert a.truth == b.truth and a.state == b.state


def test_forcing_the_drawn_fault_gives_identical_scenario():
    a = generate_scenario(7)
    b = generate_scenario(7, a.truth.fault, a.truth.severity)
    assert a.state == b.state


def test_public_view_hides_truth():
    sc = generate_scenario(3)
    pub = sc.public()
    assert not hasattr(pub, "truth")
    for f in FAULTS:
        assert f not in pub.symptom


def test_fault_signatures():
    th = generate_scenario(1, "thermal_throttling", "severe")
    assert max(th.state["temps_c"]) >= 86
    mem = generate_scenario(1, "memory_pressure", "severe")
    assert max(mem.state["mem_used_pct"]) >= 96
    net = generate_scenario(1, "network_congestion", "severe")
    assert net.state["busbw_gbps"] < 100
    ok = generate_scenario(1, "no_fault")
    assert ok.state["step_time_ratio"] < 1.55
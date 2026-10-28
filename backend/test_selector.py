import json

try:
    from .diagnostic_tests import (
        AVAILABLE_TESTS,
        run_diagnostic_test,
    )
except ImportError:
    from diagnostic_tests import (
        AVAILABLE_TESTS,
        run_diagnostic_test,
    )


def select_next_test(symptoms, completed_tests=None):
    """Select the next diagnostic test using symptom priorities."""

    completed_tests = completed_tests or []

    priorities = {
        "thermal_test": 0,
        "memory_test": 0,
        "network_test": 0,
    }

    if symptoms.get("high_temperature", False):
        priorities["thermal_test"] += 3

    if symptoms.get("high_memory_usage", False):
        priorities["memory_test"] += 3

    if symptoms.get("slow_network", False):
        priorities["network_test"] += 3

    if symptoms.get("low_gpu_utilization", False):
        priorities["memory_test"] += 1
        priorities["network_test"] += 1

    available = [
        test for test in AVAILABLE_TESTS
        if test not in completed_tests
    ]

    if not available:
        return None

    return max(
        available,
        key=lambda test: priorities[test]
    )


def investigate_gpu(gpu, symptoms, max_tests=3):
    """Investigate a simulated GPU using selected tests."""

    completed_tests = []
    history = []
    total_cost = 0

    for _ in range(min(max_tests, len(AVAILABLE_TESTS))):
        next_test = select_next_test(
            symptoms,
            completed_tests
        )

        if next_test is None:
            break

        result = run_diagnostic_test(gpu, next_test)

        history.append(result)
        completed_tests.append(next_test)
        total_cost += result["test_cost"]

        if result["result"] == "abnormal":
            break

    abnormal_tests = [
        result["test"]
        for result in history
        if result["result"] == "abnormal"
    ]

    return {
        "gpu_id": gpu["gpu_id"],
        "tests_completed": completed_tests,
        "total_test_cost": total_cost,
        "suspected_causes": abnormal_tests,
        "investigation_history": history,
        "status": (
            "suspected_fault"
            if abnormal_tests
            else "inconclusive"
        ),
    }


if __name__ == "__main__":
    sample_gpu = {
        "gpu_id": "GPU-001",
        "temperature_c": 92,
        "memory_usage_percent": 55,
        "gpu_utilization_percent": 60,
        "network_latency_ms": 3.2,
    }

    symptoms = {
        "high_temperature": True,
        "high_memory_usage": False,
        "slow_network": False,
        "low_gpu_utilization": False,
    }

    result = investigate_gpu(sample_gpu, symptoms)

    print("FailureDNA X - Adaptive Diagnostic Selector")
    print("=" * 45)
    print(json.dumps(result, indent=4))
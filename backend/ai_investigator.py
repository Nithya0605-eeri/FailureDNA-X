import json

from .nemotron import select_test_with_ai
from .diagnostic_tests import run_diagnostic_test, AVAILABLE_TESTS


def run_ai_investigation(gpu, symptoms, max_tests=3):
    """
    Run a GPU investigation using NVIDIA Nemotron
    to select diagnostic tests.
    """

    completed_tests = []
    investigation_history = []
    total_cost = 0
    suspected_causes = []

    test_to_cause = {
        "thermal_test": "overheating",
        "memory_test": "memory_pressure",
        "network_test": "network_congestion",
    }

    for step in range(min(max_tests, len(AVAILABLE_TESTS))):

        # Ask NVIDIA Nemotron to choose the next test
        ai_decision = select_test_with_ai(
            symptoms,
            completed_tests
        )

        selected_test = ai_decision["selected_test"]

        # Never execute an unknown or repeated test
        if selected_test not in AVAILABLE_TESTS:
            raise ValueError("AI selected an unknown test.")

        if selected_test in completed_tests:
            raise ValueError("AI repeated a completed test.")

        # Execute the selected diagnostic test
        test_result = run_diagnostic_test(
            gpu,
            selected_test
        )

        completed_tests.append(selected_test)
        total_cost += test_result["test_cost"]

        investigation_history.append({
            "step": step + 1,
            "ai_selected_test": selected_test,
            "ai_reason": ai_decision["reason"],
            "test_result": test_result,
        })

        # Stop when the first abnormal test is found
        if test_result["result"] == "abnormal":
            suspected_causes.append(
                test_to_cause[selected_test]
            )
            break

    return {
        "gpu_id": gpu["gpu_id"],
        "status": (
            "suspected_fault"
            if suspected_causes
            else "inconclusive"
        ),
        "suspected_causes": suspected_causes,
        "tests_completed": completed_tests,
        "total_test_cost": total_cost,
        "investigation_history": investigation_history,
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

    print("FailureDNA X - Autonomous AI Investigation")

    result = run_ai_investigation(
        sample_gpu,
        symptoms
    )

    print(json.dumps(result, indent=4))
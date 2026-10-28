import json

AVAILABLE_TESTS = [
    "thermal_test",
    "memory_test",
    "network_test",
]


def run_diagnostic_test(gpu, test_name):
    """Run one simulated GPU diagnostic test."""

    if test_name not in AVAILABLE_TESTS:
        raise ValueError(f"Unknown diagnostic test: {test_name}")

    gpu_id = gpu.get("gpu_id", "GPU-UNKNOWN")

    if test_name == "thermal_test":
        temperature = gpu["temperature_c"]
        return {
            "gpu_id": gpu_id,
            "test": test_name,
            "measurement": {
                "temperature_c": temperature,
                "thermal_throttling": temperature >= 85,
            },
            "result": "abnormal" if temperature >= 85 else "normal",
            "test_cost": 1,
        }

    if test_name == "memory_test":
        memory = gpu["memory_usage_percent"]
        return {
            "gpu_id": gpu_id,
            "test": test_name,
            "measurement": {
                "memory_usage_percent": memory,
                "memory_pressure_detected": memory >= 90,
            },
            "result": "abnormal" if memory >= 90 else "normal",
            "test_cost": 2,
        }

    if test_name == "network_test":
        latency = gpu["network_latency_ms"]
        return {
            "gpu_id": gpu_id,
            "test": test_name,
            "measurement": {
                "network_latency_ms": latency,
                "network_congestion_detected": latency >= 20,
            },
            "result": "abnormal" if latency >= 20 else "normal",
            "test_cost": 3,
        }


if __name__ == "__main__":
    sample_gpu = {
        "gpu_id": "GPU-001",
        "temperature_c": 92,
        "memory_usage_percent": 55,
        "gpu_utilization_percent": 60,
        "network_latency_ms": 3.2,
    }

    print("FailureDNA X - Diagnostic Tests")
    print("=" * 40)

    for test in AVAILABLE_TESTS:
        result = run_diagnostic_test(sample_gpu, test)
        print(json.dumps(result, indent=4))
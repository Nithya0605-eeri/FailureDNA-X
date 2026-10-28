import json

FAULT_TYPES = [
    "overheating",
    "memory_pressure",
    "network_congestion"
]


def diagnose_gpu(gpu):
    """Detect potential GPU problems from simulated metrics."""
    issues = []

    if gpu["temperature_c"] >= 85:
        issues.append({
            "type": "overheating",
            "severity": "critical",
            "message": "GPU temperature is too high.",
            "recommendation": "Check cooling and thermal throttling."
        })

    if gpu["memory_usage_percent"] >= 90:
        issues.append({
            "type": "memory_pressure",
            "severity": "high",
            "message": "GPU memory usage is too high.",
            "recommendation": "Reduce batch size or optimize memory usage."
        })

    if gpu["network_latency_ms"] >= 20:
        issues.append({
            "type": "network_congestion",
            "severity": "high",
            "message": "GPU network latency is unusually high.",
            "recommendation": "Investigate network congestion."
        })

    return {
        "gpu_id": gpu["gpu_id"],
        "status": "warning" if issues else "healthy",
        "issues": issues
    }


def diagnose_cluster(cluster):
    return [diagnose_gpu(gpu) for gpu in cluster]


if __name__ == "__main__":
    sample_gpu = {
        "gpu_id": "GPU-001",
        "temperature_c": 92,
        "memory_usage_percent": 55,
        "gpu_utilization_percent": 60,
        "network_latency_ms": 3.2
    }

    result = diagnose_gpu(sample_gpu)
    print(json.dumps(result, indent=4))
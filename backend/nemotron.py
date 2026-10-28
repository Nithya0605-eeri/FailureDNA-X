import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.getenv(
    "NEBIUS_MODEL",
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
)

API_KEY = os.getenv("NEBIUS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "NEBIUS_API_KEY is missing from backend/.env"
    )

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=API_KEY,
    timeout=45.0,
)


def select_test_with_ai(symptoms, completed_tests=None):
    completed_tests = completed_tests or []

    available_tests = [
        "thermal_test",
        "memory_test",
        "network_test"
    ]

    remaining_tests = [
        test for test in available_tests
        if test not in completed_tests
    ]

    if not remaining_tests:
        return {
            "selected_test": None,
            "reason": "All diagnostic tests completed."
        }

    prompt = {
        "symptoms": symptoms,
        "completed_tests": completed_tests,
        "available_tests": remaining_tests,
    }

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a GPU diagnostic planning agent. "
                    "Choose exactly one diagnostic test from "
                    "the available tests. "
                    "Return only valid JSON with two keys: "
                    "selected_test and reason. "
                    "Never invent a test or claim a test was run."
                )
            },
            {
                "role": "user",
                "content": json.dumps(prompt)
            }
        ],
        temperature=0,
        max_tokens=500,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("AI returned an empty response.")

    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0].strip()

    decoder = json.JSONDecoder()
    start = content.find("{")

    if start == -1:
        raise ValueError("AI response contains no JSON object.")

    result, _ = decoder.raw_decode(content[start:])

    selected_test = result.get("selected_test")

    if selected_test not in remaining_tests:
        raise ValueError(
            f"AI selected an invalid test: {selected_test}"
        )

    return {
        "selected_test": selected_test,
        "reason": result.get("reason", "")
    }


if __name__ == "__main__":
    symptoms = {
        "high_temperature": True,
        "high_memory_usage": False,
        "slow_network": False,
        "low_gpu_utilization": False
    }

    print("FailureDNA X - NVIDIA Nemotron Test Selection")

    result = select_test_with_ai(symptoms)

    print(json.dumps(result, indent=4))
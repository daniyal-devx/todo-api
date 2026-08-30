import json
import requests

with open("evals/cases.json") as f:
    cases = json.load(f)

correct = 0
failed_cases = []

for case in cases:
    resp = requests.post(
        "http://localhost:8000/triage",
        json={"text": case["text"]},
    )
    if resp.status_code != 200:
        failed_cases.append((case["text"], f"HTTP {resp.status_code}"))
        continue

    result = resp.json()
    match = result["category"] == case["expected_category"]
    if match:
        correct += 1
    else:
        failed_cases.append((case["text"], f"expected {case['expected_category']}, got {result['category']}"))

print(f"\nScore: {correct}/{len(cases)} on category\n")
for text, reason in failed_cases:
    print(f"FAILED: \"{text}\" — {reason}")
"""Evaluation script: runs eval questions against the API and reports pass/fail."""

import csv
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.api import app


def run_eval(csv_path: str):
    """Run evaluation and return pass/fail stats."""
    client = TestClient(app)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    passed = 0
    failed = []

    for i, row in enumerate(rows, 1):
        question = row["question"]
        expected_type = row["expected_type"]
        must_contain = row["must_contain"] if row["must_contain"] else ""

        try:
            resp = client.post("/chat", json={"question": question})
            data = resp.json()
        except Exception as e:
            failed.append((i, question, f"Request error: {e}", ""))
            continue

        answer = data.get("answer", "")
        debug = data.get("debug", {})
        guardrail = debug.get("guardrail")
        threshold_passed = debug.get("threshold_passed", False)

        # Determine actual type
        if guardrail:
            actual_type = guardrail
        elif not threshold_passed:
            actual_type = "not_found"
        else:
            actual_type = "answer"

        # Check pass/fail
        type_match = (actual_type == expected_type)
        content_match = True
        if must_contain:
            content_match = must_contain.lower() in answer.lower()

        if type_match and content_match:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"
            failed.append((i, question, f"Expected type={expected_type}, got={actual_type}; must_contain='{must_contain}'", answer[:200]))

        print(f"{i:3d} [{status}] {question[:80]}...")
        if status == "FAIL":
            print(f"      Expected: type={expected_type}, contains='{must_contain}'")
            # Handle unicode for printing
            safe_answer = answer[:150].encode('ascii', 'replace').decode('ascii')
            print(f"      Got:      type={actual_type}, answer='{safe_answer}'")

    print(f"\n{'='*60}")
    print(f"Total: {total}, Passed: {passed}, Failed: {len(failed)}")
    print(f"Score: {passed}/{total} ({passed/total*100:.1f}%)")

    if failed:
        print(f"\nFailed questions:")
        for idx, q, reason, ans in failed:
            safe_q = q.encode('ascii', 'replace').decode('ascii')
            safe_ans = ans[:200].encode('ascii', 'replace').decode('ascii')
            print(f"  {idx}: {safe_q}")
            print(f"     Reason: {reason}")
            print(f"     Answer: {safe_ans}")

    return passed, total, failed


if __name__ == "__main__":
    csv_path = "tests/eval_questions.csv"
    run_eval(csv_path)
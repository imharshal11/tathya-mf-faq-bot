"""Evaluation script: runs eval questions against the API and reports pass/fail."""

import csv
import sys
import os
import time

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
    rate_limits = 0

    for i, row in enumerate(rows, 1):
        question = row["question"]
        expected_type = row["expected_type"]
        must_contain = row["must_contain"] if row["must_contain"] else ""
        must_not_contain = row["must_not_contain"] if row.get("must_not_contain") else ""
        scheme = row.get("scheme", "") if "scheme" in row else ""

        # Rate limit: wait 6 seconds between questions (Groq free tier: 30 req/min)
        if i > 1:
            time.sleep(6)

        # Retry up to 2 times on 429 (rate limit) after 30 seconds
        data = {}
        for attempt in range(3):
            try:
                payload = {"question": question}
                if scheme:
                    payload["scheme"] = scheme
                resp = client.post("/chat", json=payload)
                if resp.status_code == 429:
                    rate_limits += 1
                    print(f"      [RATE LIMIT 429] Q{i}, attempt {attempt+1}/3, waiting 30s...")
                    if attempt < 2:
                        time.sleep(30)
                        continue
                data = resp.json()
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(30)
                    continue
                failed.append((i, question, f"Request error: {e}", ""))
                data = {}
                break
        else:
            # If we exhausted retries
            if not data:
                failed.append((i, question, "Rate limited after retries", ""))
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
        not_contain_match = True
        if must_not_contain:
            not_contain_match = must_not_contain.lower() not in answer.lower()

        if type_match and content_match and not_contain_match:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"
            reason_parts = []
            if not type_match:
                reason_parts.append(f"Expected type={expected_type}, got={actual_type}")
            if must_contain and not content_match:
                reason_parts.append(f"must_contain='{must_contain}'")
            if must_not_contain and not not_contain_match:
                reason_parts.append(f"must_not_contain='{must_not_contain}'")
            failed.append((i, question, "; ".join(reason_parts), answer[:200]))

        scheme_str = f" [scheme={scheme}]" if scheme else ""
        print(f"{i:3d} [{status}]{scheme_str} {question[:80]}...")
        if status == "FAIL":
            print(f"      Expected: type={expected_type}, contains='{must_contain}', not_contains='{must_not_contain}'")
            print(f"      Intent: {debug.get('intent')}, Guardrail: {guardrail}")
            print(f"      Matches: {debug.get('matches')}")
            # Handle unicode for printing
            safe_answer = answer[:150].encode('ascii', 'replace').decode('ascii')
            print(f"      Got:      type={actual_type}, answer='{safe_answer}'")

    print(f"\n{'='*60}")
    print(f"Total: {total}, Passed: {passed}, Failed: {len(failed)}")
    print(f"Rate limits (429): {rate_limits}")
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
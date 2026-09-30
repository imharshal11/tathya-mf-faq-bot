"""Evaluation script: runs eval questions against the API and reports pass/fail."""

import csv
import sys
import os
import time
import argparse
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.api import app


FAILED_LOG = "tests/last_failed.txt"


def _get_type(row: dict) -> str:
    """Get the type category for a row."""
    return row["expected_type"]


def _select_quick_set(rows: list[dict]) -> list[dict]:
    """Select 2-3 rows per expected type across the whole file for quick smoke test."""
    by_type = {}
    for row in rows:
        t = _get_type(row)
        by_type.setdefault(t, []).append(row)

    selected = []
    for t, type_rows in by_type.items():
        # Take 2-3 per type from across the file (not just first rows)
        take = min(3, len(type_rows))
        # Pick from beginning, middle, and end for coverage
        if len(type_rows) <= take:
            selected.extend(type_rows)
        else:
            indices = [0, len(type_rows) // 2, len(type_rows) - 1]
            for i in indices[:take]:
                selected.append(type_rows[i])
    return selected


def _load_failed_indices() -> set[int]:
    """Load failed row indices from last_failed.txt (1-indexed)."""
    if not os.path.exists(FAILED_LOG):
        return set()
    with open(FAILED_LOG, "r", encoding="utf-8") as f:
        return {int(line.strip()) for line in f if line.strip().isdigit()}


def _save_failed_indices(failed: list[tuple]) -> None:
    """Save failed row indices to last_failed.txt."""
    with open(FAILED_LOG, "w", encoding="utf-8") as f:
        for idx, _, _, _ in failed:
            f.write(f"{idx}\n")


def run_eval(csv_path: str, only_text: str | None = None, use_failed: bool = False, quick: bool = False):
    """Run evaluation and return pass/fail stats."""
    client = TestClient(app)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    # Filter rows based on flags
    if use_failed:
        failed_indices = _load_failed_indices()
        rows = [(i, row) for i, row in enumerate(all_rows, 1) if i in failed_indices]
        if not rows:
            print("No failed rows from last run.")
            return 0, 0, []
    elif quick:
        quick_rows = _select_quick_set(all_rows)
        # Keep original indices
        rows = [(i, row) for i, row in enumerate(all_rows, 1) if row in quick_rows]
    elif only_text:
        rows = [(i, row) for i, row in enumerate(all_rows, 1) if only_text.lower() in row["question"].lower()]
        if not rows:
            print(f"No questions containing '{only_text}'")
            return 0, 0, []
    else:
        rows = [(i, row) for i, row in enumerate(all_rows, 1)]

    total = len(rows)
    passed = 0
    failed = []
    rate_limits = 0

    for idx, (orig_i, row) in enumerate(rows, 1):
        question = row["question"]
        expected_type = row["expected_type"]
        must_contain = row["must_contain"] if row["must_contain"] else ""
        must_not_contain = row["must_not_contain"] if row.get("must_not_contain") else ""
        scheme = row.get("scheme", "") if "scheme" in row else ""

        # Rate limit: wait 6 seconds between questions (Groq free tier: 30 req/min)
        if idx > 1:
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
                    print(f"      [RATE LIMIT 429] Q{orig_i}, attempt {attempt+1}/3, waiting 30s...")
                    if attempt < 2:
                        time.sleep(30)
                        continue
                data = resp.json()
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(30)
                    continue
                failed.append((orig_i, question, f"Request error: {e}", ""))
                data = {}
                break
        else:
            # If we exhausted retries
            if not data:
                failed.append((orig_i, question, "Rate limited after retries", ""))
                continue

        answer = data.get("answer", "")
        title = data.get("title", "") or ""
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

        # Check pass/fail - check must_contain against title + answer combined
        type_match = (actual_type == expected_type)
        combined = (title + " " + answer).strip()
        content_match = True
        if must_contain:
            content_match = must_contain.lower() in combined.lower()
        not_contain_match = True
        if must_not_contain:
            not_contain_match = must_not_contain.lower() not in combined.lower()

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
            failed.append((orig_i, question, "; ".join(reason_parts), combined[:200]))

        scheme_str = f" [scheme={scheme}]" if scheme else ""
        print(f"{orig_i:3d} [{status}]{scheme_str} {question[:80]}...")
        if status == "FAIL":
            print(f"      Expected: type={expected_type}, contains='{must_contain}', not_contains='{must_not_contain}'")
            print(f"      Intent: {debug.get('intent')}, Guardrail: {guardrail}")
            print(f"      Matches: {debug.get('matches')}")
            # Handle unicode for printing
            safe_combined = combined[:150].encode('ascii', 'replace').decode('ascii')
            print(f"      Got:      type={actual_type}, answer='{safe_combined}'")

    print(f"\n{'='*60}")
    print(f"Total: {total}, Passed: {passed}, Failed: {len(failed)}")
    print(f"Rate limits (429): {rate_limits}")
    if total > 0:
        print(f"Score: {passed}/{total} ({passed/total*100:.1f}%)")

    if failed:
        print(f"\nFailed questions:")
        for orig_i, q, reason, ans in failed:
            safe_q = q.encode('ascii', 'replace').decode('ascii')
            safe_ans = ans[:200].encode('ascii', 'replace').decode('ascii')
            print(f"  {orig_i}: {safe_q}")
            print(f"     Reason: {reason}")
            print(f"     Answer: {safe_ans}")

    # Save failed indices for --failed option
    _save_failed_indices(failed)

    return passed, total, failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation")
    parser.add_argument("--only", type=str, help="Filter questions containing this text")
    parser.add_argument("--failed", action="store_true", help="Re-run only failed rows from last run")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test (~20 rows, 2-3 per type)")
    args = parser.parse_args()

    csv_path = "tests/eval_questions.csv"
    run_eval(csv_path, only_text=args.only, use_failed=args.failed, quick=args.quick)
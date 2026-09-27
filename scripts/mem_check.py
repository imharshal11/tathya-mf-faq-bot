"""Memory check script: runs 5 test queries via FastAPI TestClient and reports peak RSS."""

import os
import sys
import psutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.api import app


def get_rss_mb() -> float:
    """Get current process RSS in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def main():
    client = TestClient(app)

    # Test queries
    questions = [
        "What is the expense ratio of HDFC Large Cap Fund?",
        "Who manages HDFC Balanced Advantage Fund?",
        "What is the lock-in of HDFC ELSS Tax Saver Fund?",
        "What is the exit load of HDFC Small Cap Fund?",
        "Who won the IPL?",
    ]

    print("Starting memory check...")
    print(f"Initial RSS: {get_rss_mb():.1f} MB")
    print()

    peak_rss = get_rss_mb()

    for i, q in enumerate(questions, 1):
        rss_before = get_rss_mb()
        resp = client.post("/chat", json={"question": q})
        rss_after = get_rss_mb()
        peak_rss = max(peak_rss, rss_after)

        data = resp.json()
        debug = data.get("debug", {})
        matches = debug.get("matches", [])
        top_score = matches[0]["score"] if matches else 0

        print(f"Q{i}: {q}")
        print(f"  RSS before: {rss_before:.1f} MB, after: {rss_after:.1f} MB, delta: {rss_after - rss_before:+.1f} MB")
        print(f"  Answer: {data['answer'][:80]}...")
        print(f"  Top score: {top_score:.4f}, Threshold passed: {debug.get('threshold_passed')}")
        print()

    print(f"Peak RSS: {peak_rss:.1f} MB")
    print(f"Target: < 400 MB")
    print(f"Status: {'PASS' if peak_rss < 400 else 'FAIL'}")


if __name__ == "__main__":
    main()
import requests
import json
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Test queries
queries = [
    'What is the expense ratio of HDFC Large Cap Fund?',
    'What is the exit load of HDFC Small Cap Fund?',
    'What is the lock-in period of HDFC ELSS Tax Saver Fund?',
    'What is the benchmark of HDFC Balanced Advantage Fund?',
    'What is the minimum SIP for HDFC Flexi Cap Fund?',
    'Who manages HDFC Balanced Advantage Fund?',
    'What is the minimum amount to invest in HDFC ELSS?',
    'Should I buy HDFC Small Cap Fund?',
    'My PAN is ABCDE1234F',
    'What were the past returns of HDFC Large Cap Fund?',
]

for q in queries:
    try:
        resp = requests.post('http://127.0.0.1:8000/chat', json={'question': q}, timeout=60)
        data = resp.json()
        print(f'Q: {q}')
        print(f'A: {data.get("answer", "")}')
        print(f'fallback: {data.get("debug", {}).get("fallback", False)}')
        print(f'guardrail: {data.get("debug", {}).get("guardrail", None)}')
        print(f'threshold_passed: {data.get("debug", {}).get("threshold_passed", None)}')
        matches = data.get("debug", {}).get("matches", [])
        if matches:
            for m in matches:
                print(f'  match: {m}')
        print('---')
    except Exception as e:
        print(f'Error for Q: {q} -> {e}')
        print('---')
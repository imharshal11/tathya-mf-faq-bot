import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Out-of-corpus queries to tune threshold
queries = [
    'Who won the IPL?',
    'What is the weather in Mumbai?',
    'What is my portfolio value?',
]

for q in queries:
    try:
        resp = requests.post('http://127.0.0.1:8000/chat', json={'question': q}, timeout=30)
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
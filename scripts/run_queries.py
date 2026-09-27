import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

questions = [
    'What is the expense ratio of HDFC Large Cap Fund?',
    'What is the lock-in period of HDFC ELSS Tax Saver Fund?',
    'What is the exit load of HDFC Small Cap Fund?',
    'What is the benchmark of HDFC Balanced Advantage Fund?',
    'What is the minimum SIP for HDFC Flexi Cap Fund?',
    'Who manages HDFC Small Cap Fund?',
    'What is the riskometer level of HDFC ELSS Tax Saver Fund?',
    'Should I buy HDFC Small Cap Fund?',
    'My PAN is ABCDE1234F',
    'What were the past returns of HDFC Large Cap Fund?'
]

for q in questions:
    r = requests.post('http://127.0.0.1:8000/chat', json={'question': q})
    data = r.json()
    print('Q: ' + q)
    print('A: ' + data.get('answer', ''))
    print('Source: ' + data.get('source_url', ''))
    print('Date: ' + data.get('fetched_date', ''))
    print('Debug: ' + str(data.get('debug', {})))
    print('---')
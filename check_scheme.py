import csv
with open('tests/eval_questions.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['question'] == 'aum?':
            print(f"question: {row['question']}")
            print(f"scheme: '{row['scheme']}'")
            print(f"expected_type: {row['expected_type']}")
            print(f"must_contain: {row['must_contain']}")
            print(f"must_not_contain: {row['must_not_contain']}")
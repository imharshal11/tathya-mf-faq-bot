with open('tests/eval_questions.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'aum?' in line:
            print(f"Line {i+1}: {line.strip()}")
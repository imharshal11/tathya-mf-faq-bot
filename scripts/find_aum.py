import re

with open(r'C:\Users\Harshal Sarowar\OneDrive\Desktop\Groww Rag Bot\data\raw\raw_hdfc-small-cap.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the main fund data - look for the fund's own aum
matches = list(re.finditer(r'"aum":\s*(\d+\.?\d*)', content))
for i, m in enumerate(matches):
    context = content[max(0,m.start()-100):m.end()+50]
    print(f'Match {i}: {m.group(1)} - Context: ...{context}...')
    print()
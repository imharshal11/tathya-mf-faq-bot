import re

funds = [
    ('HDFC Large Cap Fund', 'data/raw/raw_hdfc-large-cap-fund--direct-growth.html'),
    ('HDFC Flexi Cap Fund', 'data/raw/raw_hdfc-flexi-cap-fund-formerly-hdfc-equity-fund--direct-growth.html'),
    ('HDFC ELSS Tax Saver Fund', 'data/raw/raw_hdfc-elss-tax-saver-fund--direct-plan-growth.html'),
    ('HDFC Small Cap Fund', 'data/raw/raw_hdfc-small-cap-fund--direct-growth.html'),
    ('HDFC Balanced Advantage Fund', 'data/raw/raw_hdfc-balanced-advantage-fund--direct-growth.html'),
]

for name, path in funds:
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Search for lock_in in JSON
    lock_matches = re.findall(r'"lock_in"[^}]*}', html)
    for m in lock_matches[:2]:
        print(f'{name} JSON: {m}')
    
    # Also search for 'Lock-in period' text
    text_matches = re.findall(r'Lock.?in period[^<\n]*', html, re.IGNORECASE)
    for m in text_matches[:2]:
        print(f'{name} TEXT: {m}')
    
    print()
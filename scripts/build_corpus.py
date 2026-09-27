import re
import json
from bs4 import BeautifulSoup
from datetime import date

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('–', '-').replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    return text.strip()

def extract_fund_json(html, search_id, scheme_name):
    """Extract the fund JSON data matching the search_id"""
    # First try to find by search_id
    for m in re.finditer(r'(\{.*?expense_ratio.*?\})', html):
        try:
            data = json.loads(m.group(1))
            if data.get('search_id') == search_id:
                return data
        except:
            pass
    
    # Fallback: find by scheme name keywords
    keywords = scheme_name.replace('–', '-').replace('-', ' ').split()
    for m in re.finditer(r'(\{.*?expense_ratio.*?\})', html):
        try:
            data = json.loads(m.group(1))
            sname = data.get('scheme_name', '') or data.get('fund_name', '')
            if 'HDFC' in sname:
                for kw in keywords:
                    if kw.lower() in sname.lower():
                        return data
        except:
            pass
    
    # Third fallback: extract values directly from HTML using regex
    return None

def extract_current_exit_load(html):
    """Extract the current exit load rule (not historical)"""
    # Look for the current exit load in the exit load section
    patterns = [
        r'Exit Load for units in excess of 15% of the investment,1% will be charged for redemption within 1 year',
        r'Exit load of 1% if redeemed within 1 year',
        r'Exit load is (?:zero|nil|Nil)',
        r'Exit load.*?(\d+%.*?year)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            if match.groups():
                return match.group(1).strip()
            return match.group(0).strip()
    return None

def extract_fund_objective(html):
    """Extract the fund's investment objective from About section"""
    # Look for "About" or "Fund objective" section
    patterns = [
        r'About the fund.*?The scheme seeks to (.*?)(?=\.|$)',
        r'Investment objective.*?The scheme seeks to (.*?)(?=\.|$)',
        r'The scheme seeks to (.*?)(?=\.|$)',
        r'Fund objective.*?The scheme seeks to (.*?)(?=\.|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            obj = clean_text(match.group(1))
            if len(obj) > 20:
                return f"The scheme seeks to {obj}."
    return None

def extract_fund_manager_clean(html, search_id, scheme_name):
    """Extract clean fund manager info for this specific fund"""
    # Find the fund manager in JSON for this specific fund
    for m in re.finditer(r'(\{.*?fund_manager.*?\})', html):
        try:
            data = json.loads(m.group(1))
            if data.get('search_id') == search_id:
                if data.get('fund_manager'):
                    mgr = data['fund_manager']
                    # Clean up the manager name - remove extra text
                    mgr = re.sub(r'View details.*', '', mgr)
                    mgr = re.sub(r'Education.*', '', mgr)
                    mgr = re.sub(r'Experience.*', '', mgr)
                    mgr = re.sub(r'Also manages.*', '', mgr)
                    mgr = re.sub(r'Fund management', '', mgr)
                    mgr = re.sub(r'\s+', ' ', mgr)
                    return mgr.strip()
        except:
            pass
    
    # Fallback: look for fund manager in JSON with keyword matching
    keywords = scheme_name.replace('–', '-').replace('-', ' ').split()
    for m in re.finditer(r'(\{.*?fund_manager.*?\})', html):
        try:
            data = json.loads(m.group(1))
            sname = data.get('scheme_name', '') or data.get('fund_name', '')
            if 'HDFC' in sname:
                for kw in keywords:
                    if kw.lower() in sname.lower():
                        if data.get('fund_manager'):
                            mgr = data['fund_manager']
                            mgr = re.sub(r'View details.*', '', mgr)
                            mgr = re.sub(r'Education.*', '', mgr)
                            mgr = re.sub(r'Experience.*', '', mgr)
                            mgr = re.sub(r'Also manages.*', '', mgr)
                            mgr = re.sub(r'Fund management', '', mgr)
                            mgr = re.sub(r'\s+', ' ', mgr)
                            return mgr.strip()
        except:
            pass
    
    return None

def extract_fund_data_from_html(html, scheme_name, search_id):
    """Extract fund data directly from HTML using regex patterns"""
    keywords = scheme_name.replace('–', '-').replace('-', ' ').split()
    data = {}
    
    # Use search_id for precise matching - find the complete fund JSON object
    fund_json = None
    for m in re.finditer(r'(\{.*?search_id\s*:\s*"' + re.escape(search_id) + r'".*?\})', html):
        try:
            fund_json = json.loads(m.group(1))
            break
        except:
            pass
    
    # If found complete JSON, extract all fields from it
    if fund_json:
        if fund_json.get('expense_ratio'):
            exp = fund_json['expense_ratio']
            if '%' not in str(exp):
                exp = f"{exp}%"
            data['expense_ratio'] = exp
        if fund_json.get('benchmark') or fund_json.get('benchmark_name'):
            data['benchmark'] = fund_json.get('benchmark') or fund_json.get('benchmark_name')
        if fund_json.get('risk'):
            data['risk'] = fund_json['risk']
        if fund_json.get('min_sip_investment'):
            data['min_sip_investment'] = str(fund_json['min_sip_investment'])
        if fund_json.get('aum'):
            data['aum'] = str(fund_json['aum'])
        if fund_json.get('fund_house'):
            data['fund_house'] = fund_json['fund_house']
        if fund_json.get('fund_manager'):
            data['fund_manager'] = fund_json['fund_manager']
    
    # Fallback: keyword-based matching with larger context
    if not data.get('expense_ratio'):
        for m in re.finditer(r'expense_ratio["\s:]+([\d.]+)', html):
            val = m.group(1)
            context = html[max(0, m.start()-2000):m.end()+2000]
            for kw in keywords:
                if kw.lower() in context.lower():
                    data['expense_ratio'] = val
                    break
            if data.get('expense_ratio'):
                break
    
    if not data.get('benchmark'):
        for m in re.finditer(r'benchmark["\s:]+["\s]*([^",\}]+)', html):
            val = m.group(1).strip()
            if val and ('NIFTY' in val or 'BSE' in val or 'CRISIL' in val or 'SENSEX' in val):
                context = html[max(0, m.start()-2000):m.end()+2000]
                for kw in keywords:
                    if kw.lower() in context.lower():
                        data['benchmark'] = val
                        break
            if data.get('benchmark'):
                break
    
    if not data.get('risk'):
        for m in re.finditer(r'"risk"\s*:\s*"([^"]+)"', html):
            val = m.group(1).strip()
            context = html[max(0, m.start()-2000):m.end()+2000]
            for kw in keywords:
                if kw.lower() in context.lower():
                    data['risk'] = val
                    break
            if data.get('risk'):
                break
    
    if not data.get('min_sip_investment'):
        for m in re.finditer(r'min_sip_investment["\s:]+(\d+)', html):
            val = m.group(1)
            context = html[max(0, m.start()-2000):m.end()+2000]
            for kw in keywords:
                if kw.lower() in context.lower():
                    data['min_sip_investment'] = val
                    break
            if data.get('min_sip_investment'):
                break
    
    if not data.get('aum'):
        for m in re.finditer(r'"aum"\s*:\s*([\d.]+)', html):
            val = m.group(1)
            context = html[max(0, m.start()-2000):m.end()+2000]
            for kw in keywords:
                if kw.lower() in context.lower():
                    data['aum'] = val
                    break
            if data.get('aum'):
                break
    
    if not data.get('fund_house'):
        for m in re.finditer(r'fund_house["\s:]+["\s]*([^",\}]+)', html):
            val = m.group(1).strip()
            context = html[max(0, m.start()-2000):m.end()+2000]
            for kw in keywords:
                if kw.lower() in context.lower():
                    data['fund_house'] = val
                    break
            if data.get('fund_house'):
                break
    
    if not data.get('fund_manager'):
        for m in re.finditer(r'fund_manager["\s:]+["\s]*([^",\}]+)', html):
            val = m.group(1).strip()
            context = html[max(0, m.start()-2000):m.end()+2000]
            for kw in keywords:
                if kw.lower() in context.lower():
                    data['fund_manager'] = val
                    break
            if data.get('fund_manager'):
                break
    
    # Stamp duty - fund-specific
    stamp_match = re.search(r'Stamp duty on investment:.*?([\d.]+%)', html, re.IGNORECASE | re.DOTALL)
    if stamp_match:
        data['stamp_duty'] = f"Stamp duty on investment: {stamp_match.group(1)} (from July 1st, 2020)."
    
    # FAQs
    faqs = extract_faqs_clean(html)
    if faqs:
        data['faqs'] = []
        for q, a in faqs:
            if len(a) > 30:
                data['faqs'].append(f"Q: {q} A: {a}")
    
    return data


def extract_aum_with_date(html, search_id, scheme_name):
    """Extract AUM and its date for this specific fund"""
    keywords = scheme_name.replace('–', '-').replace('-', ' ').split()
    for m in re.finditer(r'(\{.*?aum.*?\})', html):
        try:
            data = json.loads(m.group(1))
            sname = data.get('scheme_name', '') or data.get('fund_name', '')
            if 'HDFC' in sname:
                for kw in keywords:
                    if kw.lower() in sname.lower():
                        if data.get('aum'):
                            aum = data['aum']
                            as_of = data.get('aum_as_on', data.get('as_of_date', ''))
                            return aum, as_of
        except:
            pass
    
    # Fallback: search in text
    aum_match = re.search(r'Fund size \(AUM\).*?₹([\d,]+\.?\d*)\s*Cr', html)
    if aum_match:
        return aum_match.group(1), ""
    return None, None

def extract_faqs_clean(html):
    """Extract FAQs from the FAQ section"""
    faqs = []
    
    # Look for FAQ schema in script tags
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL):
        json_str = m.group(1).strip()
        try:
            data = json.loads(json_str)
            if data.get('@type') == 'FAQPage':
                if 'mainEntity' in data:
                    for item in data['mainEntity']:
                        if item.get('@type') == 'Question':
                            q = clean_text(item.get('name', ''))
                            a = clean_text(item.get('acceptedAnswer', {}).get('text', ''))
                            if q and a and len(a) > 20:
                                skip_keywords = ['return', 'performance', 'nav', 'yield', 'profit', 'gain', 'loss']
                                if not any(kw in q.lower() for kw in skip_keywords):
                                    faqs.append((q, a))
                elif '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Question':
                            q = clean_text(item.get('name', ''))
                            a = clean_text(item.get('acceptedAnswer', {}).get('text', ''))
                            if q and a and len(a) > 20:
                                skip_keywords = ['return', 'performance', 'nav', 'yield', 'profit', 'gain', 'loss']
                                if not any(kw in q.lower() for kw in skip_keywords):
                                    faqs.append((q, a))
        except:
            pass
    
    return faqs

def extract_min_investments(html):
    """Extract minimum 1st and 2nd investment"""
    min1 = None
    min2 = None
    
    for m in re.finditer(r'Min\.?\s*for\s*1st\s*investment.*?([\d,]+)', html, re.IGNORECASE):
        min1 = m.group(1).replace(',', '')
    for m in re.finditer(r'Min\.?\s*for\s*2nd\s*investment.*?([\d,]+)', html, re.IGNORECASE):
        min2 = m.group(1).replace(',', '')
    
    return min1, min2

def extract_stamp_duty(html):
    """Extract stamp duty info"""
    match = re.search(r'Stamp duty on investment: ([\d.]+%)', html, re.IGNORECASE)
    if match:
        return f"Stamp duty on investment: {match.group(1)} (from July 1st, 2020)."
    return None

def extract_tax_implication(html):
    """Extract tax implication"""
    match = re.search(r'If you redeem within one year, returns are taxed at ([\d.]+%)', html, re.IGNORECASE)
    if match:
        short_term = match.group(1)
        match2 = re.search(r'If you redeem after one year, returns exceeding Rs [\d.]+ lakh in a financial year are taxed at ([\d.]+%)', html, re.IGNORECASE)
        if match2:
            long_term = match2.group(1)
            return f"Short-term capital gains (within 1 year) are taxed at {short_term}; long-term capital gains exceeding Rs 1.25 lakh per financial year are taxed at {long_term}."
    return None

def process_fund(html_file, scheme_name, search_id, category, source_url):
    """Process a single fund and return clean facts"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    fund_data = extract_fund_json(html, search_id, scheme_name)
    
    # Fallback: extract data directly from HTML if JSON parsing failed
    html_data = extract_fund_data_from_html(html, scheme_name, search_id)
    
    scheme_clean = scheme_name.replace('–', '-')
    
    result = {
        'scheme_name': scheme_clean,
        'category': category,
        'source_url': source_url,
        'fetched_date': date.today().isoformat(),
    }
    
    # Expense ratio
    exp = fund_data.get('expense_ratio') if fund_data else None
    if not exp:
        exp = html_data.get('expense_ratio')
    if exp:
        if '%' not in str(exp):
            exp = f"{exp}%"
        result['expense_ratio'] = f"The expense ratio of {scheme_clean} is {exp}."
    
    # Exit load - current rule only
    current_exit = extract_current_exit_load(html)
    if current_exit:
        result['exit_load'] = f"The exit load of {scheme_clean} is {current_exit}."
    elif fund_data and fund_data.get('exit_load'):
        exit_load = fund_data['exit_load']
        if exit_load and exit_load.lower() not in ['nil', 'none', '0', 'zero']:
            result['exit_load'] = f"The exit load of {scheme_clean} is {exit_load}."
        else:
            result['exit_load'] = f"The exit load of {scheme_clean} is nil."
    
    # Min SIP
    sip = fund_data.get('min_sip_investment') if fund_data else None
    if not sip:
        sip = html_data.get('min_sip_investment')
    if sip:
        if isinstance(sip, (int, float)):
            sip = str(int(sip))
        result['min_sip'] = f"The minimum SIP amount for {scheme_clean} is ₹{sip}."
    
    # Min 1st and 2nd investment
    min1, min2 = extract_min_investments(html)
    if min1:
        result['min_1st_investment'] = f"The minimum amount for the first investment in {scheme_clean} is ₹{min1}."
    if min2:
        result['min_2nd_investment'] = f"The minimum amount for additional investments in {scheme_clean} is ₹{min2}."
    
    # Lock-in
    lock_text = None
    if 'ELSS' in scheme_name or 'Tax Saver' in scheme_name:
        lock_text = "3 years (ELSS scheme)"
    else:
        # Check if page explicitly mentions no lock-in
        if re.search(r'No lock.?in|lock.?in.*?not\s+applicable', html, re.IGNORECASE):
            lock_text = "No lock-in period (open-ended scheme)"
        else:
            # Don't include lock-in if not explicitly stated
            lock_text = None
    
    if lock_text:
        result['lock_in'] = f"The lock-in period for {scheme_clean} is {lock_text}."
    
    # Riskometer
    risk = fund_data.get('risk') if fund_data else None
    if not risk:
        risk = html_data.get('risk')
    if risk:
        if risk.isdigit():
            risk_map = {'1': 'Low', '2': 'Low to Moderate', '3': 'Moderate', '4': 'Moderately High', '5': 'High', '6': 'Very High'}
            risk = risk_map.get(risk, risk)
        result['riskometer'] = f"The risk level of {scheme_clean} is {risk}."
    
    # Benchmark - search in all JSON objects for this fund
    bench = None
    keywords = scheme_name.replace('–', '-').replace('-', ' ').split()
    for m in re.finditer(r'(\{.*?benchmark.*?\})', html):
        try:
            data = json.loads(m.group(1))
            sname = data.get('scheme_name', '') or data.get('fund_name', '')
            if 'HDFC' in sname:
                for kw in keywords:
                    if kw.lower() in sname.lower():
                        if data.get('benchmark') or data.get('benchmark_name'):
                            bench = data.get('benchmark') or data.get('benchmark_name')
                            break
        except:
            pass
    
    if not bench:
        bench = html_data.get('benchmark')
    
    if bench:
        result['benchmark'] = f"The benchmark of {scheme_clean} is {bench}."
    
    # AUM
    aum, aum_date = extract_aum_with_date(html, search_id, scheme_name)
    if not aum:
        aum = html_data.get('aum')
    if aum:
        # Format AUM with commas
        try:
            aum_val = float(aum)
            aum_fmt = f"{aum_val:,.2f}".rstrip('0').rstrip('.')
        except:
            aum_fmt = str(aum)
        if aum_date:
            result['aum'] = f"The fund size (AUM) of {scheme_clean} is ₹{aum_fmt} crore as of {aum_date}."
        else:
            result['aum'] = f"The fund size (AUM) of {scheme_clean} is ₹{aum_fmt} crore."
    
    # Fund manager
    mgr = extract_fund_manager_clean(html, search_id, scheme_name)
    if not mgr:
        mgr = html_data.get('fund_manager')
    if mgr:
        result['fund_manager'] = f"The fund manager(s) of {scheme_clean} is/are {mgr}."
    
    # Fund objective
    obj = extract_fund_objective(html)
    if obj:
        result['fund_objective'] = f"The investment objective of {scheme_clean} is {obj}."
    
    # Fund house
    fund_house = fund_data.get('fund_house') if fund_data else None
    if not fund_house:
        fund_house = html_data.get('fund_house')
    if fund_house:
        result['fund_house'] = f"The fund house for {scheme_clean} is {fund_house}."
    
    # Stamp duty
    stamp = extract_stamp_duty(html)
    if stamp:
        result['stamp_duty'] = f"{stamp}"
    elif 'stamp_duty' in html_data:
        result['stamp_duty'] = html_data['stamp_duty']
    
    # Tax implication
    tax = extract_tax_implication(html)
    if tax:
        result['tax_implication'] = f"{tax}"
    
    # FAQs
    faqs = extract_faqs_clean(html)
    if faqs:
        result['faqs'] = []
        for q, a in faqs:
            if len(a) > 30:
                result['faqs'].append(f"Q: {q} A: {a}")
    
    return result


FUNDS = [
    {
        'html_file': 'data/raw/raw_hdfc-large-cap-fund--direct-growth.html',
        'scheme_name': 'HDFC Large Cap Fund - Direct Growth',
        'search_id': 'hdfc-large-cap-fund-direct-growth',
        'category': 'Large Cap',
        'source_url': 'https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth',
    },
    {
        'html_file': 'data/raw/raw_hdfc-flexi-cap-fund-formerly-hdfc-equity-fund--direct-growth.html',
        'scheme_name': 'HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth',
        'search_id': 'hdfc-equity-fund-direct-growth',
        'category': 'Flexi Cap',
        'source_url': 'https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth',
    },
    {
        'html_file': 'data/raw/raw_hdfc-elss-tax-saver-fund--direct-plan-growth.html',
        'scheme_name': 'HDFC ELSS Tax Saver Fund - Direct Plan Growth',
        'search_id': 'hdfc-elss-tax-saver-fund-direct-plan-growth',
        'category': 'ELSS',
        'source_url': 'https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth',
    },
    {
        'html_file': 'data/raw/raw_hdfc-small-cap-fund--direct-growth.html',
        'scheme_name': 'HDFC Small Cap Fund - Direct Growth',
        'search_id': 'hdfc-small-cap-fund-direct-growth',
        'category': 'Small Cap',
        'source_url': 'https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth',
    },
    {
        'html_file': 'data/raw/raw_hdfc-balanced-advantage-fund--direct-growth.html',
        'scheme_name': 'HDFC Balanced Advantage Fund - Direct Growth',
        'search_id': 'hdfc-balanced-advantage-fund-direct-growth',
        'category': 'Balanced Advantage (Hybrid)',
        'source_url': 'https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth',
    },
]

SECTION_ORDER = [
    ('expense_ratio', 'Expense Ratio'),
    ('exit_load', 'Exit Load'),
    ('min_sip', 'Minimum SIP'),
    ('min_1st_investment', 'Minimum First Investment'),
    ('min_2nd_investment', 'Minimum Additional Investment'),
    ('lock_in', 'Lock-in Period'),
    ('riskometer', 'Riskometer'),
    ('benchmark', 'Benchmark'),
    ('aum', 'Fund Size (AUM)'),
    ('fund_manager', 'Fund Manager'),
    ('fund_objective', 'Fund Objective'),
    ('fund_house', 'Fund House'),
    ('stamp_duty', 'Stamp Duty'),
    ('tax_implication', 'Tax Implication'),
    ('faqs', 'FAQs'),
]

def write_corpus_file(result):
    """Write a clean corpus file"""
    # Map scheme names to expected filenames
    name_map = {
        'HDFC Large Cap Fund - Direct Growth': 'hdfc-large-cap.md',
        'HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth': 'hdfc-flexi-cap.md',
        'HDFC ELSS Tax Saver Fund - Direct Plan Growth': 'hdfc-elss.md',
        'HDFC Small Cap Fund - Direct Growth': 'hdfc-small-cap.md',
        'HDFC Balanced Advantage Fund - Direct Growth': 'hdfc-balanced-advantage.md',
    }
    
    fname = name_map.get(result['scheme_name'], 
        result['scheme_name'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '') + '.md')
    fname = re.sub(r'[^a-z0-9-\.]', '', fname)
    fname = f"corpus/{fname}"
    
    lines = [
        f"<!-- scheme_name: {result['scheme_name']} -->",
        f"<!-- category: {result['category']} -->",
        f"<!-- source_url: {result['source_url']} -->",
        f"<!-- fetched_date: {result['fetched_date']} -->",
        "",
        f"# {result['scheme_name']}",
        "",
        f"**Category:** {result['category']}",
        f"**Source:** {result['source_url']}",
        f"**Fetched:** {result['fetched_date']}",
        "",
    ]
    
    for key, heading in SECTION_ORDER:
        if key in result:
            val = result[key]
            if key == 'faqs':
                lines.append(f"## {heading}")
                lines.append("")
                for faq in val:
                    lines.append(f"- {faq}")
                lines.append("")
            else:
                lines.append(f"## {heading}")
                lines.append(val)
                lines.append("")
    
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return fname


def build_summary_table(results):
    """Build a clean summary table"""
    rows = []
    for result in results:
        row = {
            'Scheme': result['scheme_name'],
            'Expense Ratio': result.get('expense_ratio', 'NOT FOUND').replace(f"The expense ratio of {result['scheme_name']} is ", "").replace(".", ""),
            'Exit Load': result.get('exit_load', 'NOT FOUND').replace(f"The exit load of {result['scheme_name']} is ", "").replace(".", ""),
            'Min SIP': result.get('min_sip', 'NOT FOUND').replace(f"The minimum SIP amount for {result['scheme_name']} is ", "").replace(".", ""),
            'Lock-in': result.get('lock_in', 'NOT FOUND').replace(f"The lock-in period for {result['scheme_name']} is ", "").replace(".", ""),
            'Riskometer': result.get('riskometer', 'NOT FOUND').replace(f"The risk level of {result['scheme_name']} is ", "").replace(".", ""),
            'Benchmark': result.get('benchmark', 'NOT FOUND').replace(f"The benchmark of {result['scheme_name']} is ", "").replace(".", ""),
        }
        rows.append(row)
    return rows


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    all_results = []
    for fund in FUNDS:
        print(f"Processing {fund['scheme_name']}...")
        result = process_fund(**fund)
        fname = write_corpus_file(result)
        all_results.append(result)
        print(f"  Saved: {fname}")
    
    # Print summary table
    print("\n=== SUMMARY TABLE ===")
    rows = build_summary_table(all_results)
    print("| Scheme | Expense Ratio | Exit Load | Min SIP | Lock-in | Riskometer | Benchmark |")
    print("|--------|---------------|-----------|---------|---------|------------|-----------|")
    for row in rows:
        print(f"| {row['Scheme']} | {row['Expense Ratio']} | {row['Exit Load']} | {row['Min SIP']} | {row['Lock-in']} | {row['Riskometer']} | {row['Benchmark']} |")
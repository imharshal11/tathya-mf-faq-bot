# Tathya UI Spec

Rebuild the Tathya web UI to match our approved design, using the exact wording below.
The UI is split into 3 files: web/index.html (structure and text), web/styles.css (all styles), web/app.js (all behaviour).
Plain HTML + CSS + vanilla JS, no framework. Must work on iPhone, Android and desktop browsers.
Do NOT start, stop, or kill any server. Do not edit .env or corpus files.
Do not change guardrails, retrieval, or generation logic except the small API additions below.

## BRAND
- Fonts (Google Fonts): Poppins 600/700 for the wordmark, headings and big numbers; DM Sans 400/500/700 for everything else.
- Colors: navy #0B2A5B (primary actions, user bubbles), sky #0EA5E9 (accents only, never body text), link blue #0369A1, page bg #F3F7FC (mobile) / #EEF3F9 (desktop), cards #FFFFFF, borders #E3E8EF, text #0F172A / #475569 / #64748B.
- Fund tints: Large Cap #DBEEFD, Flexi Cap #E3E6FB, ELSS Tax Saver #D5F5EE, Small Cap #FCEFCB, Balanced Advantage #E2E8F0.
- Logo: web/brand/icon.svg and web/brand/wordmark.svg (lowercase "tath" navy + "ya" sky).
- Favicons: web/brand/favicon.svg, favicon-32.png, favicon-16.png, apple-touch-icon.png, icon-512.png. theme-color #0B2A5B.
- Radii: cards 24px, bubbles 22px, pills 999px. Tap targets at least 44px.

## API ADDITIONS
1. GET /funds: read the 5 corpus files and return per fund: full_name (e.g. "HDFC Large Cap Fund"), short_name ("Large Cap", "Flexi Cap", "ELSS Tax Saver", "Small Cap", "Balanced Advantage"), category, source_url, fetched_date, expense_ratio, exit_load, min_sip, lock_in (if any), riskometer, benchmark, aum, fund_managers (with since dates). Parse from the corpus; no hardcoding. Format AUM with "crore", exit load as "1% if sold within 1 year".
2. POST /chat accepts an optional "scheme" field. If the question names no fund and "scheme" is set, treat it as that fund.
3. FastAPI serves web/index.html at "/", plus /styles.css, /app.js, /brand/* and /manifest.json.

## WORDING RULES
- Sentence case.
- Always "fund" in UI text (not scheme/plan/MF).
- Full names like "HDFC Large Cap Fund"; plans in brackets, e.g. "HDFC Large Cap Fund (Direct Growth)", never with " - ".
- Dates like "27 Sep 2026".
- Write "crore", not "Cr".
- Page title: "Tathya — HDFC Mutual Fund FAQ Assistant". Tagline: "Mutual fund facts, with proof."

## MOBILE (width < 768px), two views switched by JS

### A. HOME
- Header: icon (40px) + wordmark; round button aria-label "About Tathya".
- "Hi there!" (Poppins 32). Below: "Ask me about 5 HDFC mutual funds. Every answer shows its source."
- Navy pill button "Start new chat" with a sky round arrow on the right.
- Sky pill: "Facts-only. No investment advice."
- Section "Funds covered" with hint "Tap a fund to ask about it".
- 2-column tinted tiles (radius 24, white round icon, short name, fact line):
  - Large Cap: "Expense ratio: 1.03%"
  - Flexi Cap: "Expense ratio: 0.77%"
  - ELSS Tax Saver: "3-year lock-in"
  - Small Cap: "Exit load: 1% if sold within 1 year"
  - Balanced Advantage (full-width white row): "Hybrid fund · Expense ratio: 0.78%"
  - Build fact lines from /funds in this format. Tapping a tile opens CHAT with that fund selected.
- Disclaimer card (info icon, 12px, aria-label "Investment disclaimer"): "Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts only, not investment advice."
- "Built by Harshal S" with round icon links, target="_blank" rel="noopener":
  - LinkedIn: https://www.linkedin.com/in/imharshal11 (aria-label "Harshal S on LinkedIn")
  - GitHub: https://github.com/imharshal11 (aria-label "Harshal S on GitHub")
- Floating white bottom nav pill: Home, Chat, Funds, About (active = navy circle).

### B. CHAT
- Header: back button (aria-label "Back to home"), wordmark, button (aria-label "New chat").
- Fund switcher pills (scrollable, active navy): Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage.
- Messages (see MESSAGES).
- Composer: white rounded pill, input placeholder "Ask a question about a fund…", navy round Send button (48px, aria-label "Send").
- Under the composer (11px): "Mutual fund investments carry market risk. Facts only, not advice."
- Use 100dvh and env(safe-area-inset-bottom) for iPhones.

## DESKTOP (width >= 1024px)
- Top bar: logo left; center nav pill: Chat (active), Funds, About; right: sky pill "Facts-only. No investment advice." + navy pill "New chat".
- Left sidebar card (280px):
  - "Funds covered" list (tint square, full name, fact line). Fact lines: "Large Cap · Expense ratio: 1.03%", "Flexi Cap · Expense ratio: 0.77%", "ELSS · 3-year lock-in", "Small Cap · Expense ratio: 0.78%", "Hybrid fund · Expense ratio: 0.78%". Active item background #EAF2FF.
  - "Recent questions": questions asked this session (in memory), clickable to re-show the answer.
  - Bottom card: "HS" avatar, "Built by" / "Harshal S", LinkedIn + GitHub icon links.
- Main card, empty state:
  - Layered circles with the app icon.
  - Heading: "Hi, I'm Tathya. Which fund fact can I find for you?" ("Tathya" in #0284C7).
  - Subtitle: "I answer only from 5 HDFC fund pages, and I show the source and date for every answer."
  - Chips that prefill the input: Expense ratio, Exit load, Minimum SIP, Lock-in period, Riskometer, Benchmark, Fund managers.
  - Composer card: textarea placeholder "Ask a question, for example: "What is the exit load of HDFC Small Cap Fund?""; label "Fund" + select (All 5 funds, HDFC Large Cap Fund, HDFC Flexi Cap Fund, HDFC ELSS Tax Saver Fund, HDFC Small Cap Fund, HDFC Balanced Advantage Fund); navy pill "Send".
  - Fund pills row with label "Funds covered".
  - Disclaimer: "Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts from public Groww pages (as of 27 Sep 2026) for information only. It is not investment advice or a recommendation to buy or sell any fund."
- After the first question, conversation view:
  - Header: full fund name + "Direct Plan · Growth" + green pill "Verified sources".
  - Messages.
  - Rounded composer, placeholder "Ask a question about a fund…".
  - Under it: "Mutual fund investments carry market risk. Facts only, not advice."
- Right "Source facts" card (320px), filled from /funds for the current fund:
  - Tinted title card: "HDFC Large Cap Fund (Direct Growth)" + "groww.in · Updated 27 Sep 2026".
  - Rows: Expense ratio, Exit load, Minimum SIP, Riskometer, Benchmark, Fund size, Fund managers.
  - Navy button "Open source page".
  - Box titled "Investment disclaimer": "Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts from public Groww pages (as of 27 Sep 2026) for information only. It is not investment advice or a recommendation to buy or sell any fund. Returns and performance are not shown. Please check the official HDFC factsheet."

## TABLET (768-1023px)
Desktop layout without the right Source facts card.

## MESSAGES
- User bubble: navy, radius 22 22 6 22, small buttons "Copy" and "Ask again".
- Answer: small "t" avatar + card.
  - If the answer has exactly one key figure (%, ₹ amount, or "X years"), show it big (Poppins 36, navy) with a small label from the question topic (e.g. "expense ratio"), then the sentence.
  - Strip: "Source: groww.in" (link, new tab) + "Updated 27 Sep 2026" (from fetched_date).
  - Actions: "Copy" (clipboard, toast "Copied"), "Share" (navigator.share, fallback copy).
- Guardrail replies use the "title" field if present:
  - advisory / returns: warm card (#FFF4E5, text #7C2D12) with title, text and a "Learn more" link.
  - pii: warm card, no link.
  - clarify / out_of_scope / greeting / thanks / live_data / plan_type: neutral white card.
  - not found: neutral card + "Learn more".
- While waiting: "Tathya is typing…".
- API error: "Something went wrong. Please try again in a moment."
- Timeout: "The app is starting up. This can take up to a minute. Please try again."
- Always keep the user's message visible.

## QUALITY
- Real <button>, <a>, <label> elements; aria-labels on icon buttons; visible focus rings.
- Text contrast at least 4.5:1.
- No localStorage.

## TEST, THEN SHIP
1. Run scripts/run_eval.py; the score must not drop.
2. Check at 390px, 768px and 1440px widths that nothing overflows.
3. Commit and push after each step.
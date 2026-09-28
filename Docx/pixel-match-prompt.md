#####################################################################
PROJECT RULES (apply to every phase)
#####################################################################
- Do NOT start, stop, or kill any server (it runs at http://127.0.0.1:8000). Do not edit .env or corpus files.
- Design files are in Docx/design/. Read them from there.
- Current files: web/index.html, web/styles.css, web/app.js (create app.js if missing). You may rename classes/DOM to the structure below, but keep index.html, styles.css and app.js consistent with each other.
- After EACH phase: commit with a clear message and git push.
- Fund data: use the existing GET /funds endpoint (src/api.py). Do not scrape or hardcode fund values.
- Questions: POST /chat with {"question": text, "scheme": selected fund or null}. Response: answer, title (optional), source_url, fetched_date, debug.guardrail.
- Reply styles by debug.guardrail: advisory, returns, pii = warm card (#FFF4E5); clarify, out_of_scope, greeting, thanks, live_data, plan_type, and "I don't have that information yet" = neutral white card (border 1px #E3E8EF). Show "title" in bold if present. Show "Learn more" only if source_url is set. No big number and no source strip on these cards.
- Also build: "Tathya is typing…" while waiting; error "Something went wrong. Please try again in a moment."; timeout after 60s "The app is starting up. This can take up to a minute. Please try again."; Copy/Share with a "Copied" toast; desktop "Recent questions" from this session.
- At the end of Phase 4 and Phase 8: run .venv\Scripts\python scripts/run_eval.py (must stay 64/64) and .venv\Scripts\python scripts/check_layout.py.

You are working on our ongoing Tathya project (HDFC mutual fund FAQ RAG chatbot, served at 127.0.0.1:8000).
TASK: make the frontend look EXACTLY like the 4 design files on desktop, tablet and mobile.
This is a pixel-match task, NOT a redesign.

#####################################################################
SECTION 0 — SOURCE OF TRUTH
#####################################################################
Docx/design/desktop-home.html   → desktop HOME state (1440×900)
Docx/design/desktop-chat.html   → desktop CHAT state, after an answer (1440×900)
Docx/design/mobile-home.html    → mobile HOME (390×844)
Docx/design/mobile-chat.html    → mobile CHAT (390×844)

#####################################################################
SECTION 1 — STRICT RULES
#####################################################################
1. Do NOT redesign, "improve", simplify or approximate anything.
2. For every element: open the design file, copy its HTML structure and SVG EXACTLY, then move inline
   styles into CSS classes with IDENTICAL values (px, hex, radius, weight, gap, shadow).
3. Use ONLY the SVG icons given in this prompt / the design files. No icon fonts, no emoji, no substitutes,
   no repeated generic icon. Never replace an icon with a text label.
4. Copy all visible text exactly (including "·", "₹", capitalisation, punctuation). No uppercase transforms.
5. Fonts: Google Fonts Poppins 600/700 + DM Sans 400/500/700.
   Poppins ONLY for: logo wordmark, logo "t" tiles, h1 headings, big answer numbers (e.g. 1.03%).
   Everything else DM Sans.
6. Do NOT change backend / RAG / retrieval logic.
7. First inspect the current frontend (web/index.html, web/styles.css, web/app.js) and tell me which files you will edit.
8. Work in PHASES. After each phase: commit and push, then stop, list files changed and items fixed, and wait for me to reply "next".
9. Test ONLY in DevTools device mode at zoom 100%: 1440×900 (desktop), 900×1024 (tablet), 390×844 (mobile).
   Never test by dragging the browser window.

ALL SVGs in this prompt use these attributes unless stated:
viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"

ICON LIBRARY (use these exact paths)
- info:        <circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>
- shield:      <path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/>
- plus:        <path d="M12 5v14"/><path d="M5 12h14"/>
- arrow-right: <path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>
- arrow-up:    <path d="M12 19V5"/><path d="M6 11l6-6 6 6"/>
- back:        <path d="M15 6l-6 6 6 6"/>
- chevron:     <path d="M9 6l6 6-6 6"/>
- edit:        <path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>
- chat:        <path d="M5 5h14v10H9l-4 4V5z"/>
- home:        <path d="M4 11l8-7 8 7"/><path d="M6 10v10h12V10"/>
- grid:        <rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/>
- external:    <path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>
- copy:        <rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a1 1 0 0 1 1-1h9"/>
- share:       <path d="M12 4v11"/><path d="M8 8l4-4 4 4"/><path d="M5 14v5h14v-5"/>
- linkedin:    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>
- github:      <path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>
- fund-large:  <path d="M4 19h16"/><path d="M7 15V9"/><path d="M12 15V5"/><path d="M17 15v-4"/>
- fund-flexi:  <path d="M4 12a8 8 0 0 1 16 0"/><path d="M20 12a8 8 0 0 1-16 0"/><path d="M9 12l2 2 4-4"/>
- fund-elss:   <rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>
- fund-small:  <path d="M4 17l5-5 4 4 7-7"/><path d="M15 9h5v5"/>
- fund-baf:    <path d="M12 4v16"/><path d="M5 8h14"/><path d="M5 8l-2 6h4l-2-6z"/><path d="M19 8l-2 6h4l-2-6z"/>

FUND COLOURS: Large #DBEEFD · Flexi #E3E6FB · ELSS #D5F5EE · Small #FCEFCB · Balanced Advantage #E2E8F0 (desktop) / white card (mobile)

#####################################################################
SECTION 2 — KNOWN BUGS IN CURRENT BUILD (all must be fixed)
#####################################################################
Desktop:
D1  Source panel visible on HOME with "—" values (HOME must be 2 columns; panel only after first answer, real values).
D2  Source panel missing "Source facts" label.
D3  Missing icons: shield (Facts pill), plus (New chat), arrow-up (Send), external (Open source page).
D4  Composer textarea has its own inner border box; Fund select too wide.
D5  Built-by card layout wrong (must be one row: avatar → text column → icons).
D6  Nav "Chat" tab has no active style.
D7  Bottom disclaimer has an extra ⓘ icon; "Funds covered" label sits above chips instead of inline.
D8  Main card shows a scrollbar on HOME.
Mobile:
M1  Bottom nav shows TEXT labels in circles — must be ICON-ONLY 50px circles.
M2  "Start new chat" and Facts band touch screen edges — need 20px side padding.
M3  Logo tile and wordmark touch — need 10px gap.
M4  "Start new chat" uses outline ⊕ — must be 38px filled sky circle with white arrow-right.
M5  Facts pill is a full-width band without icon — must hug content, rounded, with shield.
M6  "FUNDS COVERED" uppercase + blue hint on new line — must be one row, normal case.
M7  All fund cards use the same house icon — each needs its own icon.
M8  Fund card subtitles missing.
M9  Fund grid indented more than other content.
M10 Balanced Advantage card missing subtitle and chevron.
M11 "Harshal S" not bold.

#####################################################################
PHASE 1 — GLOBAL RESET + DESKTOP SHELL
#####################################################################
Add once:
*, *::before, *::after { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
body { font-family: 'DM Sans', sans-serif; color: #0F172A; }
button, input, select, textarea { font-family: inherit; }
textarea { border: none; outline: none; resize: none; background: transparent; padding: 0; box-shadow: none; }
a { color: #0369A1; } a:hover { color: #075985; }
.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }

Desktop (min-width: 1024px). Header is a normal grid row — NO position fixed/absolute/sticky.
DOM: .app > .topbar  and  .app > .workspace > .sidebar, .main, .sources-panel

.app { height:100vh; padding:20px; background:#EEF3F9; display:grid;
       grid-template-rows:64px minmax(0,1fr); gap:20px; overflow:hidden; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding:0 4px; position:static; }
.topbar .brand   { width:280px; display:flex; align-items:center; gap:10px; }
.topbar .actions { width:420px; display:flex; align-items:center; justify-content:flex-end; gap:10px; }
.workspace { display:grid; gap:20px; min-height:0; grid-template-columns:280px minmax(0,1fr); }
.workspace.is-chat { grid-template-columns:280px minmax(0,1fr) 320px; }
.sources-panel { display:none !important; }
.workspace.is-chat .sources-panel { display:flex !important; flex-direction:column; }
.sidebar, .main, .sources-panel { min-height:0; background:#FFFFFF; border-radius:24px; }
.main { overflow:hidden; display:flex; flex-direction:column; }
.messages { flex:1; overflow-y:auto; }   /* the ONLY scrolling area */

STATE RULES
- No messages = HOME: .workspace WITHOUT is-chat. Source panel hidden. No fund active in sidebar. No scrollbar in main.
- After first answer = CHAT: add is-chat. Source panel shows facts of the fund in the LATEST answer.
  Sidebar active fund = fund of latest answer.
- "New chat" clears messages → HOME.

STOP. Report. Wait for "next".

#####################################################################
PHASE 2 — DESKTOP TOPBAR + SIDEBAR  (copy Docx/design/desktop-home.html)
#####################################################################
Topbar
- Logo tile 40×40, radius 12, bg #0B2A5B, position relative, white Poppins 700 24px "t",
  dot 6×6 #0EA5E9 absolute top 8 right 8.
- Wordmark Poppins 700 24px, letter-spacing -0.5px: "tath" #0B2A5B + "ya" #0EA5E9.
- Nav pill: bg #FFF, border 1px #E3E8EF, radius 999, padding 5, gap 4.
  Tabs: height 40, padding 0 20, radius 999, 14px, display flex, align-items center, no underline.
  ACTIVE "Chat": bg #EAF2FF, color #0B2A5B, weight 700. Inactive "Funds", "About": color #475569, weight 500.
- Facts pill: display flex, align-items center, gap 8, padding 9px 14px, radius 999, bg #E0F2FE,
  color #075985, 13px/500. shield SVG 15px stroke #075985 width 2. Text "Facts-only. No investment advice."
- New chat: height 44, padding 0 18, radius 999, bg #0B2A5B, white 14px/500, display flex, gap 8.
  plus SVG 17px stroke #FFF width 2, then "New chat".

Sidebar: padding 18, display flex column, gap 18, full height.
- Label "Funds covered": 12px/500 #64748B, padding 0 10px 6px.
- Fund row button: background transparent, border none, radius 12, padding 9px 10px, text-align left,
  display flex, align-items CENTER, gap 10.
  Swatch 12×12, radius 4, border 1px #CBD5E1, flex-shrink 0, fund colour.
  Title 14px/700 #0F172A. Subtitle 12px #64748B (values from GET /funds).
  Hover bg #F6F8FB. Active (CHAT only): bg #EAF2FF + title colour #0B2A5B.
- "Recent questions" label (same style) + items: 13px #334155, chat SVG 15px stroke #64748B,
  single line ellipsis. Hide the label if there are no recent questions.
- Spacer (flex-grow 1).
- Built-by card — ONE HORIZONTAL ROW, in this exact order:
  container: bg #F3F7FC, radius 18, padding 14, display flex, align-items center, gap 10.
  [1] HS avatar 38×38 circle bg #0B2A5B, white 13px/700, flex-shrink 0
  [2] column (flex-grow 1, gap 1): "Built by" 12px #64748B, then "Harshal S" 14px/700 #0F172A
  [3] LinkedIn 36×36 circle (bg #FFF, border 1px #E3E8EF), linkedin SVG 16px stroke #0A66C2 width 2
      → https://www.linkedin.com/in/imharshal11 (target _blank, rel noopener)
  [4] GitHub 36×36 circle (same style), github SVG 16px stroke #0F172A width 2 → https://github.com/imharshal11 (target _blank, rel noopener)

STOP. Report. Wait for "next".

#####################################################################
PHASE 3 — DESKTOP MAIN: HOME + CHAT
#####################################################################
HOME (copy Docx/design/desktop-home.html): main padding 40, display flex column, align-items center,
justify-content center, gap 22, overflow hidden (NO scrollbar).
- Hero logo: 3 nested layers, EACH display flex, align-items center, justify-content center:
  132×132 circle #EEF6FD → 98×98 circle #DBEEFD → 64×64 tile radius 18 #0B2A5B (position relative),
  "t" Poppins 700 38px white, dot 9×9 #0EA5E9 absolute top 13 right 13.
- Text block: max-width 760, flex column, gap 10, text-align center.
  h1 Poppins 600 36px, line-height 1.2, letter-spacing -0.6px, margin 0:
  Hi, I'm <span style="color:#0284C7">Tathya</span>. Which fund fact can I find for you?
  p 16px, line-height 1.5, #475569, margin 0:
  I answer only from 5 HDFC fund pages, and I show the source and date for every answer.
- Suggestion chips: container max-width 760, flex wrap, justify-content center, gap 8.
  Chip: height 38, padding 0 16, radius 999, bg #FFF, border 1px #E3E8EF, 13px/500 #0F172A.
  Chips: Expense ratio · Exit load · Minimum SIP · Lock-in period · Riskometer · Benchmark · Fund managers.
  Click → insert a template question into the textarea (do not auto-send).
- Composer card: width 100%, max-width 780, bg #FFF, border 1px #D5DDE8, radius 24,
  padding 16px 16px 14px 20px, flex column, gap 12, box-shadow 0 10px 30px rgba(11,42,91,0.08).
  textarea rows 2, 16px/1.5, NO border, NO background, NO inner box, NO padding.
  Placeholder: Ask a question, for example: "What is the exit load of HDFC Small Cap Fund?"
  Bottom row: display flex, justify-content space-between, align-items center.
   LEFT (flex, gap 8): label "Fund" 13px #64748B + <select> height 40, padding 0 14, radius 999,
        bg #F1F5F9, border 1px #E3E8EF, 14px, width auto, flex none.
        Options: All 5 funds, HDFC Large Cap Fund, HDFC Flexi Cap Fund, HDFC ELSS Tax Saver Fund,
        HDFC Small Cap Fund, HDFC Balanced Advantage Fund.
   RIGHT: Send button height 44, padding 0 20, radius 999, bg #0B2A5B, white 14px/500, border none,
        display flex, gap 8: "Send" then arrow-up SVG 17px stroke #FFF width 2.
- Funds covered row: ONE centred row (flex, wrap, align-items center, gap 8):
  INLINE label "Funds covered" 13px #64748B, then 5 chips height 32, padding 0 12, radius 999,
  13px/500 #0F172A, fund-colour backgrounds: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage.
- Disclaimer: plain <p>, NO icon, centred, 12px/1.5 #64748B, max-width 760, margin 0:
  Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts from public Groww pages (as of 27 Sep 2026) for information only. It is not investment advice or a recommendation to buy or sell any fund.

CHAT (copy Docx/design/desktop-chat.html):
- Header bar: height 68, padding 0 28, border-bottom 1px #EEF2F6, flex space-between, align-items center.
  Left: fund name 16px/700 + "Direct Plan · Growth" 12px #64748B (gap 2).
  Right badge: flex, gap 6, bg #DCFCE7, color #166534, 12px/500, padding 6px 12px, radius 999,
  dot 7×7 #16A34A, text "Verified sources".
- Messages wrapper (.messages): padding 24px 28px 0, justify-content center.
  Inner column: width 100%, max-width 700, flex column, gap 16.
- User bubble: align-self flex-end, max-width 70%, bg #0B2A5B, white 15px/1.4, padding 12px 16px,
  radius 22px 22px 6px 22px.
- Bot row: flex, gap 10, align-items flex-start.
  Avatar tile 32×32 radius 10 bg #0B2A5B, "t" Poppins 700 19px white, dot 5×5 #0EA5E9 top 6 right 6.
  Article: flex-grow 1, bg #F6F9FD, radius 6px 22px 22px 22px, padding 18px 20px, flex column, gap 10.
  Big number row (only for single number/percent answers): Poppins 600 38px #0B2A5B + label 15px #475569, gap 10, baseline aligned.
  Sentence: 16px/1.55 #1E293B, margin 0.
  Footer: flex space-between: link "Source: groww.in" 13px/500 #0369A1, gap 6, external SVG 14px stroke #0369A1
  + date "Updated 27 Sep 2026" 12px #64748B (date from data).
  Fund-manager answers: chips (flex gap 8) bg #FFF, border 1px #E3E8EF, radius 14, padding 8px 12px:
  name 14px/700, "Since …" 12px #64748B.
- Refusal answer (advice questions): article bg #FFF4E5, gap 6, padding 14px 16px:
  title "I can't give investment advice." 15px/700 #7C2D12;
  text "I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai." 14px/1.5 #7C2D12;
  link "Learn more" 13px/500 #9A3412 → https://www.mutualfundssahihai.com/en
- Composer area padding 14px 28px 10px, centred. Pill: width 100%, max-width 700, flex, gap 8, bg #FFF,
  border 1px #D5DDE8, radius 999, padding 6px 6px 6px 22px, box-shadow 0 10px 30px rgba(11,42,91,0.08).
  input: flex-grow 1, border none, outline none, transparent, 15px, placeholder "Ask a question about a fund…".
  Send: 48×48 circle bg #0B2A5B, arrow-up SVG 20px stroke #FFF width 2.
- Below: "Mutual fund investments carry market risk. Facts only, not advice." 12px #64748B centred, margin 0 0 16px.

STOP. Report. Wait for "next".

#####################################################################
PHASE 4 — SOURCE FACTS PANEL + DATA BINDING (CHAT only)
#####################################################################
Panel: padding 22, flex column, gap 14. NEVER visible in HOME state.
- Label "Source facts" 12px/500 #64748B — MUST be the first element.
- Fund card: bg #DBEEFD, radius 18, padding 16, flex column, gap 4.
  Title 16px/700 #0B2A5B line-height 1.35, e.g. "HDFC Large Cap Fund (Direct Growth)" (use display_name from GET /funds).
  Meta 12px #334155 "groww.in · Updated <date>".
- <dl> margin 0, rows: display flex, justify-content space-between, gap 12, padding 12px 0,
  border-bottom 1px #EEF2F6. dt 13px #64748B. dd margin 0, 13px/700, text-align right
  (#0B2A5B for Expense ratio, #0F172A for the rest).
  Rows in order: Expense ratio · Exit load · Minimum SIP · Riskometer · Benchmark · Fund size · Fund managers.
- DATA BINDING: fill every dd from GET /funds for the fund of the latest answer. Never show "—" when the value exists.
  Only if truly missing: "Not on source page" in #64748B weight 400. Also bind date and groww URL.
  In your report, show me the function in web/app.js that fills the panel.
- "Open source page": height 44, radius 999, bg #0B2A5B, white 14px/500, flex, centred, gap 8,
  external SVG 16px stroke #FFF width 2, href = fund source_url, target _blank.
- Disclaimer box: bg #F6F8FB (GREY — never peach), radius 14, padding 12px 14px, flex column, gap 6.
  Title "Investment disclaimer" 12px/700 #334155. Text 12px/1.5 #475569:
  Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts from public Groww pages (as of 27 Sep 2026) for information only. It is not investment advice or a recommendation to buy or sell any fund. Returns and performance are not shown. Please check the official HDFC factsheet.
- Sanity check: print the expense ratio for all 5 funds. Expected: 1.03%, 0.77%, 1.21%, 0.78%, 0.78% (Small Cap and Balanced Advantage are both genuinely 0.78%).

STOP. Report. Wait for "next".

#####################################################################
PHASE 5 — MOBILE HOME (max-width: 767px)  (copy Docx/design/mobile-home.html)
#####################################################################
Hide the desktop shell entirely on mobile.
Root: width 100%, height 100dvh, bg #F3F7FC, display flex column, position relative, overflow hidden.

5.1 Header: flex, align-items center, justify-content space-between, padding 18px 20px 8px 20px.
  Brand: flex, align-items center, GAP 10 (tile and wordmark must not touch).
  Tile 40×40 radius 12 bg #0B2A5B, "t" Poppins 700 24px white, dot 6×6 #0EA5E9 top 8 right 8.
  Wordmark Poppins 700 23px letter-spacing -0.5px: "tath" #0B2A5B + "ya" #0EA5E9.
  Info button: 44×44 circle bg #FFF border 1px #E3E8EF, info SVG 20px stroke #0F172A width 1.8.

5.2 Main: flex-grow 1, flex column, gap 14, overflow-y auto,
  padding 8px 20px calc(96px + env(safe-area-inset-bottom)) 20px.
  Nothing inside main touches the screen edge. No extra margin/padding on child sections.

5.3 Greeting (flex column, gap 8):
  h1 "Hi there!" Poppins 600 32px, line-height 1.15, letter-spacing -0.6px, #0F172A, margin 0.
  p "Ask me about 5 HDFC mutual funds. Every answer shows its source." 15px/1.5 #475569, margin 0.

5.4 CTA block (flex column, gap 10):
  "Start new chat": height 52, radius 999, bg #0B2A5B, white 15px/500, flex, align-items center,
  justify-content space-between, padding 0 8px 0 22px, no underline.
  Right: 38×38 circle bg #0EA5E9 with arrow-right SVG 18px stroke #FFF width 2.2. (NO ⊕ icon.)
  Facts pill: align-self flex-start (NOT full width), flex, align-items center, gap 8, padding 7px 12px,
  radius 999, bg #E0F2FE, color #075985, 13px/500, shield SVG 15px stroke #075985 width 2,
  text "Facts-only. No investment advice."

5.5 Funds section (flex column, gap 10):
  Header row: flex, space-between, align-items center.
  Left "Funds covered" 15px/700 #0F172A (NOT uppercase). Right "Tap a fund to ask about it" 13px #64748B (NOT blue).
  Grid: display grid, grid-template-columns repeat(2, minmax(0,1fr)), gap 12, margin 0, padding 0.
  Small card: <button>, border none, radius 24, padding 14, height 100, text-align left,
  flex column, justify-content space-between.
   Top: 34×34 white circle, centred icon SVG 17px stroke #0B2A5B width 2.
   Bottom (flex column, gap 2): title 15px/700 #0F172A + subtitle 12px #334155.
   1 bg #DBEEFD · fund-large icon · "Large Cap"      · "Expense ratio: 1.03%"
   2 bg #E3E6FB · fund-flexi icon · "Flexi Cap"      · "Expense ratio: 0.77%"
   3 bg #D5F5EE · fund-elss icon  · "ELSS Tax Saver" · "3-year lock-in"
   4 bg #FCEFCB · fund-small icon · "Small Cap"      · "Exit load: 1% if sold within 1 year"
  Wide card (grid-column span 2): bg #FFF, border 1px #E3E8EF, radius 24, padding 12px 14px,
  flex, align-items center, gap 12.
   Left 34×34 circle bg #F1F5F9, fund-baf SVG 17px stroke #0B2A5B width 2.
   Middle (flex-grow 1, column, gap 2): "Balanced Advantage" 15px/700 + "Hybrid fund · Expense ratio: 0.78%" 12px #334155.
   Right chevron SVG 18px stroke #64748B width 2.
  Tap any card → open mobile chat with that fund selected.

5.6 Disclaimer card: bg #FFF, border 1px #E3E8EF, radius 18, padding 10px 14px, flex, gap 10, align-items flex-start.
  info SVG 16px stroke #64748B width 2, margin-top 2, flex-shrink 0.
  Text 12px/1.45 #475569 margin 0: "Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts only, not investment advice."

5.7 Built by row: flex, align-items center, justify-content center, gap 10, padding-top 2.
  <span 13px #64748B>Built by <span 700 #0F172A>Harshal S</span></span>
  LinkedIn + GitHub 36×36 circles (bg #FFF, border 1px #E3E8EF), SVG 16px (linkedin stroke #0A66C2, github stroke #0F172A), target _blank, rel noopener.

5.8 BOTTOM NAV — ICONS ONLY, NO VISIBLE TEXT
  nav: position absolute, left 50%, bottom calc(22px + env(safe-area-inset-bottom)), transform translateX(-50%),
  flex, gap 6, padding 6, bg #FFF, radius 999, box-shadow 0 8px 24px rgba(11,42,91,0.12).
  4 items: width 50, height 50, radius 50%, flex centred, border none, padding 0, flex-shrink 0,
  aria-label only (Home / Chat / Funds / About). Icon SVG 20px, stroke-width 2.
  Active Home: bg #0B2A5B, icon stroke #FFF. Inactive: bg #F1F5F9, icon stroke #0F172A.
  Icons in order: home, chat, grid, info.
  Chat → mobile chat. Funds → scroll to Funds section. About → same as header info button.

STOP. Report. Wait for "next".

#####################################################################
PHASE 6 — MOBILE CHAT (max-width: 767px)  (copy Docx/design/mobile-chat.html)
#####################################################################
Root: width 100%, height 100dvh, bg #F3F7FC, flex column, overflow hidden. NO bottom nav on this screen.
6.1 Header: flex, space-between, align-items center, padding 18px 16px 10px.
  Back: 44×44 circle bg #FFF border 1px #E3E8EF, back SVG 20px stroke #0F172A width 2 → mobile home.
  Centre wordmark Poppins 700 20px letter-spacing -0.4px ("tath" #0B2A5B + "ya" #0EA5E9).
  New chat: 44×44 circle same style, edit SVG 19px stroke #0F172A width 2.
6.2 Fund chip bar: wrapper padding 2px 16px 8px. Group: flex, gap 4, padding 4, bg #FFF,
  border 1px #E3E8EF, radius 999, overflow-x auto, scrollbar hidden (scrollbar-width none; ::-webkit-scrollbar {display:none}).
  Chips: flex-shrink 0, height 36, padding 0 14, radius 999, border none, 13px/500.
  Active: bg #0B2A5B white (aria-pressed true). Inactive: transparent, #334155.
  Order: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage.
  Active chip follows the fund of the latest question.
6.3 Messages (.messages): flex-grow 1, flex column, gap 12, padding 6px 16px 0, overflow-y auto.
  User bubble: align-self flex-end, max-width 84%, bg #0B2A5B, white 15px/1.4, padding 12px 14px,
  radius 22px 22px 6px 22px, flex column, gap 10.
  Inside the user bubble, keep the small action buttons from Docx/design/mobile-chat.html:
  "Copy" and "Ask again" (height 28, padding 0 10, radius 999, bg #1F4478, white 12px).
  Bot row: flex, gap 8. Avatar 30×30 radius 9 bg #0B2A5B, "t" Poppins 700 18px, dot 5×5 top 5 right 5.
  Answer article: flex-grow 1, bg #FFF, radius 6px 22px 22px 22px, padding 16, flex column, gap 10,
  box-shadow 0 2px 10px rgba(11,42,91,0.05).
   Fund tag: align-self flex-start, 12px/500 #0B2A5B, bg #DBEEFD, radius 999, padding 5px 10px ("HDFC Large Cap Fund · Direct Growth").
   Big number Poppins 600 36px #0B2A5B + label 14px #475569 (gap 8, baseline) — only for single number/percent answers.
   Sentence 15px/1.5 #1E293B.
   Source row: flex, space-between, align-items center, bg #F6F8FB, radius 14, padding 8px 10px:
   link "Source: groww.in" 13px/500 #0369A1 with external SVG 14px + date 12px #64748B.
   Actions row: flex, gap 14: Copy (copy SVG 15px) and Share (share SVG 15px), transparent buttons,
   13px #475569, stroke #475569 width 1.8, gap 5, padding 4px 0.
  Refusal article: bg #FFF4E5, radius 6px 22px 22px 22px, padding 14px 16px, gap 6:
   title "I can't give investment advice." 15px/700 #7C2D12; text 14px/1.5 #7C2D12
   "I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai.";
   link "Learn more" 13px/500 #9A3412 → https://www.mutualfundssahihai.com/en
6.4 Footer: padding 10px 16px calc(18px + env(safe-area-inset-bottom)).
  Pill: flex, gap 8, bg #FFF, radius 999, padding 6px 6px 6px 20px, box-shadow 0 8px 24px rgba(11,42,91,0.10).
  input: flex-grow 1, min-width 0, border none, outline none, transparent, FONT-SIZE 16px (prevents iOS zoom),
  placeholder "Ask a question about a fund…".
  Send: 48×48 circle bg #0B2A5B, arrow-up SVG 20px stroke #FFF width 2.
  Under pill: p margin 8px 0 0, centred, 11px/1.4 #64748B "Mutual fund investments carry market risk. Facts only, not advice."

STOP. Report. Wait for "next".

#####################################################################
PHASE 7 — TABLET (768px–1023px)
#####################################################################
Use the desktop shell (topbar row + workspace) but ALWAYS 2 columns (sidebar 240px + main).
Never show the Source panel on tablet; the answer card's "Source: groww.in" link is enough.
Main HOME padding 28 instead of 40; everything else identical to desktop.

STOP. Report. Wait for "next".

#####################################################################
PHASE 8 — VERIFY (do not skip)
#####################################################################
1. Zoom 100% in Chrome and Edge. DevTools device mode only.
2. 1440×900: compare HOME with Docx/design/desktop-home.html; then ask "What is the expense ratio of HDFC Large Cap Fund?"
   and compare with Docx/design/desktop-chat.html.
3. 390×844: compare with Docx/design/mobile-home.html; then ask the same question plus "Should I buy HDFC Small Cap Fund?"
   and compare with Docx/design/mobile-chat.html.
4. Run .venv\Scripts\python scripts/run_eval.py (must be 64/64) and .venv\Scripts\python scripts/check_layout.py.
5. Report YES/NO for every item:
 Desktop
 [ ] Header is a row above panels; logo overlaps nothing
 [ ] Page never scrolls; no scrollbar on HOME; only messages scroll in CHAT
 [ ] HOME = 2 columns; Source panel appears only after first answer, with real values
 [ ] "Source facts" label present; disclaimer box is GREY
 [ ] Icons present: shield, plus, arrow-up on Send, external on Open source page
 [ ] Textarea has no inner border; Fund select compact
 [ ] Built-by card = one row (avatar → text → icons)
 [ ] "Chat" tab active style; no active fund on HOME
 [ ] Bottom disclaimer has no icon; "Funds covered" inline with chips
 [ ] Computed body font = DM Sans
 Mobile
 [ ] Bottom nav = 4 icon-only 50px circles, Home active navy, no text
 [ ] 20px side padding everywhere; nothing touches the screen edge
 [ ] Logo tile and wordmark have 10px gap
 [ ] Start new chat has 38px sky circle with white arrow
 [ ] Facts pill hugs content, has shield icon
 [ ] "Funds covered" / "Tap a fund…" on one row, normal case, grey hint
 [ ] 5 different fund icons + subtitles; Balanced Advantage has subtitle + chevron
 [ ] "Harshal S" bold
 [ ] Chip bar scrolls horizontally; input 16px; no bottom nav on chat
 [ ] Bottom nav never covers content
 Both
 [ ] Eval 64/64; no console errors
6. List anything you could not match and why.

Start now: inspect the frontend files (Rule 7), then do Phase 1.
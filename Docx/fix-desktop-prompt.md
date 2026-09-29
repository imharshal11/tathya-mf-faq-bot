PROJECT RULES:
- Do NOT start, stop, or kill any server (it runs at http://127.0.0.1:8000). Do not edit .env or corpus files.
- Design files are in Docx/design/ (desktop-home.html, desktop-chat.html).
- Fund data comes ONLY from GET /funds (src/api.py). Questions go to POST /chat with {"question", "scheme"}. Do not change backend logic.
- Commit and push after the fixes. Run .venv\Scripts\python scripts/run_eval.py at the end (must be 64/64).

Fix the remaining desktop mismatches. Source of truth: Docx/design/desktop-home.html and Docx/design/desktop-chat.html.
Copy exact values. Do NOT redesign.

=====================================================================
STEP 0A — BUG: some replies never appear (fix this FIRST)
=====================================================================
Ask these 3 questions at 1440x900 and watch the DevTools Console and Network tab (the /chat response JSON):
  1. "What is the expense ratio of HDFC Large Cap Fund?"  (normal answer)
  2. "Should I buy HDFC Small Cap Fund?"                  (advisory refusal: nothing appears today)
  3. "hello"                                              (greeting: nothing appears today)
Report the exact console error and the JSON returned for 2 and 3.
Likely cause: the render code assumes every reply has a fund, source_url and fetched_date. Guardrail replies have none.
Fix app.js so EVERY reply renders:
  - Read the reply type from debug.guardrail (advisory, returns, pii, clarify, out_of_scope, greeting, thanks, live_data, plan_type) or "not found" text.
  - advisory / returns / pii: warm card (#FFF4E5): title (from "title" if present, bold 15px #7C2D12) + text 14px #7C2D12 + "Learn more" link 13px/500 #9A3412 only if source_url is set.
  - all other guardrail types and "not found": neutral white card (border 1px #E3E8EF), text 15px #1E293B, optional bold title, "Learn more" only if source_url is set.
  - These cards have NO big number and NO source row.
  - They must NOT change the active fund, the chat header, or the Source panel. If there is no fund yet (first question was a refusal/greeting), stay in a 2-column layout with no Source panel, and show "HDFC Mutual Fund FAQ" in the chat header.
  - Wrap rendering in try/catch: if anything fails, show "Something went wrong. Please try again in a moment." instead of nothing.
Re-test all 3 questions and confirm each one shows a card.

=====================================================================
STEP 0 — DEBUG
=====================================================================
Open the app at 1440×900, ask "What is the expense ratio of HDFC Large Cap Fund?", open DevTools Console
and report every error. Then inspect the Source panel and list the class names the JS renders vs the class
names in the CSS. Fix mismatches so JS markup and CSS use the SAME class names.

=====================================================================
FIX 1 — TOPBAR
=====================================================================
.topbar must have exactly 3 direct children: .brand, nav.nav-pill, .actions
.topbar { display:flex; align-items:center; justify-content:space-between; padding:0 4px; }
.topbar .brand   { width:280px; flex-shrink:0; display:flex; align-items:center; gap:10px; }
.topbar .nav-pill{ flex-shrink:0; }
.topbar .actions { width:420px; flex-shrink:0; display:flex; align-items:center; justify-content:flex-end; gap:10px; }
.btn-new-chat, .facts-pill { white-space:nowrap; flex-shrink:0; }
"New chat" must be ONE line.

=====================================================================
FIX 2 — SIDEBAR
=====================================================================
- Fund titles: remove white-space:nowrap / text-overflow:ellipsis / overflow:hidden. Titles wrap
  (e.g. "HDFC Balanced Advantage" / "Fund" on two lines). Keep line-height 1.3.
- Recent questions: dedupe (case-insensitive, trimmed), newest first, max 5 items. Questions still single-line ellipsis.
- CHAT state: fund of the latest answer is active → row bg #EAF2FF, title color #0B2A5B.
- The "HS" avatar uses DM Sans 700 13px (not Poppins).
- GitHub + LinkedIn icons: use exactly
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  LinkedIn stroke #0A66C2: <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>
  GitHub stroke #0F172A: <path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>

=====================================================================
FIX 3 — CHAT MAIN STRUCTURE (most important)
=====================================================================
DOM inside .main in CHAT state must be exactly:
.main
 ├─ .chat-header            (full width)
 ├─ .messages               (flex:1, scrolls)
 │    └─ .messages-inner    (max-width 700, column)
 │         ├─ .msg-user
 │         ├─ .msg-bot  (avatar + article)
 │         └─ ...
 ├─ .composer-wrap          (full width)
 └─ .chat-disclaimer

CSS:
.main { display:flex; flex-direction:column; align-items:stretch; min-height:0; overflow:hidden; }
       /* align-items MUST be stretch in CHAT — not center */

.chat-header { width:100%; height:68px; flex-shrink:0; padding:0 28px; display:flex; align-items:center;
               justify-content:space-between; border-bottom:1px solid #EEF2F6; }
.chat-header .title { display:flex; flex-direction:column; gap:2px; }
.chat-header .title strong { font-size:16px; font-weight:700; color:#0F172A; }
.chat-header .title span { font-size:12px; color:#64748B; }
.verified-badge { display:flex; align-items:center; gap:6px; font-size:12px; font-weight:500; color:#166534;
                  background:#DCFCE7; border-radius:999px; padding:6px 12px; white-space:nowrap; }
.verified-badge::before { content:""; width:7px; height:7px; border-radius:50%; background:#16A34A; }

.messages { flex:1; min-height:0; overflow-y:auto; display:flex; justify-content:center; padding:24px 28px 0; }
.messages-inner { width:100%; max-width:700px; display:flex; flex-direction:column; gap:16px;
                  justify-content:flex-start; align-items:stretch; }

.msg-user { align-self:flex-end; max-width:70%; background:#0B2A5B; color:#FFF; font-size:15px; line-height:1.4;
            padding:12px 16px; border-radius:22px 22px 6px 22px; }

.msg-bot { display:flex; flex-direction:row; gap:10px; align-items:flex-start; }
.msg-bot .avatar { width:32px; height:32px; border-radius:10px; flex-shrink:0; /* + "t" 19px + dot 5px */ }
.msg-bot article { flex:1; background:#F6F9FD; border-radius:6px 22px 22px 22px; padding:18px 20px;
                   display:flex; flex-direction:column; gap:10px; height:auto; }

Order: render messages in chronological order (question first, answer below). Auto-scroll to newest.

.composer-wrap { width:100%; display:flex; justify-content:center; padding:14px 28px 10px; flex-shrink:0; }
.composer-pill { width:100%; max-width:700px; display:flex; align-items:center; gap:8px; background:#FFF;
                 border:1px solid #D5DDE8; border-radius:999px; padding:6px 6px 6px 22px;
                 box-shadow:0 10px 30px rgba(11,42,91,0.08); }
.composer-pill input { flex:1; min-width:0; border:none; outline:none; background:transparent; font-size:15px; }
.chat-disclaimer { margin:0 0 16px; text-align:center; font-size:12px; color:#64748B; flex-shrink:0; }

Desktop answer card has NO fund tag pill. Remove it on ≥1024px (keep it on mobile only).
Desktop card order: big number row → sentence → source row. Source row: flex space-between,
"Source: groww.in" 13px/500 #0369A1 with external-link SVG 14px, date 12px #64748B. No grey box around it on desktop.

=====================================================================
FIX 4 — SOURCE PANEL
=====================================================================
Render this exact structure (class names must match CSS):
<aside class="sources-panel">
  <div class="sp-label">Source facts</div>
  <div class="sp-fund-card">
    <div class="sp-fund-title">HDFC Large Cap Fund (Direct Growth)</div>
    <div class="sp-fund-meta">groww.in · Updated 27 Sep 2026</div>
  </div>
  <dl class="sp-facts">
    <div class="sp-row"><dt>Expense ratio</dt><dd class="sp-accent">1.03%</dd></div>
    <div class="sp-row"><dt>Exit load</dt><dd>…</dd></div>
    <div class="sp-row"><dt>Minimum SIP</dt><dd>…</dd></div>
    <div class="sp-row"><dt>Riskometer</dt><dd>…</dd></div>
    <div class="sp-row"><dt>Benchmark</dt><dd>…</dd></div>
    <div class="sp-row"><dt>Fund size</dt><dd>…</dd></div>
    <div class="sp-row"><dt>Fund managers</dt><dd>…</dd></div>
  </dl>
  <a class="sp-open-btn" href="{source_url}" target="_blank" rel="noopener">[external SVG 16px white] Open source page</a>
  <div class="sp-disclaimer" role="note">
    <span class="sp-disc-title">Investment disclaimer</span>
    <span class="sp-disc-text">Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts from public Groww pages (as of 27 Sep 2026) for information only. It is not investment advice or a recommendation to buy or sell any fund. Returns and performance are not shown. Please check the official HDFC factsheet.</span>
  </div>
</aside>

CSS:
.sources-panel { background:#FFF; border-radius:24px; padding:22px; display:flex; flex-direction:column; gap:14px;
                 min-height:0; overflow-y:auto; overflow-x:hidden; }
.sp-label { font-size:12px; font-weight:500; color:#64748B; }
.sp-fund-card { background:#DBEEFD; border-radius:18px; padding:16px; display:flex; flex-direction:column; gap:4px; }
.sp-fund-title { font-size:16px; font-weight:700; color:#0B2A5B; line-height:1.35; }
.sp-fund-meta { font-size:12px; color:#334155; }
.sp-facts { margin:0; display:flex; flex-direction:column; }
.sp-row { display:flex; justify-content:space-between; gap:12px; padding:12px 0; border-bottom:1px solid #EEF2F6; }
.sp-row dt { font-size:13px; color:#64748B; }
.sp-row dd { margin:0; font-size:13px; font-weight:700; color:#0F172A; text-align:right; }
.sp-row dd.sp-accent { color:#0B2A5B; }
.sp-row dd.sp-missing { font-weight:400; color:#64748B; }       /* text: "Not on source page" */
.sp-open-btn { height:44px; border-radius:999px; background:#0B2A5B; color:#FFF; display:flex; align-items:center;
               justify-content:center; gap:8px; font-size:14px; font-weight:500; text-decoration:none; flex-shrink:0; }
.sp-open-btn:hover { color:#FFF; }
.sp-disclaimer { background:#F6F8FB; border-radius:14px; padding:12px 14px; display:flex; flex-direction:column; gap:6px; }
.sp-disc-title { font-size:12px; font-weight:700; color:#334155; }
.sp-disc-text { font-size:12px; line-height:1.5; color:#475569; }

DATA: fill the fund card and all 7 rows from GET /funds, for the fund of the latest answer (use display_name for the title,
fetched_date for the date, source_url for the button). If the rows were not rendering because of a JS error or a missing
data key, fix it and tell me the cause. Never show "—" when data exists.
Print the expense ratio for all 5 funds from /funds. Expected: 1.03%, 0.77%, 1.21%, 0.78%, 0.78%.

=====================================================================
VERIFY at 1440×900, zoom 100%
=====================================================================
Report YES/NO:
[ ] "Should I buy HDFC Small Cap Fund?" shows a peach card; "hello" shows a white card
[ ] Nav pill centred between brand and actions; "New chat" on one line
[ ] Sidebar fund titles wrap (no "…"); recent questions deduped, max 5
[ ] Active fund highlighted in CHAT
[ ] Chat header full width, badge at far right, divider full width
[ ] Question on top-right, answer BELOW it; avatar LEFT of answer card; card height = content
[ ] Messages start at top of panel
[ ] Composer pill full width (max 700), placeholder fully visible
[ ] No fund tag pill in desktop answer
[ ] Source panel: grey label, blue fund card, 7 rows with values, navy button with icon, grey disclaimer box, 22px padding, nothing overflows
[ ] No console errors
[ ] run_eval.py = 64/64
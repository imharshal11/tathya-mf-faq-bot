// Tathya — Frontend Application Logic
// Phase 1: Basic structure and state management

(() => {
  'use strict';

  // State
  const state = {
    messages: [],
    isChat: false,
    activeFund: null,
    recentQuestions: [],
    typing: false,
    fundsList: []
  };

  // DOM Elements
  const els = {
    app: document.querySelector('.app'),
    workspace: document.querySelector('.workspace'),
    messages: document.querySelector('#messages'),
    mobileMain: document.querySelector('#mobile-main'),
    mobileShell: document.querySelector('.mobile-shell'),
    newChatBtn: document.querySelector('.new-chat-btn'),
    fundItems: document.querySelectorAll('.fund-item'),
    recentList: document.querySelector('#recent-list'),
    composer: null, // will be set after home is rendered
    sendBtn: null,
    fundSelect: null,
    textarea: null
  };

  // Initialize
  async function init() {
    detectViewport();
    bindEvents();
    await loadFundsList();
    renderHome();
  }

  function detectViewport() {
    const isMobile = window.matchMedia('(max-width: 767px)').matches;
    const isTablet = window.matchMedia('(min-width: 768px) and (max-width: 1023px)').matches;
    const isDesktop = window.matchMedia('(min-width: 1024px)').matches;

    document.body.dataset.viewport = isMobile ? 'mobile' : (isTablet ? 'tablet' : 'desktop');
  }

  async function loadFundsList() {
    try {
      const response = await fetch('/funds');
      if (response.ok) {
        state.fundsList = await response.json();
      }
    } catch (e) {
      console.error('Failed to load funds list:', e);
    }
  }

  function bindEvents() {
    // New chat button
    if (els.newChatBtn) {
      els.newChatBtn.addEventListener('click', handleNewChat);
    }

    // Fund items in sidebar
    els.fundItems.forEach(btn => {
      btn.addEventListener('click', () => handleFundSelect(btn.dataset.fund));
    });

    // Window resize
    window.addEventListener('resize', debounce(detectViewport, 100));
  }

  function handleNewChat() {
    state.messages = [];
    state.isChat = false;
    state.activeFund = null;
    els.workspace?.classList.remove('is-chat');

    // Restore main panel to HOME structure (just messages div)
    const mainEl = document.querySelector('.main');
    if (mainEl) {
      mainEl.innerHTML = '<div class="messages" id="messages"></div>';
      els.messages = document.querySelector('#messages');
    }

    // Clear active fund in sidebar
    els.fundItems.forEach(btn => btn.classList.remove('active'));

    renderHome();
  }

  function handleFundSelect(fundId) {
    // Update active state in sidebar
    els.fundItems.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.fund === fundId);
    });
    state.activeFund = fundId;

    // If in chat mode, fetch and populate sources panel for the selected fund
    if (state.isChat) {
      fetchFundFacts(fundId);
    }
  }

  function fetchFundFacts(fundId) {
    const fund = state.fundsList.find(f => f.short_name === fundId || f.id === fundId);
    if (fund) {
      populateSourcesPanel(fund);
    }
  }

  function addRecentQuestion(question) {
    if (!question.trim()) return;
    state.recentQuestions.unshift(question);
    if (state.recentQuestions.length > 10) state.recentQuestions.pop();
    renderRecentQuestions();
  }

  function renderRecentQuestions() {
    if (!els.recentList) return;
    if (state.recentQuestions.length === 0) {
      els.recentList.innerHTML = '';
      // Hide label if no questions
      const label = document.querySelector('.recent-label');
      if (label) label.style.display = 'none';
      return;
    }

    const label = document.querySelector('.recent-label');
    if (label) label.style.display = 'block';

    els.recentList.innerHTML = state.recentQuestions.map(q => `
      <button class="recent-item" type="button" data-question="${escapeHtml(q)}">
        <svg class="icon chat" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 5h14v10H9l-4 4V5z"></path></svg>
        <span>${escapeHtml(q)}</span>
      </button>
    `).join('');

    // Bind click events
    els.recentList.querySelectorAll('.recent-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const question = btn.dataset.question;
        if (question) {
          // Insert into textarea (don't auto-send)
          if (els.textarea) {
            els.textarea.value = question;
            els.textarea.focus();
          }
        }
      });
    });
  }

  function renderHome() {
    // Desktop home
    if (els.messages) {
      els.messages.innerHTML = `
        <div class="empty-state">
          <div class="hero-logo" aria-hidden="true">
            <div class="hero-logo-inner">
              <div class="hero-logo-tile">t<span class="logo-dot" aria-hidden="true"></span></div>
            </div>
          </div>
          <h1 class="empty-heading">Hi, I'm <span class="sky">Tathya</span>. Which fund fact can I find for you?</h1>
          <p class="empty-subtext">I answer only from 5 HDFC fund pages, and I show the source and date for every answer.</p>
          <div class="topic-chips" role="group" aria-label="Suggested topics">
            <button class="topic-chip" type="button" data-topic="expense-ratio">Expense ratio</button>
            <button class="topic-chip" type="button" data-topic="exit-load">Exit load</button>
            <button class="topic-chip" type="button" data-topic="min-sip">Minimum SIP</button>
            <button class="topic-chip" type="button" data-topic="lock-in">Lock-in period</button>
            <button class="topic-chip" type="button" data-topic="riskometer">Riskometer</button>
            <button class="topic-chip" type="button" data-topic="benchmark">Benchmark</button>
            <button class="topic-chip" type="button" data-topic="fund-managers">Fund managers</button>
          </div>
          <div class="composer-card">
            <label for="q-desk" class="sr-only">Ask a question</label>
            <textarea id="q-desk" rows="2" placeholder='Ask a question, for example: "What is the exit load of HDFC Small Cap Fund?"'></textarea>
            <div class="composer-row">
              <div class="fund-field">
                <label for="fund-desk">Fund</label>
                <select id="fund-desk" class="fund-select">
                  <option value="all">All 5 funds</option>
                  <option value="large-cap">HDFC Large Cap Fund</option>
                  <option value="flexi-cap">HDFC Flexi Cap Fund</option>
                  <option value="elss">HDFC ELSS Tax Saver Fund</option>
                  <option value="small-cap">HDFC Small Cap Fund</option>
                  <option value="balanced">HDFC Balanced Advantage Fund</option>
                </select>
              </div>
              <button type="button" class="send-pill">
                <span>Send</span>
                <svg class="icon arrow-up" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5"></path><path d="M6 11l6-6 6 6"></path></svg>
              </button>
            </div>
          </div>
          <div class="funds-covered-row">
            <span class="funds-covered-label">Funds covered</span>
            <span class="fund-chip large-cap">Large Cap</span>
            <span class="fund-chip flexi-cap">Flexi Cap</span>
            <span class="fund-chip elss">ELSS Tax Saver</span>
            <span class="fund-chip small-cap">Small Cap</span>
            <span class="fund-chip balanced">Balanced Advantage</span>
          </div>
          <p class="disclaimer-text">Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts from public Groww pages (as of 27 Sep 2026) for information only. It is not investment advice or a recommendation to buy or sell any fund.</p>
        </div>
      `;

      // Bind composer events
      els.textarea = document.querySelector('#q-desk');
      els.sendBtn = document.querySelector('.send-pill');
      els.fundSelect = document.querySelector('#fund-desk');

      if (els.sendBtn) {
        els.sendBtn.addEventListener('click', handleSend);
      }

      if (els.textarea) {
        els.textarea.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        });
      }

      // Topic chips
      document.querySelectorAll('.topic-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const topic = chip.dataset.topic;
          const templates = {
            'expense-ratio': 'What is the expense ratio of HDFC Large Cap Fund?',
            'exit-load': 'What is the exit load of HDFC Small Cap Fund?',
            'min-sip': 'What is the minimum SIP amount for HDFC Flexi Cap Fund?',
            'lock-in': 'What is the lock-in period for HDFC ELSS Tax Saver Fund?',
            'riskometer': 'What is the riskometer rating of HDFC Balanced Advantage Fund?',
            'benchmark': 'What is the benchmark for HDFC Large Cap Fund?',
            'fund-managers': 'Who manages HDFC Flexi Cap Fund?'
          };
          if (els.textarea && templates[topic]) {
            els.textarea.value = templates[topic];
            els.textarea.focus();
          }
        });
      });
    }

    // Mobile home (Phase 5 will flesh this out)
    if (els.mobileMain) {
      els.mobileMain.innerHTML = `
        <div class="mobile-home">
          <div class="home-greeting">
            <h1 class="hi">Hi there!</h1>
            <p class="ask">Ask me about 5 HDFC mutual funds. Every answer shows its source.</p>
          </div>
          <button class="start-chat-btn" type="button">
            Start new chat
            <span class="icon-circle">
              <svg class="icon arrow-right" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"></path><path d="M13 6l6 6-6 6"></path></svg>
            </span>
          </button>
          <div class="trust-pill">
            <svg class="icon shield" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#075985" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z"></path><path d="M9 12l2 2 4-4"></path></svg>
            <span>Facts-only. No investment advice.</span>
          </div>
          <section class="funds-section">
            <div class="funds-header">
              <span class="funds-title">Funds covered</span>
              <span class="funds-hint">Tap a fund to ask about it</span>
            </div>
            <div class="fund-grid">
              <button class="fund-card large-cap" type="button" data-fund="large-cap">
                <div class="fund-card-icon"><svg class="icon fund-large" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0B2A5B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19h16"></path><path d="M7 15V9"></path><path d="M12 15V5"></path><path d="M17 15v-4"></path></svg></div>
                <div class="fund-card-text">
                  <span class="fund-card-name">Large Cap</span>
                  <span class="fund-card-subtitle">Expense ratio: 1.03%</span>
                </div>
              </button>
              <button class="fund-card flexi-cap" type="button" data-fund="flexi-cap">
                <div class="fund-card-icon"><svg class="icon fund-flexi" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0B2A5B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12a8 8 0 0 1 16 0"></path><path d="M20 12a8 8 0 0 1-16 0"></path><path d="M9 12l2 2 4-4"></path></svg></div>
                <div class="fund-card-text">
                  <span class="fund-card-name">Flexi Cap</span>
                  <span class="fund-card-subtitle">Expense ratio: 0.77%</span>
                </div>
              </button>
              <button class="fund-card elss" type="button" data-fund="elss">
                <div class="fund-card-icon"><svg class="icon fund-elss" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0B2A5B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path></svg></div>
                <div class="fund-card-text">
                  <span class="fund-card-name">ELSS Tax Saver</span>
                  <span class="fund-card-subtitle">3-year lock-in</span>
                </div>
              </button>
              <button class="fund-card small-cap" type="button" data-fund="small-cap">
                <div class="fund-card-icon"><svg class="icon fund-small" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0B2A5B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 17l5-5 4 4 7-7"></path><path d="M15 9h5v5"></path></svg></div>
                <div class="fund-card-text">
                  <span class="fund-card-name">Small Cap</span>
                  <span class="fund-card-subtitle">Exit load: 1% if sold within 1 year</span>
                </div>
              </button>
              <button class="fund-card balanced wide" type="button" data-fund="balanced">
                <div class="fund-card-icon balanced"><svg class="icon fund-baf" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0B2A5B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v16"></path><path d="M5 8h14"></path><path d="M5 8l-2 6h4l-2-6z"></path><path d="M19 8l-2 6h4l-2-6z"></path></svg></div>
                <div class="fund-card-text">
                  <span class="fund-card-name">Balanced Advantage</span>
                  <span class="fund-card-subtitle">Hybrid fund · Expense ratio: 0.78%</span>
                </div>
                <svg class="icon chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"></path></svg>
              </button>
            </div>
          </section>
          <div class="disclaimer-card">
            <svg class="icon info" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v5"></path><path d="M12 8h.01"></path></svg>
            <div class="text">Mutual Fund investments are subject to market risks, read all scheme related documents carefully. Tathya shares facts only, not investment advice.</div>
          </div>
          <div class="credit-links">
            <span>Built by <strong>Harshal S</strong></span>
            <a href="https://www.linkedin.com/in/imharshal11" target="_blank" rel="noopener" aria-label="Harshal S on LinkedIn">
              <svg class="icon linkedin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A66C2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
            </a>
            <a href="https://github.com/imharshal11" target="_blank" rel="noopener" aria-label="Harshal S on GitHub">
              <svg class="icon github" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F172A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"></path></svg>
            </a>
          </div>
        </div>
      `;
    }
  }

  function handleSend() {
    const question = els.textarea?.value?.trim();
    if (!question) return;

    // Determine fund from dropdown or active fund
    let fundSelectValue = 'all';
    if (state.isChat) {
      fundSelectValue = state.activeFund || 'all';
    } else {
      fundSelectValue = els.fundSelect?.value || 'all';
    }
    const scheme = fundSelectValue === 'all' ? null : getSchemeName(fundSelectValue);
    sendQuestion(question, scheme, fundSelectValue);
  }

  async function sendQuestion(question, fund, fundId) {
    // Add to recent questions
    addRecentQuestion(question);

    // Clear composer
    if (els.textarea) els.textarea.value = '';
    const chatInput = document.querySelector('#q-deskchat');
    if (chatInput) chatInput.value = '';

    // If not in chat state yet, transition and render chat view
    if (!state.isChat) {
      state.isChat = true;
      els.workspace?.classList.add('is-chat');
      await renderChatView(question, fund);
      return;
    }

    // Follow-up question: append user message and fetch answer
    if (!els.messages) return;
    const messagesInner = els.messages.querySelector('.messages-inner');
    if (!messagesInner) return;

    // Append user message
    messagesInner.insertAdjacentHTML('beforeend', `
      <div class="msg-user">${escapeHtml(question)}</div>
      <div class="msg-bot">
        <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
        <article class="typing-indicator">Tathya is typing…</article>
      </div>
    `);

    // Auto-scroll to bottom
    els.messages.scrollTop = els.messages.scrollHeight;

    // Determine fund for API call: use active fund (from latest answer or sidebar selection)
    // The active fund is tracked by short_name, find its scheme_name from the funds list
    let apiScheme = fund;
    if (!apiScheme && state.activeFund) {
      const activeFundObj = state.fundsList.find(f => f.short_name === state.activeFund);
      if (activeFundObj) {
        apiScheme = activeFundObj.full_name;
      }
    }

    // Fetch answer
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, scheme: apiScheme })
      });
      const data = await response.json();
      // Pass the question to renderAnswer for fund context logic
      data.question = question;
      renderAnswer(data);
    } catch (e) {
      console.error('API error:', e);
      const typingEl = els.messages.querySelector('.typing-indicator');
      if (typingEl) {
        typingEl.outerHTML = `
          <div class="msg-bot">
            <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
            <article class="info-card">
              <p class="answer-text">Something went wrong. Please try again in a moment.</p>
            </article>
          </div>
        `;
      }
    }
  }

  async function renderChatView(question, scheme) {
    const mainEl = document.querySelector('.main');
    if (!mainEl) return;

    // Add chat main class
    mainEl.classList.add('is-chat-main');

    // Determine fund display name from scheme
    const schemeToDisplay = {
      'HDFC Large Cap Fund - Direct Growth': 'HDFC Large Cap Fund',
      'HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth': 'HDFC Flexi Cap Fund',
      'HDFC ELSS Tax Saver Fund - Direct Plan Growth': 'HDFC ELSS Tax Saver Fund',
      'HDFC Small Cap Fund - Direct Growth': 'HDFC Small Cap Fund',
      'HDFC Balanced Advantage Fund - Direct Growth': 'HDFC Balanced Advantage Fund'
    };
    const fundDisplay = scheme ? schemeToDisplay[scheme] : 'HDFC Mutual Fund FAQ';

    // Use active fund for header if available, otherwise show default
    const headerTitle = state.activeFund ? fundDisplay : 'HDFC Mutual Fund FAQ';
    const headerSubtitle = state.activeFund ? 'Direct Plan · Growth' : 'Ask about 5 HDFC funds';

    // Render full chat structure matching design
    mainEl.innerHTML = `
      <header class="chat-header">
        <div class="title">
          <strong>${escapeHtml(headerTitle)}</strong>
          <span>${escapeHtml(headerSubtitle)}</span>
        </div>
        <span class="verified-badge"><span aria-hidden="true"></span>Verified sources</span>
      </header>
      <div class="messages" id="messages" role="log" aria-live="polite" aria-label="Conversation">
        <div class="messages-inner">
          <div class="msg-user">${escapeHtml(question)}</div>
          <div class="msg-bot">
            <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
            <article class="typing-indicator">Tathya is typing…</article>
          </div>
        </div>
      </div>
      <div class="composer-wrap">
        <form class="composer-pill" id="chat-composer-form" autocomplete="off">
          <label for="q-deskchat" class="sr-only">Ask a follow-up</label>
          <input id="q-deskchat" type="text" placeholder="Ask a question about a fund…" aria-label="Ask a question about a fund" required>
          <button type="submit" class="composer-send" aria-label="Send">
            <svg class="icon arrow-up" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5"></path><path d="M6 11l6-6 6 6"></path></svg>
          </button>
        </form>
      </div>
      <p class="chat-disclaimer">Mutual fund investments carry market risk. Facts only, not advice.</p>
    `;

    // Update messages reference
    els.messages = document.querySelector('#messages');

    // Bind chat composer events
    const chatForm = document.querySelector('#chat-composer-form');
    const chatInput = document.querySelector('#q-deskchat');
    if (chatForm && chatInput) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const q = chatInput.value.trim();
        if (q) {
          chatInput.value = '';
          const fundSelectValue = state.activeFund || 'all';
          const followUpScheme = fundSelectValue === 'all' ? null : getSchemeName(fundSelectValue);
          sendQuestion(q, followUpScheme, fundSelectValue);
        }
      });
    }

    // If there's an active fund, fetch and populate sources panel
    if (state.activeFund) {
      fetchFundFacts(state.activeFund);
    }

    // Make actual API call
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, scheme })
      });
      const data = await response.json();
      data.question = question;
      renderAnswer(data);
    } catch (e) {
      console.error('API error:', e);
      const typingEl = els.messages?.querySelector('.typing-indicator');
      if (typingEl) {
        typingEl.outerHTML = `
          <div class="msg-bot">
            <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
            <article class="info-card">
              <p class="answer-text">Something went wrong. Please try again in a moment.</p>
            </article>
          </div>
        `;
      }
    }
  }

  function renderAnswer(data) {
    if (!els.messages) return;

    try {
      const guardrail = data.debug?.guardrail;
      const isGuardrail = ['advisory', 'returns', 'pii', 'clarify', 'out_of_scope', 'greeting', 'thanks', 'live_data', 'plan_type'].includes(guardrail);
      const isNotFound = data.answer?.includes('Not in the knowledge base') || data.answer?.includes('not found');
      const isRefusal = guardrail === 'advisory' || guardrail === 'returns' || guardrail === 'pii';
      const isNeutral = guardrail === 'greeting' || guardrail === 'thanks' || guardrail === 'clarify' || guardrail === 'live_data' || guardrail === 'plan_type' || guardrail === 'out_of_scope' || isNotFound;

      // Determine fund display name
      const fundNames = {
        'large-cap': 'HDFC Large Cap Fund',
        'flexi-cap': 'HDFC Flexi Cap Fund',
        'elss': 'HDFC ELSS Tax Saver Fund',
        'small-cap': 'HDFC Small Cap Fund',
        'balanced': 'HDFC Balanced Advantage Fund'
      };
      const fundDisplay = fundNames[data.fund] || data.fund_display || 'HDFC Large Cap Fund';

      // Format date as "27 Sep 2026"
      const fetchDate = data.fetched_date || '27 Sep 2026';

      // Build answer article
      let articleHtml = '';

      if (isGuardrail || isNotFound) {
        const title = data.title || '';
        const hasSourceUrl = data.source_url && data.source_url.trim() !== '';

        if (isRefusal) {
          // Refusal card (peach #FFF4E5)
          articleHtml = `
            <article class="refusal-card" role="alert">
              <p class="answer-title">${escapeHtml(title || "I can't give investment advice.")}</p>
              <p class="answer-text">${escapeHtml(data.answer)}</p>
              ${hasSourceUrl ? `
                <a class="learn-more" href="${escapeHtml(data.source_url)}" target="_blank" rel="noopener">Learn more</a>
              ` : ''}
            </article>
          `;
        } else {
          // Info card (same shape/bg as answer-card)
          articleHtml = `
            <article class="info-card" role="status">
              <p class="answer-text">${escapeHtml(data.answer)}</p>
              ${hasSourceUrl ? `
                <a class="learn-more" href="${escapeHtml(data.source_url)}" target="_blank" rel="noopener">Learn more</a>
              ` : ''}
            </article>
          `;
        }
      } else {
        // Normal fund answer
        const isSingleNumber = data.title && (data.answer.includes('%') || data.answer.match(/^[\d.]+%?$/));

        // Big number row for single number/percent answers
        let bigNumberHtml = '';
        if (isSingleNumber && data.title) {
          const valueMatch = data.answer.match(/([\d.]+%)/);
          const value = valueMatch ? valueMatch[1] : data.title;
          const label = data.title.toLowerCase().replace('ratio', 'ratio');
          bigNumberHtml = `
            <div class="answer-number-row">
              <span class="answer-number">${escapeHtml(value)}</span>
              <span class="answer-label">${escapeHtml(label)}</span>
            </div>
          `;
        }

        // Fund manager chips if applicable
        let managerChipsHtml = '';
        if (data.answer.includes('managed by') || data.answer.includes('manages')) {
          managerChipsHtml = `
            <div class="fund-manager-chips">
              <span class="fund-manager-chip">
                <span class="name">Rahul Baijal</span>
                <span class="since">Since Jul 2022</span>
              </span>
              <span class="fund-manager-chip">
                <span class="name">Dhruv Muchhal</span>
                <span class="since">Since Jun 2023</span>
              </span>
            </div>
          `;
        }

        articleHtml = `
          <article class="answer-card">
            ${bigNumberHtml}
            <p class="answer-text">${escapeHtml(data.answer)}</p>
            ${managerChipsHtml}
            <div class="answer-source-row">
              <a class="source-link-row" href="${escapeHtml(data.source_url || '#')}" target="_blank" rel="noopener">
                <svg class="icon external" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0369A1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6"></path><path d="M20 4l-9 9"></path><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"></path></svg>
                <span>Source: groww.in</span>
              </a>
              <span class="source-date">Updated ${escapeHtml(fetchDate)}</span>
            </div>
          </article>
        `;

        // Populate sources panel for normal fund answers
        const fundFromAnswer = findFundBySourceUrl(data.source_url);
        if (fundFromAnswer) {
          state.activeFund = fundFromAnswer.short_name;
          populateSourcesPanel(fundFromAnswer);
        } else {
          populateSourcesPanel(data, fundDisplay, fetchDate);
        }
      }

      // Replace typing indicator with bot response
      const typingEl = els.messages.querySelector('.typing-indicator');
      if (typingEl) {
        const msgBotEl = typingEl.closest('.msg-bot');
        if (msgBotEl) {
          msgBotEl.innerHTML = `
            <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
            ${articleHtml}
          `;
        } else {
          // Fallback for initial render
          typingEl.outerHTML = `
            <div class="msg-bot">
              <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
              ${articleHtml}
            </div>
          `;
        }
      }
      // Auto-scroll to newest
      els.messages.scrollTop = els.messages.scrollHeight;
    } catch (e) {
      console.error('Render error:', e);
      const typingEl = els.messages.querySelector('.typing-indicator');
      if (typingEl) {
        typingEl.outerHTML = `
          <div class="msg-bot">
            <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
            <article class="info-card">
              <p class="answer-text">Something went wrong. Please try again in a moment.</p>
            </article>
          </div>
        `;
      }
    }
  }

  function populateSourcesPanel(fund) {
    const fundCardEl = document.getElementById('source-fund-card');
    const factsEl = document.getElementById('source-facts');
    const openBtnEl = document.getElementById('open-source-btn');

    if (!fund) return;

    if (fundCardEl) {
      const fetchDate = fund.fetched_date ? formatDate(fund.fetched_date) : 'Not on source page';
      fundCardEl.innerHTML = `
        <div class="sp-fund-title">${escapeHtml(fund.display_name)} (Direct Growth)</div>
        <div class="sp-fund-meta">groww.in · Updated ${escapeHtml(fetchDate)}</div>
      `;
    }

    if (factsEl) {
      const managers = (fund.fund_managers || []).map(m => m.name).join(', ') || 'Not on source page';
      const factRows = [
        { label: 'Expense ratio', value: fund.expense_ratio || 'Not on source page' },
        { label: 'Exit load', value: fund.exit_load || 'Not on source page' },
        { label: 'Minimum SIP', value: fund.min_sip ? `₹${fund.min_sip}` : 'Not on source page' },
        { label: 'Riskometer', value: fund.riskometer || 'Not on source page' },
        { label: 'Benchmark', value: fund.benchmark || 'Not on source page' },
        { label: 'Fund size', value: fund.aum ? `₹${fund.aum} crore` : 'Not on source page' },
        { label: 'Fund managers', value: managers }
      ];

      factsEl.innerHTML = factRows.map(row => `
        <div class="sp-row">
          <dt>${escapeHtml(row.label)}</dt>
          <dd>${escapeHtml(row.value)}</dd>
        </div>
      `).join('');
    }

    if (openBtnEl && fund.source_url) {
      openBtnEl.href = fund.source_url;
    }
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    return date.toLocaleDateString('en-GB', options).replace(/ /g, ' ');
  }

  function findFundBySourceUrl(sourceUrl) {
    if (!sourceUrl) return null;
    return state.fundsList.find(f => f.source_url === sourceUrl);
  }

  function getSchemeName(shortName) {
    const fund = state.fundsList.find(f => f.short_name === shortName);
    return fund ? fund.full_name : null;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function debounce(fn, delay) {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn.apply(null, args), delay);
    };
  }

  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
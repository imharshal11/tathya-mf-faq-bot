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
    fundsList: [],
    mobileView: 'home'
  };

  // Mobile home fact line formats (values come from GET /funds)
  const MOBILE_FUND_SHORT = {
    'large-cap': 'Large Cap',
    'flexi-cap': 'Flexi Cap',
    'elss': 'ELSS',
    'small-cap': 'Small Cap',
    'balanced': 'Balanced Advantage'
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

    // Mobile home: fund tiles open the mobile chat with that fund selected
    document.querySelectorAll('.fund-card').forEach(card => {
      card.addEventListener('click', () => openMobileChat(card.dataset.fund));
    });

    // Mobile home: "Start new chat"
    const mobileStartBtn = document.querySelector('.start-chat-btn');
    if (mobileStartBtn) {
      mobileStartBtn.addEventListener('click', startMobileChat);
    }

    // Mobile bottom nav (Home / Chat / Funds / About)
    document.querySelectorAll('.mobile-nav-item').forEach(item => {
      item.addEventListener('click', () => handleMobileNav(item.dataset.view));
    });

    // Header info button — same action as the "About" nav item
    const mobileInfoBtn = document.querySelector('.mobile-info-btn');
    if (mobileInfoBtn) {
      mobileInfoBtn.addEventListener('click', handleMobileAbout);
    }

    // Mobile chat: back / new chat / fund chips / composer
    const chatBackBtn = document.querySelector('.chat-back-btn');
    if (chatBackBtn) {
      chatBackBtn.addEventListener('click', () => setMobileView('home'));
    }

    const chatNewBtn = document.querySelector('.chat-new-btn');
    if (chatNewBtn) {
      chatNewBtn.addEventListener('click', handleMobileNewChat);
    }

    document.querySelectorAll('.fund-chip-bar .fund-chip').forEach(chip => {
      chip.addEventListener('click', () => toggleFundSelection(chip.dataset.fund));
    });

    const mobileChatForm = document.querySelector('#mobile-chat-form');
    const mobileChatInput = document.querySelector('#q-mobile');
    if (mobileChatForm && mobileChatInput) {
      mobileChatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const q = mobileChatInput.value.trim();
        if (!q) return;
        const fundSelectValue = state.activeFund || 'all';
        const scheme = fundSelectValue === 'all' ? null : getSchemeName(fundSelectValue);
        sendQuestion(q, scheme, fundSelectValue);
      });
    }

    // Copy / Share / Ask again — one delegated listener serves both layouts
    document.addEventListener('click', handleChatActionClick);

    // Window resize
    window.addEventListener('resize', debounce(detectViewport, 100));
  }

  // ---------- Mobile (Phase 5) ----------

  function mobileHomeEl() {
    return els.mobileMain ? els.mobileMain.querySelector('.mobile-home') : null;
  }

  function mobileChatEl() {
    return els.mobileMain ? els.mobileMain.querySelector('.mobile-chat') : null;
  }

  function isMobileChatOpen() {
    const chat = mobileChatEl();
    return !!(chat && !chat.hidden);
  }

  function mobileMessagesEl() {
    const chat = mobileChatEl();
    return chat ? chat.querySelector('.messages') : null;
  }

  // One render path: the same message container the desktop logic writes to
  function getActiveMessagesEl() {
    return isMobileChatOpen() ? mobileMessagesEl() : els.messages;
  }

  function setMobileView(view) {
    state.mobileView = view;

    const home = mobileHomeEl();
    const chat = mobileChatEl();
    if (home) home.style.display = view === 'home' ? '' : 'none';
    if (chat) chat.hidden = view !== 'chat';

    document.querySelectorAll('.mobile-nav-item').forEach(item => {
      const active = item.dataset.view === view;
      item.classList.toggle('active', active);
      if (active) {
        item.setAttribute('aria-current', 'page');
      } else {
        item.removeAttribute('aria-current');
      }
    });

    if (els.mobileMain) els.mobileMain.scrollTop = 0;
  }

  function openMobileChat(fundId) {
    if (fundId) state.activeFund = fundId;
    const chat = mobileChatEl();
    if (chat) chat.dataset.fund = state.activeFund || 'all';
    syncFundSelectionUI();
    setMobileView('chat');
  }

  function startMobileChat() {
    handleMobileNewChat();
  }

  // Mobile "New chat": clear the conversation, stay on the mobile chat screen
  function handleMobileNewChat() {
    handleNewChat();

    const chat = mobileChatEl();
    if (chat) {
      const inner = chat.querySelector('.messages-inner');
      if (inner) inner.innerHTML = '';
      const input = chat.querySelector('#q-mobile');
      if (input) input.value = '';
    }

    syncFundSelectionUI();
    setMobileView('chat');
  }

  function handleMobileNav(view) {
    switch (view) {
      case 'home':
        setMobileView('home');
        break;
      case 'chat':
        openMobileChat(state.activeFund);
        break;
      case 'funds':
        setMobileView('home');
        document.querySelector('.funds-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        break;
      case 'about':
        handleMobileAbout();
        break;
      default:
        break;
    }
  }

  function handleMobileAbout() {
    const target = document.querySelector('.credit-links') || document.querySelector('.disclaimer-card');
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function mobileFundFact(fund) {
    if (!fund) return '';
    switch (fund.short_name) {
      case 'Large Cap':
      case 'Flexi Cap':
        return fund.expense_ratio ? `Expense ratio: ${fund.expense_ratio}` : '';
      case 'ELSS':
        if (fund.lock_in) return `${fund.lock_in.replace(/\s+years?$/i, '-year')} lock-in`;
        return fund.expense_ratio ? `Expense ratio: ${fund.expense_ratio}` : '';
      case 'Small Cap':
        return fund.exit_load ? `Exit load: ${fund.exit_load}` : '';
      case 'Balanced Advantage':
        return fund.expense_ratio ? `Hybrid fund · Expense ratio: ${fund.expense_ratio}` : 'Hybrid fund';
      default:
        return '';
    }
  }

  function renderMobileFundFacts() {
    if (!els.mobileMain) return;
    els.mobileMain.querySelectorAll('.fund-card').forEach(card => {
      const shortName = MOBILE_FUND_SHORT[card.dataset.fund];
      const fund = shortName ? state.fundsList.find(f => f.short_name === shortName) : null;
      const fact = mobileFundFact(fund);
      const subtitle = card.querySelector('.fund-card-subtitle');
      if (fact && subtitle) subtitle.textContent = fact;
    });
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
    // If same fund is already selected, unselect (back to "All 5 funds")
    if (normalizeFundId(state.activeFund) === normalizeFundId(fundId)) {
      state.activeFund = null;
    } else {
      state.activeFund = fundId;
    }
    syncFundSelectionUI();

    // If in chat mode, fetch and populate sources panel for the selected fund
    if (state.isChat && state.activeFund) {
      fetchFundFacts(state.activeFund);
    }
  }

  function fetchFundFacts(fundId) {
    const fundIdNorm = normalizeFundId(fundId);
    const fund = state.fundsList.find(f => normalizeFundId(f.short_name) === fundIdNorm);
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
            <button class="fund-chip large-cap" type="button" data-fund="large-cap">Large Cap</button>
            <button class="fund-chip flexi-cap" type="button" data-fund="flexi-cap">Flexi Cap</button>
            <button class="fund-chip elss" type="button" data-fund="elss">ELSS Tax Saver</button>
            <button class="fund-chip small-cap" type="button" data-fund="small-cap">Small Cap</button>
            <button class="fund-chip balanced" type="button" data-fund="balanced">Balanced Advantage</button>
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

      // Fund chips (pills) - click to select/unselect fund
      els.app.querySelectorAll('.fund-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const fundId = chip.dataset.fund;
          toggleFundSelection(fundId);
        });
      });

      // Topic chips - build question from selected fund
      document.querySelectorAll('.topic-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const topic = chip.dataset.topic;
          insertTopicQuestion(topic);
        });
      });

      // Sync UI with current activeFund state
      syncFundSelectionUI();
    }

    // Mobile home markup is static in index.html; refresh fact lines from GET /funds
    renderMobileFundFacts();
  }

  // Fund selection helpers
  // Funds are addressed both by data-fund id ("flexi-cap") and by the API
  // short_name ("Flexi Cap") — normalise so every lookup accepts either.
  const FUND_ID_ALIASES = {
    'large-cap': 'large-cap', 'Large Cap': 'large-cap',
    'flexi-cap': 'flexi-cap', 'Flexi Cap': 'flexi-cap',
    'elss': 'elss', 'ELSS': 'elss',
    'small-cap': 'small-cap', 'Small Cap': 'small-cap',
    'balanced': 'balanced', 'Balanced Advantage': 'balanced'
  };

  function normalizeFundId(value) {
    if (!value) return null;
    return FUND_ID_ALIASES[value] || value;
  }

  function getFundDisplayName(shortName) {
    const names = {
      'large-cap': 'HDFC Large Cap Fund',
      'flexi-cap': 'HDFC Flexi Cap Fund',
      'elss': 'HDFC ELSS Tax Saver Fund',
      'small-cap': 'HDFC Small Cap Fund',
      'balanced': 'HDFC Balanced Advantage Fund'
    };
    return names[normalizeFundId(shortName)] || '';
  }

  function toggleFundSelection(fundId) {
    // If same fund is already selected, unselect (back to "All 5 funds")
    if (normalizeFundId(state.activeFund) === normalizeFundId(fundId)) {
      state.activeFund = null;
    } else {
      state.activeFund = fundId;
    }
    syncFundSelectionUI();
  }

  function syncFundSelectionUI() {
    const activeId = normalizeFundId(state.activeFund);

    // Sync fund pills (desktop home)
    document.querySelectorAll('.app .fund-chip').forEach(chip => {
      chip.classList.toggle('active', normalizeFundId(chip.dataset.fund) === activeId);
    });

    // Sync dropdown (home)
    if (els.fundSelect) {
      els.fundSelect.value = activeId || 'all';
    }

    // Sync sidebar fund items
    els.fundItems.forEach(btn => {
      btn.classList.toggle('active', normalizeFundId(btn.dataset.fund) === activeId);
    });

    syncMobileFundChips();
  }

  // Mobile chat fund chip bar (aria-pressed follows the active fund)
  function syncMobileFundChips() {
    const activeId = normalizeFundId(state.activeFund);
    document.querySelectorAll('.fund-chip-bar .fund-chip').forEach(chip => {
      const on = normalizeFundId(chip.dataset.fund) === activeId;
      chip.classList.toggle('active', on);
      chip.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  // ---------- Copy / Share / Ask again (mobile chat actions) ----------

  let toastTimer = null;

  function showToast(message) {
    let el = document.querySelector('.app-toast');
    if (!el) {
      el = document.createElement('div');
      el.className = 'app-toast';
      el.setAttribute('role', 'status');
      document.body.appendChild(el);
    }
    el.textContent = message;
    void el.offsetWidth;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      el.classList.remove('show');
      const node = el;
      setTimeout(() => node.remove(), 260);
    }, 1600);
  }

  function legacyCopy(text, done) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '0';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
    } catch (e) {
      // clipboard unavailable — still confirm the attempt
    }
    ta.remove();
    done();
  }

  function copyText(text) {
    const done = () => showToast('Copied');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(() => legacyCopy(text, done));
    } else {
      legacyCopy(text, done);
    }
  }

  function shareText(text) {
    if (typeof navigator.share === 'function') {
      navigator.share({ title: 'Tathya', text }).catch(() => copyText(text));
    } else {
      copyText(text);
    }
  }

  function handleChatActionClick(e) {
    const btn = e.target.closest ? e.target.closest('.msg-user-action, .answer-action') : null;
    if (!btn) return;

    const action = btn.dataset.action;

    if (action === 'copy') {
      const userBubble = btn.closest('.msg-user');
      const card = btn.closest('.answer-card, .refusal-card, .info-card');
      const source = userBubble
        ? userBubble.querySelector('.msg-user-text')
        : (card ? card.querySelector('.answer-text') : null);
      const text = source ? source.textContent : '';
      if (text) copyText(text);
      return;
    }

    if (action === 'share') {
      const card = btn.closest('.answer-card, .refusal-card, .info-card');
      const text = card ? (card.querySelector('.answer-text')?.textContent || '') : '';
      if (text) shareText(text);
      return;
    }

    if (action === 'again') {
      const bubble = btn.closest('.msg-user');
      const question = bubble ? (bubble.querySelector('.msg-user-text')?.textContent || '').trim() : '';
      if (!question) return;
      const fundSelectValue = state.activeFund || 'all';
      const scheme = fundSelectValue === 'all' ? null : getSchemeName(fundSelectValue);
      sendQuestion(question, scheme, fundSelectValue);
    }
  }

  function insertTopicQuestion(topic) {
    if (!els.textarea) return;

    const fundDisplayName = state.activeFund ? getFundDisplayName(state.activeFund) : '';
    const templates = {
      'expense-ratio': fundDisplayName ? `What is the expense ratio of ${fundDisplayName}?` : 'What is the expense ratio of ',
      'exit-load': fundDisplayName ? `What is the exit load of ${fundDisplayName}?` : 'What is the exit load of ',
      'min-sip': fundDisplayName ? `What is the minimum SIP amount for ${fundDisplayName}?` : 'What is the minimum SIP amount for ',
      'lock-in': fundDisplayName ? `What is the lock-in period for ${fundDisplayName}?` : 'What is the lock-in period for ',
      'riskometer': fundDisplayName ? `What is the riskometer rating of ${fundDisplayName}?` : 'What is the riskometer rating of ',
      'benchmark': fundDisplayName ? `What is the benchmark for ${fundDisplayName}?` : 'What is the benchmark for ',
      'fund-managers': fundDisplayName ? `Who manages ${fundDisplayName}?` : 'Who manages '
    };

    const question = templates[topic];
    if (question) {
      els.textarea.value = question;
      els.textarea.focus();
      // If no fund selected, position cursor at end so user can type fund name
      if (!fundDisplayName) {
        els.textarea.setSelectionRange(question.length, question.length);
      }
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

  function userBubbleHtml(question) {
    return `<div class="msg-user"><span class="msg-user-text">${escapeHtml(question)}</span><div class="msg-user-actions"><button class="msg-user-action" type="button" data-action="copy">Copy</button><button class="msg-user-action" type="button" data-action="again">Ask again</button></div></div>`;
  }

  function typingRowHtml() {
    return `
      <div class="msg-bot">
        <div class="avatar">t<span class="dot" aria-hidden="true"></span></div>
        <article class="typing-indicator">Tathya is typing…</article>
      </div>
    `;
  }

  function clearComposers() {
    if (els.textarea) els.textarea.value = '';
    ['q-deskchat', 'q-mobile'].forEach(id => {
      const field = document.getElementById(id);
      if (field) field.value = '';
    });
  }

  // POST /chat — same payload as desktop, with a 60s startup timeout
  async function fetchChatAnswer(question, scheme) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 60000);
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, scheme }),
        signal: controller.signal
      });
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  function renderBotError(message, messagesEl) {
    const target = messagesEl || getActiveMessagesEl();
    if (!target) return;
    const typingEl = target.querySelector('.typing-indicator');
    if (!typingEl) return;
    typingEl.outerHTML = `
      <article class="info-card" role="alert">
        <p class="answer-text">${escapeHtml(message)}</p>
      </article>
    `;
    target.scrollTop = target.scrollHeight;
  }

  async function requestAnswer(question, apiScheme, messagesEl) {
    try {
      const data = await fetchChatAnswer(question, apiScheme);
      // Pass the question to renderAnswer for fund context logic
      data.question = question;
      renderAnswer(data, messagesEl);
    } catch (e) {
      if (e && e.name === 'AbortError') {
        renderBotError('The app is starting up. This can take up to a minute. Please try again.', messagesEl);
        return;
      }
      console.error('API error:', e);
      renderBotError('Something went wrong. Please try again in a moment.', messagesEl);
    }
  }

  async function sendQuestion(question, fund, fundId) {
    // Add to recent questions
    addRecentQuestion(question);

    // Clear composer
    clearComposers();

    const mobileOpen = isMobileChatOpen();
    const messagesEl = mobileOpen ? mobileMessagesEl() : els.messages;

    // If not in chat state yet, transition and render chat view
    if (!mobileOpen && !state.isChat) {
      state.isChat = true;
      els.workspace?.classList.add('is-chat');
      await renderChatView(question, fund);
      return;
    }

    // Follow-up question: append user message and fetch answer
    if (!messagesEl) return;
    let messagesInner = messagesEl.querySelector('.messages-inner');
    if (!messagesInner) {
      messagesEl.innerHTML = '<div class="messages-inner"></div>';
      messagesInner = messagesEl.querySelector('.messages-inner');
    }

    // Append user message
    messagesInner.insertAdjacentHTML('beforeend', `
      ${userBubbleHtml(question)}
      ${typingRowHtml()}
    `);

    // Auto-scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;

    // Determine fund for API call: use active fund (from latest answer or sidebar selection)
    // The active fund is tracked by short_name, find its scheme_name from the funds list
    let apiScheme = fund;
    if (!apiScheme && state.activeFund) {
      const activeFundId = normalizeFundId(state.activeFund);
      const activeFundObj = state.fundsList.find(f => normalizeFundId(f.short_name) === activeFundId);
      if (activeFundObj) {
        apiScheme = activeFundObj.scheme_name;
      }
    }

    // Fetch answer
    await requestAnswer(question, apiScheme, messagesEl);
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
          ${userBubbleHtml(question)}
          ${typingRowHtml()}
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
    await requestAnswer(question, scheme, els.messages);
  }

  function answerFactLabel(data) {
    const q = (data.question || '').toLowerCase();
    if (q.includes('expense ratio')) return 'expense ratio';
    if (q.includes('exit load')) return 'exit load';
    if (q.includes('minimum sip') || q.includes('min sip')) return 'minimum SIP';
    if (q.includes('lock-in') || q.includes('lock in')) return 'lock-in period';
    if (q.includes('riskometer')) return 'riskometer';
    if (q.includes('benchmark')) return 'benchmark';
    if (q.includes('fund size') || q.includes('aum')) return 'fund size';
    return '';
  }

  // Fund-manager answers never carry a big number
  function isManagerQuestion(data) {
    const q = (data.question || '').toLowerCase();
    return q.includes('manage') || q.includes('manager') || q.includes('who runs');
  }

  // ONE detection function shared by mobile and desktop chat:
  // a factual answer gets a big number only when it has exactly one key
  // figure — a % value, a ₹ amount or "X years" — and a known topic label.
  const ANSWER_FIGURE_RE = /(₹\s?[\d][\d,]*(?:\.\d+)?|\b\d+(?:\.\d+)?\s*years?\b|\b\d+(?:\.\d+)?%)/gi;

  function answerBigFigure(data) {
    if (isManagerQuestion(data)) return null;
    const label = answerFactLabel(data);
    if (!label) return null;
    const answer = data.answer || '';
    const figures = answer.match(ANSWER_FIGURE_RE);
    if (!figures || figures.length !== 1) return null;
    return { value: figures[0].trim().replace(/\s+/g, ' '), label };
  }

  function bigNumberRowHtml(data) {
    const figure = answerBigFigure(data);
    if (!figure) return '';
    return `
            <div class="answer-number-row">
              <span class="answer-number">${escapeHtml(figure.value)}</span>
              <span class="answer-label">${escapeHtml(figure.label)}</span>
            </div>
          `;
  }

  function renderAnswer(data, messagesEl) {
    messagesEl = messagesEl || getActiveMessagesEl();
    if (!messagesEl) return;

    try {
      const guardrail = data.debug?.guardrail;
      const isGuardrail = ['advisory', 'returns', 'pii', 'clarify', 'out_of_scope', 'greeting', 'thanks', 'live_data', 'plan_type'].includes(guardrail);
      const isNotFound = data.answer?.includes('Not in the knowledge base') || data.answer?.includes('not found') || data.answer?.includes('I don\'t have that information yet');
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
      const fundFromAnswer = findFundBySourceUrl(data.source_url);

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
              ${title ? `<p class="answer-title">${escapeHtml(title)}</p>` : ''}
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
              ${title ? `<p class="answer-title">${escapeHtml(title)}</p>` : ''}
              <p class="answer-text">${escapeHtml(data.answer)}</p>
              ${hasSourceUrl ? `
                <a class="learn-more" href="${escapeHtml(data.source_url)}" target="_blank" rel="noopener">Learn more</a>
              ` : ''}
            </article>
          `;
        }
      } else {
        // Normal fund answer
        // Fund tag (mobile chat) — "<fund full name> · Direct Growth"
        const tagShortName = fundFromAnswer ? fundFromAnswer.short_name : state.activeFund;
        const tagFundName = tagShortName ? getFundDisplayName(tagShortName) : '';
        const fundTagHtml = tagFundName
          ? `<span class="answer-fund-tag">${escapeHtml(tagFundName)} · Direct Growth</span>`
          : '';

        // Big number row — ONE detection function shared by mobile and desktop
        const bigNumberHtml = bigNumberRowHtml(data);

        // Fund manager chips - ONLY for manager-related questions
        let managerChipsHtml = '';
        if (isManagerQuestion(data) && fundFromAnswer && fundFromAnswer.fund_managers && fundFromAnswer.fund_managers.length > 0) {
          const chips = fundFromAnswer.fund_managers.map(m => `
              <span class="fund-manager-chip">
                <span class="name">${escapeHtml(m.name)}</span>
                <span class="since">${escapeHtml('Since ' + m.since)}</span>
              </span>
            `).join('');
          managerChipsHtml = `<div class="fund-manager-chips">${chips}</div>`;
        }

        articleHtml = `
          <article class="answer-card">
            ${fundTagHtml}
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
            <div class="answer-actions">
              <button class="answer-action" type="button" data-action="copy">
                <svg class="icon copy" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"></rect><path d="M5 15V6a1 1 0 0 1 1-1h9"></path></svg>
                <span>Copy</span>
              </button>
              <button class="answer-action" type="button" data-action="share">
                <svg class="icon share" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11"></path><path d="M8 8l4-4 4 4"></path><path d="M5 14v5h14v-5"></path></svg>
                <span>Share</span>
              </button>
            </div>
          </article>
        `;

        // Populate sources panel for normal fund answers
        if (fundFromAnswer) {
          state.activeFund = fundFromAnswer.short_name;
          populateSourcesPanel(fundFromAnswer);
          // Active fund chip follows the fund of the latest factual answer
          syncMobileFundChips();
        } else {
          populateSourcesPanel(data, fundDisplay, fetchDate);
        }
      }

      // Replace typing indicator with bot response
      const typingEl = messagesEl.querySelector('.typing-indicator');
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
      messagesEl.scrollTop = messagesEl.scrollHeight;
    } catch (e) {
      console.error('Render error:', e);
      renderBotError('Something went wrong. Please try again in a moment.', messagesEl);
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
    const fundId = normalizeFundId(shortName);
    const fund = state.fundsList.find(f => normalizeFundId(f.short_name) === fundId);
    return fund ? fund.scheme_name : null;
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
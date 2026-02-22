/* ============================================================
   F&O Sentinel — app.js
   All dashboard logic: polling, API calls, UI updates
   ============================================================ */

const API = '';
let POLL_INTERVAL = null;
let currentSettings = {};
let pendingMode = null;
let pendingConfirmCallback = null;

// ── Bootstrap ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('fno_token');
    if (!token) { window.location.href = '/login'; return; }

    document.getElementById('user-chip').textContent = localStorage.getItem('fno_user') || 'Trader';

    loadSettings();
    pollStatus();
    POLL_INTERVAL = setInterval(pollStatus, 3000);
});

function logout() {
    clearInterval(POLL_INTERVAL);
    localStorage.clear();
    window.location.href = '/login';
}

function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('fno_token')}`
    };
}

async function apiCall(url, method = 'GET', body = null) {
    try {
        const opts = { method, headers: authHeaders() };
        if (body) opts.body = JSON.stringify(body);
        const resp = await fetch(API + url, opts);
        if (resp.status === 401) { logout(); return null; }
        return await resp.json();
    } catch (e) {
        console.error('API error:', e);
        return null;
    }
}

// ── Polling ───────────────────────────────────────────────────
async function pollStatus() {
    const status = await apiCall('/api/bot/status');
    if (!status) return;
    updateStatusUI(status);
}

function updateStatusUI(status) {
    const running = status.running;
    const cta = document.getElementById('main-cta');
    const ctaLabel = document.getElementById('cta-label');
    const statStatus = document.getElementById('stat-status');
    const statUptime = document.getElementById('stat-uptime');
    const modeBadge = document.getElementById('mode-badge');
    const modeText = document.getElementById('mode-text');
    const uptimeDisplay = document.getElementById('uptime-display');

    cta.className = `cta-btn ${running ? 'stop' : 'start'}`;
    ctaLabel.textContent = running ? 'STOP BOT' : 'START BOT';
    statStatus.textContent = running ? 'RUNNING' : 'STOPPED';
    statStatus.style.color = running ? 'var(--accent-green)' : 'var(--accent-red)';
    statUptime.textContent = `Uptime: ${status.uptime || '0s'}`;
    uptimeDisplay.textContent = running ? `Running for ${status.uptime}` : '';

    const mode = status.trading_mode || 'PAPER';
    modeBadge.className = `mode-badge ${mode.toLowerCase()}`;
    modeText.textContent = mode;

    // OTP
    const otpAlert = document.getElementById('otp-alert');
    if (status.otp_pending) {
        otpAlert.classList.remove('hidden');
    } else {
        otpAlert.classList.add('hidden');
    }

    // Logs
    if (status.logs && status.logs.length > 0) {
        const term = document.getElementById('terminal');
        term.innerHTML = status.logs.map(l => {
            let cls = 'log-entry';
            if (l.includes('❌') || l.includes('FATAL') || l.includes('ERROR')) cls += ' log-error';
            else if (l.includes('⚠️') || l.includes('WARNING')) cls += ' log-warning';
            else if (l.includes('✅') || l.includes('ENTRY') || l.includes('EXIT')) cls += ' log-success';
            return `<div class="${cls}">${escapeHtml(l)}</div>`;
        }).join('');
        term.scrollTop = term.scrollHeight;
    }
}

// ── Bot Control ───────────────────────────────────────────────
async function handleBotToggle() {
    const running = document.getElementById('cta-label').textContent === 'STOP BOT';
    if (running) {
        showConfirm(
            '🛑', 'Stop the Bot?',
            'All monitoring will pause. Active positions will still be tracked when restarted.',
            async () => {
                const r = await apiCall('/api/bot/stop', 'POST');
                if (r) showNotif(r.message || 'Bot stopping...', 'success');
                await pollStatus();
            }
        );
    } else {
        const r = await apiCall('/api/bot/start', 'POST');
        if (r) {
            if (r.status === 'needs_otp') {
                document.getElementById('otp-alert').classList.remove('hidden');
            }
            showNotif(r.message || 'Bot started!', r.status === 'error' ? 'error' : 'success');
        }
        await pollStatus();
    }
}

// ── Settings ──────────────────────────────────────────────────
async function loadSettings() {
    const s = await apiCall('/api/settings/');
    if (!s) return;
    currentSettings = s;
    populateSettingsUI(s);
}

function populateSettingsUI(s) {
    const set = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined && val !== null) el.value = val; };
    const check = (id, val) => { const el = document.getElementById(id); if (el) el.checked = !!val; };

    set('s-capital', s.initial_capital);
    set('s-loss-limit', s.daily_loss_limit_pct);
    set('s-profit-cap', s.daily_profit_cap);
    set('s-rsi-min', s.rsi_min);
    set('s-rsi-max', s.rsi_max);
    set('s-adx', s.adx_min_daily);
    set('s-vix', s.vix_min_threshold);
    set('s-target', s.profit_target_amount);
    set('s-strike', s.strike_depth);
    set('s-open', s.market_open_time);
    set('s-cutoff', s.entry_cutoff_time);
    set('s-nifty-sl-low', s.nifty_sl_low);
    set('s-nifty-sl-mid', s.nifty_sl_mid);
    set('s-nifty-sl-high', s.nifty_sl_high);
    set('s-bn-sl-low', s.banknifty_sl_low);
    set('s-bn-sl-mid', s.banknifty_sl_mid);
    set('s-bn-sl-high', s.banknifty_sl_high);
    set('s-fn-sl-low', s.finnifty_sl_low);
    set('s-fn-sl-mid', s.finnifty_sl_mid);
    set('s-fn-sl-high', s.finnifty_sl_high);
    set('s-sx-sl-low', s.sensex_sl_low);
    set('s-sx-sl-mid', s.sensex_sl_mid);
    set('s-sx-sl-high', s.sensex_sl_high);
    set('s-nifty-lots', s.nifty_lots);
    set('s-bn-lots', s.banknifty_lots);
    set('s-fn-lots', s.finnifty_lots);
    set('s-sx-lots', s.sensex_lots);
    check('s-trade-nifty', s.trade_nifty);
    check('s-trade-bn', s.trade_banknifty);
    check('s-trade-fn', s.trade_finnifty);
    check('s-trade-sx', s.trade_sensex);
    check('s-email-on', s.email_enabled);
    set('s-email-addr', s.email_address);
    set('s-smtp-host', s.email_smtp_host);
    set('s-smtp-port', s.email_smtp_port);
    check('s-tg-on', s.telegram_enabled);
    set('s-tg-chatid', s.telegram_chat_id);

    setModeUI(s.trading_mode || 'PAPER');

    // Credential badges
    const connStatus = document.getElementById('conn-status');
    const credSet = s.mstock_api_key_set && s.mstock_client_code_set;
    connStatus.innerHTML = credSet
        ? `<span style="color:var(--accent-green)">✅ mStock credentials saved</span>${s.mstock_access_token_set ? ' &nbsp;·&nbsp; <span style="color:var(--accent-green)">Token active</span>' : ' &nbsp;·&nbsp; <span style="color:var(--accent-orange)">⚠️ Not authenticated — click Initiate Login</span>'}`
        : `<span style="color:var(--accent-orange)">⚠️ No mStock credentials yet</span>`;
}

function setMode(mode) {
    if (mode === 'LIVE' && currentSettings.trading_mode !== 'LIVE') {
        showConfirm('⚡', 'Switch to LIVE mode?',
            'Real orders will be placed with mStock using your account. This action trades with real money.',
            () => { currentSettings.trading_mode = 'LIVE'; setModeUI('LIVE'); }
        );
    } else {
        currentSettings.trading_mode = mode;
        setModeUI(mode);
    }
}

function setModeUI(mode) {
    document.getElementById('mode-paper').className = 'radio-opt' + (mode === 'PAPER' ? ' active-paper' : '');
    document.getElementById('mode-live').className = 'radio-opt' + (mode === 'LIVE' ? ' active-live' : '');
    currentSettings.trading_mode = mode;
}

async function saveSettings() {
    const btn = document.getElementById('save-btn');
    const text = document.getElementById('save-text');
    const spinner = document.getElementById('save-spinner');
    btn.disabled = true;
    text.classList.add('hidden');
    spinner.classList.remove('hidden');

    const get = (id) => { const el = document.getElementById(id); return el ? el.value || null : null; };
    const getNum = (id) => { const v = get(id); return v ? parseFloat(v) : null; };
    const getInt = (id) => { const v = get(id); return v ? parseInt(v) : null; };
    const getBool = (id) => { const el = document.getElementById(id); return el ? el.checked : null; };

    const payload = {
        trading_mode: currentSettings.trading_mode,
        initial_capital: getNum('s-capital'),
        daily_loss_limit_pct: getNum('s-loss-limit'),
        daily_profit_cap: getNum('s-profit-cap'),
        rsi_min: getNum('s-rsi-min'),
        rsi_max: getNum('s-rsi-max'),
        adx_min_daily: getNum('s-adx'),
        vix_min_threshold: getNum('s-vix'),
        profit_target_amount: getNum('s-target'),
        strike_depth: getInt('s-strike'),
        market_open_time: get('s-open'),
        entry_cutoff_time: get('s-cutoff'),
        nifty_sl_low: getNum('s-nifty-sl-low'),
        nifty_sl_mid: getNum('s-nifty-sl-mid'),
        nifty_sl_high: getNum('s-nifty-sl-high'),
        banknifty_sl_low: getNum('s-bn-sl-low'),
        banknifty_sl_mid: getNum('s-bn-sl-mid'),
        banknifty_sl_high: getNum('s-bn-sl-high'),
        finnifty_sl_low: getNum('s-fn-sl-low'),
        finnifty_sl_mid: getNum('s-fn-sl-mid'),
        finnifty_sl_high: getNum('s-fn-sl-high'),
        sensex_sl_low: getNum('s-sx-sl-low'),
        sensex_sl_mid: getNum('s-sx-sl-mid'),
        sensex_sl_high: getNum('s-sx-sl-high'),
        nifty_lots: getInt('s-nifty-lots'),
        banknifty_lots: getInt('s-bn-lots'),
        finnifty_lots: getInt('s-fn-lots'),
        sensex_lots: getInt('s-sx-lots'),
        trade_nifty: getBool('s-trade-nifty'),
        trade_banknifty: getBool('s-trade-bn'),
        trade_finnifty: getBool('s-trade-fn'),
        trade_sensex: getBool('s-trade-sx'),
        email_enabled: getBool('s-email-on'),
        email_address: get('s-email-addr'),
        email_smtp_host: get('s-smtp-host'),
        email_smtp_port: getInt('s-smtp-port'),
        email_smtp_user: get('s-smtp-user') || undefined,
        email_smtp_pass: get('s-smtp-pass') || undefined,
        telegram_enabled: getBool('s-tg-on'),
        telegram_bot_token: get('s-tg-token') || undefined,
        telegram_chat_id: get('s-tg-chatid'),
        mstock_api_key: get('s-api-key') || undefined,
        mstock_api_secret: get('s-api-secret') || undefined,
        mstock_client_code: get('s-client-code') || undefined,
        mstock_password: get('s-password') || undefined,
    };

    // Remove nulls/undefined
    Object.keys(payload).forEach(k => (payload[k] === null || payload[k] === undefined) && delete payload[k]);

    const result = await apiCall('/api/settings/', 'POST', payload);

    btn.disabled = false;
    text.classList.remove('hidden');
    spinner.classList.add('hidden');

    if (result) {
        showNotif('✅ Settings saved successfully!', 'success');
        if (result.settings) {
            currentSettings = result.settings;
            populateSettingsUI(result.settings);
        }
    } else {
        showNotif('❌ Failed to save settings.', 'error');
    }
}

async function testConnection() {
    const btn = document.getElementById('test-conn-btn');
    btn.textContent = '⏳ Testing...';
    btn.disabled = true;
    const r = await apiCall('/api/settings/test-connection', 'POST');
    btn.textContent = '🔌 Test Connection';
    btn.disabled = false;
    if (r) {
        const cs = document.getElementById('conn-status');
        cs.innerHTML = r.message;
        cs.style.color = r.status === 'connected' ? 'var(--accent-green)' : 'var(--accent-orange)';
        showNotif(r.message, r.status === 'connected' ? 'success' : 'error');
    }
}

async function initiateLogin() {
    const btn = document.getElementById('initiate-login-btn');
    btn.textContent = '⏳ Sending OTP...';
    btn.disabled = true;
    const r = await apiCall('/api/bot/initiate-login', 'POST');
    btn.textContent = '📱 Initiate mStock Login (OTP)';
    btn.disabled = false;
    if (r) {
        showNotif(r.message, r.status === 'otp_sent' ? 'success' : 'error');
        if (r.status === 'otp_sent') showOtpModal();
    }
}

// ── OTP ───────────────────────────────────────────────────────
function showOtpModal() { document.getElementById('otp-modal').classList.remove('hidden'); document.getElementById('otp-input').focus(); }
function hideOtpModal() { document.getElementById('otp-modal').classList.add('hidden'); }

async function submitOtp() {
    const otp = document.getElementById('otp-input').value.trim();
    if (!otp || otp.length < 4) { showNotif('Please enter a valid OTP', 'error'); return; }
    const r = await apiCall('/api/bot/otp', 'POST', { otp });
    hideOtpModal();
    if (r) showNotif(r.message, r.status === 'authenticated' ? 'success' : 'error');
    await loadSettings();
}

// ── Collapsible sections ──────────────────────────────────────
function toggleSection(name) {
    const body = document.getElementById(name + '-body');
    const arrow = document.getElementById(name + '-arrow');
    body.classList.toggle('open');
    arrow.classList.toggle('open');
}

// ── Confirm dialog ────────────────────────────────────────────
function showConfirm(icon, title, body, callback) {
    document.getElementById('confirm-icon').textContent = icon;
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-body').textContent = body;
    pendingConfirmCallback = callback;
    document.getElementById('confirm-modal').classList.remove('hidden');
}
function hideConfirm() { document.getElementById('confirm-modal').classList.add('hidden'); pendingConfirmCallback = null; }
function confirmAction() { if (pendingConfirmCallback) pendingConfirmCallback(); hideConfirm(); }

// ── Notifications ─────────────────────────────────────────────
function showNotif(message, type = 'success') {
    const el = document.createElement('div');
    el.className = `notif-banner notif-${type}`;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}

// ── Utils ─────────────────────────────────────────────────────
function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

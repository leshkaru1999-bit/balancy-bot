// ============================================================
// BALANCY MINI APP — app.js
// Навигация, рендер, формы, загрузка данных
// ============================================================

// ── Telegram Web App ──────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const telegramId = tg?.initDataUnsafe?.user?.id || null;
const initData = tg?.initData || null;

if (!telegramId || !initData) {
  const debugTg = window.Telegram?.WebApp ? JSON.stringify(window.Telegram.WebApp.initDataUnsafe) : "No tg object";
  const debugInitData = window.Telegram?.WebApp?.initData || "empty string";
  const debugUrl = window.location.href;

  document.getElementById('app').innerHTML = `
    <div style="padding: 20px; color: white; text-align: center; margin-top: 50px; font-size: 16px; line-height: 1.5; word-break: break-all;">
      ❌ Ошибка безопасности<br><br>Приложение должно быть открыто только внутри Telegram.
      <hr style="border-color:#333; margin: 15px 0;">
      <p style="font-size: 10px; color: yellow; text-align: left;">initData: ${debugInitData}</p>
      <p style="font-size: 10px; color: yellow; text-align: left;">initDataUnsafe: ${debugTg}</p>
      <p style="font-size: 10px; color: cyan; text-align: left;">URL: ${debugUrl}</p>
    </div>
  `;
  throw new Error("No secure telegram initData provided");
}


// ── I18N ────────────────────────────────────────────────────────
const I18N = {
  ru: {
    loading: "Загрузка...",
    cancel: "Отмена",
    error_no_id: "❌ Ошибка!\n\nПожалуйста, закройте это окно, отправьте боту команду /start и нажмите на кнопку «Открыть Balancy» под сообщением бота.",
    greeting: "Добро пожаловать 👋",
    balance_label: "Текущий баланс",
    income: "Доходы",
    expense: "Расходы",
    last_ops: "Последние операции",
    all: "Все",
    history: "История",
    stats: "Статистика",
    add_operation: "Новая операция",
    amount_label: "Сумма (сум)",
    cat_label: "Категория",
    comment_label: "Комментарий (необязательно)",
    btn_save: "Сохранить",
    btn_cancel: "Отмена",
    set_balance: "Установить баланс",
    set_balance_desc: "Введи текущий остаток средств",
    nav_home: "Главная",
    nav_stats: "Статистика",
    nav_profile: "Профиль",
    cat_food: "Еда",
    cat_transport: "Транспорт",
    cat_shopping: "Покупки",
  },
  uz: {
    greeting: "Xush kelibsiz 👋",
    balance_label: "Joriy balans",
    income: "Daromadlar",
    expense: "Xarajatlar",
    last_ops: "So'nggi operatsiyalar",
    all: "Barchasi",
    history: "Tarix",
    stats: "Statistika",
    add_operation: "Yangi operatsiya",
    amount_label: "Summa (so'm)",
    cat_label: "Kategoriya",
    comment_label: "Izoh (ixtiyoriy)",
    btn_save: "Saqlash",
    btn_cancel: "Bekor qilish",
    set_balance: "Balansni kiritish",
    set_balance_desc: "Joriy balansni kiriting",
    nav_home: "Asosiy",
    nav_stats: "Statistika",
    nav_profile: "Profil",
    cat_food: "Ovqat",
    cat_transport: "Transport",
    cat_shopping: "Xaridlar",
  }
};

function applyTranslations(lang) {
  const texts = I18N[lang] || I18N["ru"];
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (texts[key]) el.textContent = texts[key];
  });
}

const lang = tg?.initDataUnsafe?.user?.language_code === 'uz' ? 'uz' : 'ru';
const t = (key) => I18N[lang]?.[key] || key;

if (!telegramId) {
  document.getElementById('app').innerHTML = `
    <div style="padding: 20px; color: white; text-align: center; margin-top: 50px; font-size: 16px; line-height: 1.5;">
      ${t('error_no_id')}
    </div>
  `;
  throw new Error("No telegram ID provided");
}

let txData = [];
let userData = null;

// ── State ─────────────────────────────────────────────────────
let state = {
  balance: 0,
  language: "ru",
  transactions: [],
  stats: [],
  currentScreen: "home",
  statsType: "expense",
  categoryTabType: "expense",
  selectedCategory: null,
  selectedType: "expense",
  customCategories: [],
  limits: [],
  isPremium: false,
  premiumUntil: null,
  remindersEnabled: false,
  reminderTime: "20:00",
  homeFilter: "all",
};

// ── Category definitions ──────────────────────────────────────
const CATS_EXPENSE = [
  { icon: "🍽️", label: "Еда",           value: "Еда" },
  { icon: "☕",  label: "Кафе",          value: "Кафе/Ресторан" },
  { icon: "🛒",  label: "Продукты",      value: "Продукты" },
  { icon: "🚌",  label: "Транспорт",     value: "Транспорт" },
  { icon: "🚕",  label: "Такси",         value: "Такси" },
  { icon: "👕",  label: "Одежда",        value: "Одежда" },
  { icon: "💊",  label: "Здоровье",      value: "Здоровье" },
  { icon: "🎬",  label: "Развлечения",   value: "Развлечения" },
  { icon: "📱",  label: "Связь",         value: "Связь" },
  { icon: "🏠",  label: "Комм. услуги",  value: "Коммунальные" },
  { icon: "📌",  label: "Прочее",        value: "Прочее" },
];

const CATS_INCOME = [
  { icon: "💼", label: "Зарплата", value: "Зарплата" },
  { icon: "💻", label: "Фриланс",  value: "Фриланс" },
  { icon: "🎁", label: "Подарок",  value: "Прочее" },
  { icon: "📌", label: "Прочее",   value: "Прочее" },
];

const CAT_ICONS = {
  "Еда": "🍽️", "Кафе/Ресторан": "☕", "Транспорт": "🚌",
  "Такси": "🚕", "Продукты": "🛒", "Одежда": "👕",
  "Здоровье": "💊", "Развлечения": "🎬", "Зарплата": "💼",
  "Фриланс": "💻", "Связь": "📱", "Коммунальные": "🏠",
  "Прочее": "📌",
};

const CHART_COLORS = [
  "#7c6eff", "#ff6584", "#ffd97d", "#22c55e",
  "#38bdf8", "#f59e0b", "#ef4444", "#a855f7",
  "#10b981", "#f97316",
];

// ── Helpers ───────────────────────────────────────────────────
function fmtMoney(n) {
  return new Intl.NumberFormat("ru-RU").format(Math.round(n)) + " сум";
}

function fmtShort(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000)     return (n / 1_000).toFixed(0) + "K";
  return Math.round(n).toString();
}

function fmtDate(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diff = now - d;
  if (diff < 60_000) return "только что";
  if (diff < 3_600_000) return Math.floor(diff / 60_000) + " мин назад";
  if (diff < 86_400_000) return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "short" });
}

function animateCounter(el, target, duration = 700) {
  const start = Date.now();
  const from  = parseFloat(el.dataset.val || 0);
  el.dataset.val = target;
  const step = () => {
    const p = Math.min((Date.now() - start) / duration, 1);
    const e = 1 - Math.pow(1 - p, 3);
    const v = from + (target - from) * e;
    el.textContent = fmtMoney(v);
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ── Navigation ────────────────────────────────────────────────
function navigate(screenName) {
  if (state.currentScreen === screenName) return;

  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-item[data-screen]").forEach(n => n.classList.remove("active"));

  const screen = document.getElementById(`screen-${screenName}`);
  if (screen) {
    screen.classList.add("active");
    state.currentScreen = screenName;
  }

  const navBtn = document.querySelector(`.nav-item[data-screen="${screenName}"]`);
  if (navBtn) navBtn.classList.add("active");

  // Render screen data
  if (screenName === "stats") renderStats();
  if (screenName === "history") renderHistoryFull();
  if (screenName === "categories") renderCustomCategories();
  if (screenName === "profile") renderProfile();
  if (screenName === "limits") renderLimits();
}

function openAddScreen() {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-item[data-screen]").forEach(n => n.classList.remove("active"));
  document.getElementById("screen-add").classList.add("active");
  state.currentScreen = "add";
  renderCategoryGrid();
}

// ── Toast ─────────────────────────────────────────────────────
function showToast(msg, duration = 2500) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove("show"), duration);
}

// ── Modal ─────────────────────────────────────────────────────
function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

// ── Render: Balance ───────────────────────────────────────────
function renderBalance() {
  const balEl = document.getElementById("balance-amount");
  animateCounter(balEl, state.balance);

  const income  = state.stats.filter(s => s.type === "income").reduce((a, s) => a + s.total, 0);
  const expense = state.stats.filter(s => s.type === "expense").reduce((a, s) => a + s.total, 0);

  document.getElementById("total-income").textContent  = fmtMoney(income);
  document.getElementById("total-expense").textContent = fmtMoney(expense);
}

// ── Render: Transactions (home - last 5) ──────────────────────
function setHomeFilter(btn) {
  document.querySelectorAll("#home-filter-tabs .filter-tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  state.homeFilter = btn.dataset.filter;
  renderHomeTransactions();
}

function renderHomeTransactions() {
  const el = document.getElementById("home-tx-list");
  
  let txs = [...state.transactions];
  if (state.homeFilter !== "all") {
    txs = txs.filter(tx => tx.category === state.homeFilter);
  }
  txs = txs.slice(0, 5);

  if (!txs.length) {
    el.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">📭</span>
        <p>${state.homeFilter === "all" ? "Отправь голосовое боту,<br>чтобы добавить первую запись" : "Нет записей по фильтру"}</p>
      </div>`;
    return;
  }

  el.innerHTML = "";
  txs.forEach((tx, i) => {
    el.appendChild(buildTxItem(tx, i));
  });
}

// ── Render: History (full list) ───────────────────────────────
function renderHistoryFull() {
  const filterVal = document.getElementById("history-filter")?.value || "all";
  const el = document.getElementById("history-tx-list");

  let txs = [...state.transactions];
  if (filterVal !== "all") txs = txs.filter(tx => tx.type === filterVal);

  if (!txs.length) {
    el.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">📭</span>
        <p>${filterVal === "all" ? "Операций пока нет" : "Нет записей по фильтру"}</p>
      </div>`;
    return;
  }

  el.innerHTML = "";
  txs.forEach((tx, i) => el.appendChild(buildTxItem(tx, i)));
}

function filterHistory() { renderHistoryFull(); }

// ── Build TX item ─────────────────────────────────────────────
function buildTxItem(tx, i) {
  const icon  = CAT_ICONS[tx.category] || "📌";
  const sign  = tx.type === "expense" ? "−" : "+";

  const div = document.createElement("div");
  div.className = "tx-item";
  div.style.animationDelay = `${i * 30}ms`;
  div.innerHTML = `
    <div class="tx-icon ${tx.type}">${icon}</div>
    <div class="tx-info">
      <p class="tx-category">${tx.category}</p>
      <p class="tx-desc">${tx.description || tx.raw_text || "—"}</p>
    </div>
    <div class="tx-right">
      <p class="tx-amount ${tx.type}">${sign}${fmtMoney(tx.amount)}</p>
      <p class="tx-date">${fmtDate(tx.created_at)}</p>
    </div>`;
  return div;
}

// ── Render: Stats ─────────────────────────────────────────────
function renderStats() {
  renderChart();
  renderStatCategories();
}

function switchStatsTab(btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  state.statsType = btn.dataset.type;
  renderStats();
}

function renderChart() {
  const canvas = document.getElementById("chart");
  const ctx    = canvas.getContext("2d");
  const legend = document.getElementById("chart-legend");
  const totalEl = document.getElementById("chart-total");

  const items = state.stats.filter(s => s.type === state.statsType);
  const total = items.reduce((a, s) => a + s.total, 0);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  legend.innerHTML = "";

  const cx = 90, cy = 90, R = 78, r = 50;
  const gap = 0.03; // gap between sectors (radians)

  if (!items.length) {
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255,255,255,0.06)";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = getComputedStyle(document.body).getPropertyValue("--bg") || "#0d0d14";
    ctx.fill();
    totalEl.textContent = "—";
    return;
  }

  totalEl.textContent = fmtShort(total);

  let angle = -Math.PI / 2;
  const sorted = [...items].sort((a, b) => b.total - a.total);

  sorted.forEach((s, i) => {
    const slice = (s.total / total) * (Math.PI * 2 - gap * sorted.length);
    const color = CHART_COLORS[i % CHART_COLORS.length];

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, R, angle + gap / 2, angle + slice + gap / 2);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    angle += slice + gap;

    // Legend
    const pct = Math.round((s.total / total) * 100);
    const li = document.createElement("div");
    li.className = "legend-item";
    li.innerHTML = `
      <div class="legend-dot" style="background:${color}"></div>
      <span class="legend-label">${s.category}</span>
      <span class="legend-value">${pct}%</span>`;
    legend.appendChild(li);
  });

  // Donut hole
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = getComputedStyle(document.body).getPropertyValue("--bg") || "#0d0d14";
  ctx.fill();
}

function renderStatCategories() {
  const el = document.getElementById("stats-categories");
  const items = state.stats
    .filter(s => s.type === state.statsType)
    .sort((a, b) => b.total - a.total);
  const total = items.reduce((a, s) => a + s.total, 0);

  if (!items.length) {
    el.innerHTML = `<div class="empty-state"><span class="empty-icon">📭</span><p>Нет данных</p></div>`;
    return;
  }

  el.innerHTML = "";
  items.forEach((s, i) => {
    const pct   = total > 0 ? (s.total / total * 100) : 0;
    const color = CHART_COLORS[i % CHART_COLORS.length];
    const icon  = CAT_ICONS[s.category] || "📌";

    const div = document.createElement("div");
    div.className = "stat-cat-item";
    div.style.animationDelay = `${i * 40}ms`;
    div.innerHTML = `
      <div class="stat-cat-icon">${icon}</div>
      <div class="stat-cat-info">
        <p class="stat-cat-name">${s.category}</p>
        <div class="stat-cat-bar-wrap">
          <div class="stat-cat-bar" style="width:0%; background:${color}"></div>
        </div>
      </div>
      <div>
        <p class="stat-cat-amount">${fmtMoney(s.total)}</p>
        <p class="stat-cat-pct">${Math.round(pct)}%</p>
      </div>`;
    el.appendChild(div);

    // Animate bar
    requestAnimationFrame(() => {
      const bar = div.querySelector(".stat-cat-bar");
      if (bar) bar.style.width = `${pct}%`;
    });
  });
}

// ── Render: Add Form ──────────────────────────────────────────
function renderCategoryGrid() {
  const grid = document.getElementById("category-grid");
  const baseCats = state.selectedType === "expense" ? CATS_EXPENSE : CATS_INCOME;
  const customCats = state.customCategories
    .filter(c => c.type === state.selectedType)
    .map(c => ({ icon: c.icon, label: c.name, value: c.name, isCustom: true }));
  
  const cats = [...baseCats, ...customCats];
  state.selectedCategory = null;

  grid.innerHTML = "";
  cats.forEach(cat => {
    const btn = document.createElement("button");
    btn.className = "cat-btn" + (cat.isCustom ? " custom-cat" : "");
    btn.dataset.value = cat.value;
    btn.innerHTML = `<span class="cat-btn-icon">${cat.icon}</span><span>${cat.label}</span>`;
    btn.onclick = () => selectCategory(cat.value, btn);
    grid.appendChild(btn);
  });
}

// ── Render: Manage Categories ─────────────────────────────────
function switchCategoryTab(btn) {
  document.querySelectorAll("#screen-categories .tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  state.categoryTabType = btn.dataset.type;
  renderCustomCategories();
}

function renderCustomCategories() {
  const el = document.getElementById("custom-categories-list");
  
  const baseCats = state.categoryTabType === "expense" ? CATS_EXPENSE : CATS_INCOME;
  const customCats = state.customCategories.filter(c => c.type === state.categoryTabType);
  
  el.innerHTML = "";
  
  // Render Custom
  customCats.forEach(c => {
    const div = document.createElement("div");
    div.className = "tx-item";
    div.innerHTML = `
      <div class="tx-icon ${c.type}">${c.icon}</div>
      <div class="tx-info">
        <p class="tx-category">${c.name}</p>
        <p class="tx-desc" style="color:#22c55e">Моя категория</p>
      </div>
      <div class="tx-right">
        <button class="btn-icon" style="color:#ef4444" onclick="deleteCustomCategory(${c.id})">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
    `;
    el.appendChild(div);
  });
  
  // Render Base
  baseCats.forEach(c => {
    const div = document.createElement("div");
    div.className = "tx-item";
    div.innerHTML = `
      <div class="tx-icon ${state.categoryTabType}">${c.icon}</div>
      <div class="tx-info">
        <p class="tx-category">${c.label}</p>
        <p class="tx-desc">Базовая (нельзя удалить)</p>
      </div>
    `;
    el.appendChild(div);
  });
}

async function addCustomCategory() {
  const icon = document.getElementById("new-cat-icon").value.trim();
  const name = document.getElementById("new-cat-name").value.trim();
  
  if (!icon || !name) {
    showToast("❌ Введи эмодзи и название");
    tg?.HapticFeedback?.notificationOccurred("error");
    return;
  }
  
  const btn = document.getElementById("btn-add-cat");
  btn.disabled = true;
  btn.textContent = "⏳...";
  
  try {
    if (telegramId) {
      const cat = await apiAddCategory(telegramId, state.categoryTabType, name, icon);
      state.customCategories.push(cat);
    } else {
      state.customCategories.push({
        id: Date.now(), type: state.categoryTabType, name, icon
      });
    }
    
    // Clear inputs
    document.getElementById("new-cat-icon").value = "";
    document.getElementById("new-cat-name").value = "";
    
    renderCustomCategories();
    showToast("✅ Категория добавлена!");
    tg?.HapticFeedback?.notificationOccurred("success");
    
    // Update icons dict for stats/history rendering
    CAT_ICONS[name] = icon;
    
  } catch (err) {
    showToast("❌ Ошибка: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Добавить";
  }
}

async function deleteCustomCategory(id) {
  if (!confirm("Удалить эту категорию?")) return;
  
  try {
    if (telegramId) {
      await apiDeleteCategory(telegramId, id);
    }
    state.customCategories = state.customCategories.filter(c => c.id !== id);
    renderCustomCategories();
    showToast("✅ Категория удалена");
    tg?.HapticFeedback?.notificationOccurred("success");
  } catch(err) {
    showToast("❌ Ошибка: " + err.message);
  }
}

function selectType(type, el) {
  state.selectedType = type;
  state.selectedCategory = null;
  document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
  el.classList.add("active");
  renderCategoryGrid();
}

function selectCategory(value, el) {
  state.selectedCategory = value;
  document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("selected"));
  el.classList.add("selected");
  tg?.HapticFeedback?.selectionChanged();
}

async function submitTransaction() {
  const amount = parseFloat(document.getElementById("add-amount").value);
  const desc   = document.getElementById("add-desc").value.trim();

  if (!amount || amount <= 0) {
    showToast("❌ Введи сумму");
    tg?.HapticFeedback?.notificationOccurred("error");
    return;
  }
  if (!state.selectedCategory) {
    showToast("❌ Выбери категорию");
    tg?.HapticFeedback?.notificationOccurred("error");
    return;
  }

  const btn = document.getElementById("btn-submit");
  btn.disabled = true;
  btn.textContent = "⏳ Сохраняю...";

  try {
    if (telegramId) {
      await apiAddTransaction(
        telegramId,
        state.selectedType,
        amount,
        state.selectedCategory,
        desc
      );
    } else {
      // Demo mode
      state.transactions.unshift({
        id: Date.now(),
        type: state.selectedType,
        amount,
        category: state.selectedCategory,
        description: desc,
        created_at: new Date().toISOString(),
      });
      if (state.selectedType === "expense") state.balance -= amount;
      else state.balance += amount;
    }

    // Refresh and navigate home
    if (telegramId) await loadData();
    else renderBalance();

    showToast("✅ Сохранено!");
    tg?.HapticFeedback?.notificationOccurred("success");

    // Reset form
    document.getElementById("add-amount").value = "";
    document.getElementById("add-desc").value   = "";
    state.selectedCategory = null;
    document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("selected"));

    navigate("home");
  } catch (err) {
    showToast("❌ Ошибка: " + err.message);
    tg?.HapticFeedback?.notificationOccurred("error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Сохранить";
  }
}

// ── Profile ───────────────────────────────────────────────────
function renderProfile() {
  document.getElementById("profile-name").value = state.firstName || "";
  
  // Premium
  const premStatus = document.getElementById("premium-status");
  if (state.isPremium && state.premiumUntil) {
    const d = new Date(state.premiumUntil);
    premStatus.textContent = `Активен до ${d.toLocaleDateString()}`;
    premStatus.style.color = "#22c55e";
  } else {
    premStatus.textContent = "Нет активной подписки";
    premStatus.style.color = "#a1a1aa";
  }
  
  // Reminders
  const tgl = document.getElementById("reminders-toggle");
  const timeBox = document.getElementById("reminders-time-box");
  const timeInput = document.getElementById("reminders-time");
  
  tgl.checked = state.remindersEnabled;
  timeInput.value = state.reminderTime;
  timeBox.style.opacity = state.remindersEnabled ? "1" : "0.5";
  timeBox.style.pointerEvents = state.remindersEnabled ? "auto" : "none";
}

async function saveProfileName() {
  const name = document.getElementById("profile-name").value.trim();
  if (!name) return showToast("❌ Введи имя");
  try {
    if (telegramId) await apiUpdateUserName(telegramId, name);
    state.firstName = name;
    showToast("✅ Имя сохранено!");
    tg?.HapticFeedback?.notificationOccurred("success");
  } catch (err) { showToast("❌ " + err.message); }
}

async function toggleReminders() {
  state.remindersEnabled = document.getElementById("reminders-toggle").checked;
  document.getElementById("reminders-time-box").style.opacity = state.remindersEnabled ? "1" : "0.5";
  document.getElementById("reminders-time-box").style.pointerEvents = state.remindersEnabled ? "auto" : "none";
  await _saveReminders();
}

async function saveReminderTime() {
  state.reminderTime = document.getElementById("reminders-time").value || "20:00";
  await _saveReminders();
}

async function _saveReminders() {
  try {
    if (telegramId) {
      await apiUpdateReminders(telegramId, state.remindersEnabled, state.reminderTime);
    }
    showToast("✅ Настройки уведомлений сохранены");
  } catch(err) {
    showToast("❌ " + err.message);
  }
};

async function resetUserData() {
  if (tg && tg.showConfirm) {
    tg.showConfirm("Вы уверены, что хотите удалить все транзакции и обнулить баланс? Это действие необратимо.", async (confirmed) => {
      if (confirmed) {
        await executeReset();
      }
    });
  } else {
    if (confirm("Вы уверены, что хотите удалить все транзакции и обнулить баланс? Это действие необратимо.")) {
      await executeReset();
    }
  }
}

async function executeReset() {
  try {
    if (telegramId) {
      await apiResetData(telegramId);
      await loadData();
    } else {
      state.balance = 0;
      state.transactions = [];
      state.stats = [];
      renderBalance();
    }
    showToast("✅ Данные успешно сброшены");
    tg?.HapticFeedback?.notificationOccurred("success");
    navigate("home");
  } catch(err) {
    showToast("❌ Ошибка сброса: " + err.message);
  }
}

// ── Limits ────────────────────────────────────────────────────
function renderLimits() {
  const list = document.getElementById("limits-list");
  const select = document.getElementById("limit-cat-select");
  list.innerHTML = "";
  select.innerHTML = "";
  
  // Populate select (Expenses only)
  const expenseCats = [...CATS_EXPENSE, ...state.customCategories.filter(c => c.type === 'expense')];
  expenseCats.forEach(c => {
    const name = c.name || c.value;
    const icon = c.icon;
    const label = c.label || name;
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = `${icon} ${label}`;
    select.appendChild(opt);
  });
  
  // Render limits list
  if (state.limits.length === 0) {
    list.innerHTML = `<p style="text-align:center; color:#a1a1aa; padding:20px;">У вас пока нет лимитов.</p>`;
    return;
  }
  
  // Calculate spent this month per category from history (for accurate UI)
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  
  if (!telegramId) {
    const debugTg = window.Telegram?.WebApp ? JSON.stringify(window.Telegram.WebApp.initDataUnsafe) : "No tg object";
    const debugUrl = window.location.href;
    document.getElementById("app").innerHTML = `
      <div style="padding: 32px; text-align: center; background: var(--bg); word-break: break-all;">
        <h2 style="font-size: 22px; margin-bottom: 12px; color: var(--text);">Ошибка ID</h2>
        <p style="color: var(--text2); margin-bottom: 16px;">telegramId = null</p>
        <p style="color: yellow; text-align: left; font-size: 10px; margin-bottom: 8px;">initDataUnsafe: ${debugTg}</p>
        <p style="color: cyan; text-align: left; font-size: 10px;">URL: ${debugUrl}</p>
      </div>
    `;
    return;
  }

  state.limits.forEach(lim => {
    // find spent amount
    const spent = state.transactions
      .filter(tx => tx.category === lim.category && tx.type === "expense" && new Date(tx.created_at) >= monthStart)
      .reduce((a, b) => a + b.amount, 0);
      
    const percent = Math.min(100, Math.round((spent / lim.limit_amount) * 100));
    let fillClass = "normal";
    if (percent >= 80) fillClass = "warning";
    if (percent >= 100) fillClass = "danger";
    
    const icon = CAT_ICONS[lim.category] || "📌";
    const div = document.createElement("div");
    div.className = "tx-item";
    div.style.flexDirection = "column";
    div.style.alignItems = "stretch";
    
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:12px;">
          <div class="tx-icon expense" style="width:36px; height:36px; font-size:18px;">${icon}</div>
          <div>
            <p class="tx-category" style="font-size:15px;">${lim.category}</p>
            <p class="tx-desc">${fmtMoney(spent)} из ${fmtMoney(lim.limit_amount)}</p>
          </div>
        </div>
        <button class="btn-icon" style="color:#ef4444" onclick="deleteLimit(${lim.id})">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
      <div class="progress-bg">
        <div class="progress-fill ${fillClass}" style="width: ${percent}%"></div>
      </div>
    `;
    list.appendChild(div);
  });
}

async function addLimit() {
  const cat = document.getElementById("limit-cat-select").value;
  const amt = parseFloat(document.getElementById("limit-amount").value);
  
  if (!amt || amt <= 0) return showToast("❌ Введи сумму лимита");
  
  const btn = document.getElementById("btn-add-limit");
  btn.disabled = true; btn.textContent = "⏳...";
  try {
    if (telegramId) {
      await apiSetLimit(telegramId, cat, amt);
      state.limits = await fetchLimits(telegramId);
    }
    document.getElementById("limit-amount").value = "";
    renderLimits();
    showToast("✅ Лимит установлен");
    tg?.HapticFeedback?.notificationOccurred("success");
  } catch(err) { showToast("❌ " + err.message); }
  finally { btn.disabled = false; btn.textContent = "Добавить"; }
}

async function deleteLimit(id) {
  if (!confirm("Удалить лимит?")) return;
  try {
    if (telegramId) {
      await apiDeleteLimit(telegramId, id);
      state.limits = state.limits.filter(l => l.id !== id);
    }
    renderLimits();
    showToast("✅ Лимит удален");
  } catch(err) { showToast("❌ " + err.message); }
}

// ── Load data ─────────────────────────────────────────────────
async function loadData() {
  if (!telegramId) {
    const debugTg = window.Telegram?.WebApp ? JSON.stringify(window.Telegram.WebApp.initDataUnsafe) : "No tg object";
    const debugUrl = window.location.href;
    document.getElementById("app").innerHTML = `
      <div style="padding: 32px; text-align: center; background: var(--bg); word-break: break-all;">
        <h2 style="font-size: 22px; margin-bottom: 12px; color: var(--text);">Error ID</h2>
        <p style="color: var(--text2); margin-bottom: 16px;">telegramId = null</p>
        <p style="color: yellow; text-align: left; font-size: 10px; margin-bottom: 8px;">initDataUnsafe: ${debugTg}</p>
        <p style="color: cyan; text-align: left; font-size: 10px;">URL: ${debugUrl}</p>
      </div>
    `;
    return;
  }

  try {
    const [uData, tData, sData, cData, lData] = await Promise.all([
      fetchUser(telegramId),
      fetchTransactions(telegramId),
      fetchStats(telegramId, document.getElementById("stats-period")?.value || "month"),
      fetchCategories(telegramId),
      telegramId ? fetchLimits(telegramId) : Promise.resolve([])
    ]);
    
    userData = uData;
    txData = tData;
    
    state.balance          = userData.balance      || 0;
    state.language         = userData.language     || "ru";
    state.firstName        = userData.first_name   || "Balancy User";
    state.isPremium        = userData.is_premium   || false;
    state.premiumUntil     = userData.premium_until;
    state.remindersEnabled = userData.reminders_enabled || false;
    state.reminderTime     = userData.reminder_time || "20:00";
    state.transactions     = txData                || [];
    state.stats            = sData                 || [];
    state.customCategories = cData                 || [];
    state.limits           = lData                 || [];
    
    // update global icons map
    state.customCategories.forEach(c => {
      CAT_ICONS[c.name] = c.icon;
    });

    applyTranslations(state.language);
    renderAll();
  } catch (err) {
    console.error("Ошибка загрузки:", err);
    document.getElementById("app").innerHTML = `
      <div style="padding: 32px; text-align: left; background: var(--bg); word-break: break-all;">
        <h2 style="color: red;">Catch Error</h2>
        <p style="color: yellow; font-size: 12px;">${err.message}</p>
        <p style="color: cyan; font-size: 10px;">Stack: ${err.stack}</p>
      </div>
    `;}
}

function renderAll() {
  renderBalance();
  renderHomeTransactions();
  if (state.currentScreen === "stats")   renderStats();
  if (state.currentScreen === "history") renderHistoryFull();
}

function onPeriodChange() {
  const period = document.getElementById("stats-period").value;
  const customRange = document.getElementById("custom-date-range");
  if (period === "custom") {
    customRange.style.display = "flex";
    const today = new Date().toISOString().split('T')[0];
    if (!document.getElementById("date-start").value) document.getElementById("date-start").value = today;
    if (!document.getElementById("date-end").value) document.getElementById("date-end").value = today;
  } else {
    customRange.style.display = "none";
  }
  loadStats();
}

async function loadStats() {
  if (!telegramId) return;
  const period = document.getElementById("stats-period")?.value || "month";
  let startDate = "";
  let endDate = "";

  if (period === "custom") {
    startDate = document.getElementById("date-start").value;
    endDate = document.getElementById("date-end").value;
    if (!startDate || !endDate) return;
  }

  try {
    state.stats = await fetchStats(telegramId, period, startDate, endDate);
    renderStats();
  } catch (err) {
    showToast("❌ " + err.message);
  }
}

// ── Event Listeners ───────────────────────────────────────────
document.getElementById("btn-refresh")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-refresh");
  btn.classList.add("spin");
  await loadData();
  setTimeout(() => btn.classList.remove("spin"), 700);
});

// Close modal on overlay click
document.querySelectorAll(".modal-overlay").forEach(el => {
  el.addEventListener("click", e => {
    if (e.target.classList.contains("modal-overlay")) {
      closeModal(e.target.id);
    }
  });
});

// ── Init ──────────────────────────────────────────────────────
loadData();

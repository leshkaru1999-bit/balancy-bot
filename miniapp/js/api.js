// ============================================================
// BALANCY — API layer
// Все запросы идут на относительные пути /api/...
// Работает при любом ngrok URL (MinApp серверится тем же FastAPI)
// ============================================================

const BASE = "/api";

/**
 * Получить данные пользователя (баланс)
 */
async function fetchUser(telegramId) {
  const r = await fetch(`${BASE}/user/${telegramId}`, { headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка получения данных пользователя");
  return r.json();
}

/**
 * Получить историю транзакций
 */
async function fetchTransactions(telegramId, limit = 50) {
  const r = await fetch(`${BASE}/transactions/${telegramId}?limit=${limit}`, { headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка получения истории");
  return r.json();
}

/**
 * Получить статистику
 */
async function fetchStats(telegramId, period = "all", startDate = "", endDate = "") {
  let url = `${BASE}/stats/${telegramId}?period=${period}`;
  if (period === "custom" && startDate && endDate) {
    url += `&start_date=${startDate}&end_date=${endDate}`;
  }
  const r = await fetch(url, { headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка получения статистики");
  return r.json();
}

/**
 * Обновить имя пользователя
 */
async function apiUpdateUserName(telegramId, firstName) {
  const r = await fetch(`${BASE}/user/name`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" },
    body: JSON.stringify({ telegram_id: telegramId, first_name: firstName }),
  });
  if (!r.ok) throw new Error("Ошибка обновления имени");
  return r.json();
}

/**
 * Добавить транзакцию вручную из Mini App
 */
async function apiAddTransaction(telegramId, type, amount, category, description = "") {
  const r = await fetch(`${BASE}/transaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" },
    body: JSON.stringify({ telegram_id: telegramId, type, amount, category, description }),
  });
  if (!r.ok) throw new Error("Ошибка добавления транзакции");
  return r.json();
}

/**
 * Удалить транзакцию
 */
async function apiDeleteTransaction(txId) {
  const r = await fetch(`${BASE}/transaction/${txId}`, { method: "DELETE", headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка удаления транзакции");
  return r.json();
}

/**
 * Получить кастомные категории
 */
async function fetchCategories(telegramId) {
  const r = await fetch(`${BASE}/categories/${telegramId}`, { headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка получения категорий");
  return r.json();
}

/**
 * Добавить кастомную категорию
 */
async function apiAddCategory(telegramId, type, name, icon) {
  const r = await fetch(`${BASE}/categories`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" },
    body: JSON.stringify({ telegram_id: telegramId, type, name, icon }),
  });
  if (!r.ok) throw new Error("Ошибка добавления категории");
  return r.json();
}

/**
 * Удалить кастомную категорию
 */
async function apiDeleteCategory(telegramId, catId) {
  const r = await fetch(`${BASE}/categories/${telegramId}/${catId}`, { method: "DELETE", headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка удаления категории");
  return r.json();
}

/**
 * Обновить настройки уведомлений
 */
async function apiUpdateReminders(telegramId, enabled, timeStr) {
  const r = await fetch(`${BASE}/user/reminders`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" },
    body: JSON.stringify({ telegram_id: telegramId, enabled, time_str: timeStr }),
  });
  if (!r.ok) throw new Error("Ошибка обновления уведомлений");
  return r.json();
}

/**
 * Получить лимиты
 */
async function fetchLimits(telegramId) {
  const r = await fetch(`${BASE}/limits/${telegramId}`, { headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка получения лимитов");
  return r.json();
}

/**
 * Добавить/обновить лимит
 */
async function apiSetLimit(telegramId, category, amount) {
  const r = await fetch(`${BASE}/limits`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" },
    body: JSON.stringify({ telegram_id: telegramId, category, limit_amount: amount }),
  });
  if (!r.ok) throw new Error("Ошибка установки лимита");
  return r.json();
}

/**
 * Удалить лимит
 */
async function apiDeleteLimit(telegramId, limitId) {
  const r = await fetch(`${BASE}/limits/${telegramId}/${limitId}`, { method: "DELETE", headers: { "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" } });
  if (!r.ok) throw new Error("Ошибка удаления лимита");
  return r.json();
}

/**
 * Сбросить все данные пользователя
 */
async function apiResetData(telegramId) {
  const r = await fetch(`${BASE}/user/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "" },
    body: JSON.stringify({ telegram_id: telegramId }),
  });
  if (!r.ok) throw new Error("Ошибка сброса данных");
  return r.json();
}

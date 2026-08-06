"""
Минимальный manual.py — FSM для ручного ввода через чат.
Запускается кнопкой "➕ Добавить вручную".
"""
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from bot.services import db
import bot.config as cfg

router = Router()


class ManualForm(StatesGroup):
    choosing_type     = State()
    entering_amount   = State()
    choosing_category = State()


class BalanceForm(StatesGroup):
    waiting_amount = State()


EXPENSE_CATEGORIES = [
    ("🍽️ Еда", "Еда"), ("☕ Кафе", "Кафе/Ресторан"), ("🛒 Продукты", "Продукты"),
    ("🚌 Транспорт", "Транспорт"), ("🚕 Такси", "Такси"), ("👕 Одежда", "Одежда"),
    ("💊 Здоровье", "Здоровье"), ("🎬 Развлечения", "Развлечения"),
    ("📱 Связь", "Связь"), ("🏠 Коммунальные", "Коммунальные"), ("📌 Прочее", "Прочее"),
]
INCOME_CATEGORIES = [
    ("💼 Зарплата", "Зарплата"), ("💻 Фриланс", "Фриланс"), ("📌 Прочее", "Прочее"),
]


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def open_app_btn():
    if cfg.MINIAPP_URL:
        return [InlineKeyboardButton(text="📊 В приложении", web_app=WebAppInfo(url=cfg.MINIAPP_URL))]
    return []


def type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔴 Расход", callback_data="mtype:expense"),
            InlineKeyboardButton(text="🟢 Доход",  callback_data="mtype:income"),
        ],
        [InlineKeyboardButton(text="✕ Отмена", callback_data="mcancel")],
    ])


async def category_keyboard(tx_type: str, telegram_id: int):
    base_cats = EXPENSE_CATEGORIES if tx_type == "expense" else INCOME_CATEGORIES
    cats = list(base_cats)
    
    # Add custom categories
    custom_cats = await db.get_custom_categories(telegram_id)
    for c in custom_cats:
        if c["type"] == tx_type:
            cats.append((f'{c["icon"]} {c["name"]}', c["name"]))

    rows, row = [], []
    for label, value in cats:
        row.append(InlineKeyboardButton(text=label, callback_data=f"mcat:{value}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton(text="✕ Отмена", callback_data="mcancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard(tx_type, amount, category):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Сохранить", callback_data=f"msave:{tx_type}:{amount}:{category}"),
        InlineKeyboardButton(text="✕ Отмена",    callback_data="mcancel"),
    ]])


# ── Entry ─────────────────────────────────────────────────────

async def start_manual_add(message: Message, state: FSMContext):
    await state.set_state(ManualForm.choosing_type)
    await message.answer("Что добавляем?", reply_markup=type_keyboard())


@router.message(lambda m: m.text in ["➕ Добавить вручную", "➕ Qo'lda qo'shish"])
@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await start_manual_add(message, state)


# ── Step 1: Type ──────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("mtype:"))
async def cb_type(callback: CallbackQuery, state: FSMContext):
    tx_type = callback.data.split(":")[1]
    await state.update_data(tx_type=tx_type)
    await state.set_state(ManualForm.entering_amount)
    label = "расход" if tx_type == "expense" else "доход"
    await callback.message.edit_text(f"Сумма ({label}), в сумах:")
    await callback.answer()


# ── Step 2: Amount ────────────────────────────────────────────

@router.message(ManualForm.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "").replace(",", "")
    try:
        amount = float(raw)
        if amount <= 0: raise ValueError
    except ValueError:
        await message.answer("❌ Введи число, например `50000`")
        return
    await state.update_data(amount=amount)
    await state.set_state(ManualForm.choosing_category)
    data = await state.get_data()
    markup = await category_keyboard(data["tx_type"], message.from_user.id)
    await message.answer("Категория:", reply_markup=markup)


# ── Step 3: Category ──────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("mcat:"))
async def cb_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    data = await state.get_data()
    tx_type, amount = data["tx_type"], data["amount"]
    color = "🔴" if tx_type == "expense" else "🟢"
    await callback.message.edit_text(
        f"{color} {fmt(amount)} сум — {category}",
        reply_markup=confirm_keyboard(tx_type, amount, category)
    )
    await callback.answer()


# ── Step 4: Save ──────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("msave:"))
async def cb_save(callback: CallbackQuery, state: FSMContext):
    _, tx_type, amount_str, category = callback.data.split(":", 3)
    amount = float(amount_str)

    new_balance = await db.add_transaction(
        telegram_id=callback.from_user.id,
        data={"type": tx_type, "amount": amount, "category": category, "description": ""},
        raw_text=f"Вручную: {category}"
    )
    history = await db.get_history(callback.from_user.id, limit=1)
    tx_id = history[0].id if history else 0

    color = "🔴" if tx_type == "expense" else "🟢"
    sign  = "−" if tx_type == "expense" else "+"

    extra_btns = open_app_btn()
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="↩️ Отменить", callback_data=f"delete_tx:{tx_id}"),
        *extra_btns
    ]])

    limit_warning = ""
    if tx_type == "expense":
        is_exceeded, current, limit = await db.check_budget_limit(callback.from_user.id, category, amount)
        if is_exceeded:
            limit_warning = f"\n⚠️ *Превышен лимит!* ({fmt(current)} / {fmt(limit)})"

    await callback.message.edit_text(
        f"{color} {sign}{fmt(amount)} сум — {category}\n"
        f"Баланс: *{fmt(new_balance)} сум*{limit_warning}",
        reply_markup=markup
    )
    await state.clear()
    await callback.answer("Сохранено ✅")


# ── Cancel ────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "mcancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.")
    await callback.answer()


# ── Balance FSM ───────────────────────────────────────────────

@router.message(BalanceForm.waiting_amount)
async def process_set_balance(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "").replace(",", "")
    try:
        amount = float(raw)
        if amount < 0: raise ValueError
    except ValueError:
        await message.answer("❌ Введи число, например `1500000`")
        return
    new_balance = await db.set_balance(message.from_user.id, amount)
    await state.clear()
    extra = open_app_btn()
    markup = InlineKeyboardMarkup(inline_keyboard=[extra]) if extra else None
    await message.answer(f"✅ Баланс: *{fmt(new_balance)} сум*", reply_markup=markup)

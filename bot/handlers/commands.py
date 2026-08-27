"""
Минималистичный бот — только ввод данных.
Вся аналитика в Mini App.
"""
from aiogram import Router
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command
from bot.services import db
from bot.services.texts import get_text
import bot.config as cfg

router = Router()


# ── Keyboard helpers ──────────────────────────────────────────

def open_app_keyboard(lang: str = "ru", user_id: int = 0) -> InlineKeyboardMarkup | None:
    """Inline кнопка 'Открыть Balancy' — только если MINIAPP_URL задан."""
    if not cfg.MINIAPP_URL:
        return None
    base_url = cfg.MINIAPP_URL if cfg.MINIAPP_URL.endswith("index.html") else cfg.MINIAPP_URL.rstrip('/') + "/index.html"
    url = f"{base_url}?tg_id={user_id}&v=1050" if user_id else f"{base_url}?v=1050"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=get_text(lang, "btn_app"),
            web_app=WebAppInfo(url=url)
        )
    ]])

def input_keyboard(lang: str = "ru", user_id: int = 0) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    """Удаляем Reply-клавиатуру, так как Telegram не передает безопасную подпись через нее."""
    return ReplyKeyboardRemove()

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")]
    ])


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


# ── /start ────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    
    # Всегда запрашиваем язык при старте, либо только если не установлен
    await message.answer(
        "🌍 Выберите язык / Tilni tanlang:",
        reply_markup=language_keyboard()
    )


# ── /help ─────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    user = await db.get_or_create_user(message.from_user.id)
    lang = user.language or "ru"
    markup = open_app_keyboard(lang, user.telegram_id)
    await message.answer(get_text(lang, "help"), reply_markup=markup)


# ── /balance — быстрый ответ ──────────────────────────────────

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    user = await db.get_or_create_user(message.from_user.id)
    balance = user.balance
    lang = user.language or "ru"
    markup = open_app_keyboard(lang, user.telegram_id)
    await message.answer(
        f"💰 *{fmt(balance)} сум*",
        reply_markup=markup
    )


# ── /admin ───────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    # Если ADMIN_IDS пустой, позволяем первому вызвавшему стать админом в логах, 
    # либо просто используем ADMIN_IDS.
    if message.from_user.id not in cfg.ADMIN_IDS:
        # Для удобства настройки: если вы не настроили ID, бот подскажет его.
        if not cfg.ADMIN_IDS:
            await message.answer(f"⚠️ ADMIN_IDS не настроен в .env!\nВаш Telegram ID: `{message.from_user.id}`\nДобавьте его в .env файл на сервере: ADMIN_IDS={message.from_user.id}")
        return

    users_count = await db.get_total_users_count()
    await message.answer(
        f"🔧 *Панель администратора*\n\n"
        f"👥 Всего пользователей: {users_count}\n"
    )

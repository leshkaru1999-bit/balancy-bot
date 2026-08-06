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

def open_app_keyboard(lang: str = "ru") -> InlineKeyboardMarkup | None:
    """Inline кнопка 'Открыть Balancy' — только если MINIAPP_URL задан."""
    if not cfg.MINIAPP_URL:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=get_text(lang, "btn_app"),
            web_app=WebAppInfo(url=cfg.MINIAPP_URL)
        )
    ]])

def input_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    """Reply-клавиатура только с кнопкой Web App."""
    if not cfg.MINIAPP_URL:
        return ReplyKeyboardRemove()
        
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text=get_text(lang, "btn_app"),
                web_app=WebAppInfo(url=cfg.MINIAPP_URL)
            )
        ]],
        resize_keyboard=True,
        input_field_placeholder=get_text(lang, "placeholder"),
    )

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
    markup = open_app_keyboard(lang)
    await message.answer(get_text(lang, "help"), reply_markup=markup)


# ── /balance — быстрый ответ ──────────────────────────────────

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    user = await db.get_or_create_user(message.from_user.id)
    balance = user.balance
    lang = user.language or "ru"
    markup = open_app_keyboard(lang)
    await message.answer(
        f"💰 *{fmt(balance)} сум*",
        reply_markup=markup
    )

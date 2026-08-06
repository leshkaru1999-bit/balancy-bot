"""
Обработка голосовых и текстовых сообщений.
После сохранения — минимальный ответ + кнопка открыть приложение.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.services.whisper import voice_to_text
from bot.services.nlp import extract_transaction
from bot.services import db
import bot.config as cfg

router = Router()

CATEGORY_ICONS = {
    "Еда": "🍽️", "Кафе/Ресторан": "☕", "Транспорт": "🚌",
    "Такси": "🚕", "Продукты": "🛒", "Одежда": "👕",
    "Здоровье": "💊", "Развлечения": "🎬", "Зарплата": "💼",
    "Фриланс": "💻", "Связь": "📱", "Коммунальные": "🏠",
    "Прочее": "📌",
}

# Тексты кнопок которые НЕ нужно обрабатывать как транзакцию
SKIP_TEXTS = {"➕ Добавить вручную", "➕ Qo'lda qo'shish"}


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def result_keyboard(tx_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки после сохранения: Отменить + Открыть приложение."""
    text_cancel = "↩️ Отменить" if lang == "ru" else "↩️ Bekor qilish"
    buttons = [[
        InlineKeyboardButton(text=text_cancel, callback_data=f"delete_tx:{tx_id}"),
    ]]
    if cfg.MINIAPP_URL:
        from bot.services.texts import get_text
        buttons[0].append(
            InlineKeyboardButton(text=get_text(lang, "btn_app"), web_app=WebAppInfo(url=cfg.MINIAPP_URL))
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _save_and_reply(msg: Message, text: str, processing_msg=None):
    """Сохраняет транзакции и отправляет ответ."""
    user = await db.get_or_create_user(msg.from_user.id)
    lang = user.language or "ru"
    custom_categories = await db.get_custom_categories(msg.from_user.id)
    
    transactions = await extract_transaction(text, lang, custom_categories)
    
    new_balance = 0
    reply_lines = []
    
    for data in transactions:
        new_balance = await db.add_transaction(
            telegram_id=msg.from_user.id,
            data=data,
            raw_text=text,
        )
        
        icon  = CATEGORY_ICONS.get(data["category"], "📌")
        sign  = "−" if data["type"] == "expense" else "+"
        limit_warning = ""
        if data["type"] == "expense":
            is_exceeded, current, limit = await db.check_budget_limit(msg.from_user.id, data["category"], data["amount"])
            if is_exceeded:
                limit_warning = f"\n⚠️ *Превышен лимит!* ({fmt(current)} / {fmt(limit)})"
    
        color = "🔴" if data["type"] == "expense" else "🟢"
        reply_lines.append(f"{color} {sign}{fmt(data['amount'])} — {data['category']} {icon}{limit_warning}")

    history = await db.get_history(msg.from_user.id, limit=1)
    tx_id = history[0].id if history else 0

    text_balance = "Баланс" if lang == "ru" else "Balans"
    
    # Combine all lines
    reply = "\n".join(reply_lines) + f"\n\n{text_balance}: *{fmt(new_balance)}*"

    if processing_msg:
        await processing_msg.edit_text(reply, reply_markup=result_keyboard(tx_id, lang))
    else:
        await msg.answer(reply, reply_markup=result_keyboard(tx_id, lang))


# ── Голосовые ─────────────────────────────────────────────────

@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    user = await db.get_or_create_user(message.from_user.id)
    lang = user.language or "ru"
    has_premium = await db.is_premium(message.from_user.id)
    
    if not has_premium:
        from bot.services.texts import get_text
        from bot.handlers.commands import open_app_keyboard
        # Покажем клавиатуру покупки позже, но сейчас текст:
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium")
        ]])
        await message.answer(get_text(lang, "voice_premium_only"), reply_markup=markup)
        return

    processing_msg = await message.answer("🎙️")
    try:
        file = await bot.get_file(message.voice.file_id)
        file_url = f"https://api.telegram.org/file/bot{cfg.BOT_TOKEN}/{file.file_path}"
        text = await voice_to_text(file_url)
        await processing_msg.edit_text("🧠")
        await _save_and_reply(message, text, processing_msg)
    except ValueError:
        user = await db.get_or_create_user(message.from_user.id)
        lang = user.language or "ru"
        err_text = (
            "❓ Не понял. Скажи например:\n_«Потратил 50 тысяч на такси»_" 
            if lang == "ru" else 
            "❓ Tushunmadim. Masalan shunday deng:\n_«Taksiga 50 ming sarfladim»_"
        )
        await processing_msg.edit_text(err_text)
    except Exception as e:
        await processing_msg.edit_text(f"❌ Ошибка: `{str(e)[:80]}`")


# ── Текст ─────────────────────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    text = message.text.strip()
    if text in SKIP_TEXTS or len(text) < 4:
        return
    try:
        processing_msg = await message.answer("🧠")
        await _save_and_reply(message, text, processing_msg)
    except Exception:
        # Молча игнорируем если не похоже на финансовую запись
        pass

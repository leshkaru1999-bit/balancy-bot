from aiogram import Router, Bot, F
from aiogram.types import (
    Message, CallbackQuery, PreCheckoutQuery,
    LabeledPrice, SuccessfulPayment, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
import bot.config as cfg
from bot.services import db
from bot.services.texts import get_text
from datetime import datetime

router = Router()

# Для тестирования Telegram дает тестовые токены (Test token). 
# Пользователь позже должен вставить свой токен от Click/Payme.
PROVIDER_TOKEN = "" 

@router.callback_query(lambda c: c.data == "buy_premium")
async def cb_buy_premium(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    await send_payment_options(callback.message, callback.from_user.id)
    await callback.answer()

@router.message(Command("premium"))
async def cmd_premium(message: Message, bot: Bot):
    await send_payment_options(message, message.from_user.id)

async def send_payment_options(message: Message, telegram_id: int):
    user = await db.get_or_create_user(telegram_id)
    lang = user.language or "ru"

    text = "Выбери удобный способ оплаты:" if lang == "ru" else "To'lov usulini tanlang:"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Telegram Stars (150 ⭐️)", callback_data="invoice_stars")],
        [InlineKeyboardButton(text="💳 Uzcard / Humo (30 000 UZS)", callback_data="invoice_uzs")]
    ])
    await message.answer(text, reply_markup=markup)


@router.callback_query(lambda c: c.data in ["invoice_stars", "invoice_uzs"])
async def cb_send_invoice(callback: CallbackQuery, bot: Bot):
    method = callback.data.split("_")[1]
    user = await db.get_or_create_user(callback.from_user.id)
    lang = user.language or "ru"
    
    await callback.message.delete()

    if method == "uzs":
        if not PROVIDER_TOKEN:
            await callback.message.answer("⚠️ Оплата картой (Click/Payme) еще не настроена. Добавь `PROVIDER_TOKEN`.")
            return
        
        prices = [LabeledPrice(label=get_text(lang, "premium_invoice_title"), amount=3000000)] # 3000000 тийинов = 30000 сум
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=get_text(lang, "premium_invoice_title"),
            description=get_text(lang, "premium_invoice_desc"),
            payload="premium_1_month_uzs",
            provider_token=PROVIDER_TOKEN,
            currency="UZS",
            prices=prices,
            start_parameter="premium-subscription",
        )
    elif method == "stars":
        # Для оплаты звёздами provider_token должен быть пустым, а currency="XTR"
        prices = [LabeledPrice(label=get_text(lang, "premium_invoice_title"), amount=150)] # 150 звезд
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=get_text(lang, "premium_invoice_title"),
            description=get_text(lang, "premium_invoice_desc"),
            payload="premium_1_month_stars",
            provider_token="", # Обязательно пустая строка для Stars
            currency="XTR",
            prices=prices,
            start_parameter="premium-subscription-stars",
        )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user = await db.get_or_create_user(message.from_user.id)
    lang = user.language or "ru"
    
    # Выдаем премиум на 30 дней
    new_date = await db.add_premium_days(message.from_user.id, 30)
    
    date_str = new_date.strftime("%d.%m.%Y")
    text = get_text(lang, "premium_success", date=date_str)
    
    await message.answer(text)

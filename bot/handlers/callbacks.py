from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from bot.services import db
import bot.config as cfg

router = Router()


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def open_app_btn(lang: str = "ru"):
    if cfg.MINIAPP_URL:
        from bot.services.texts import get_text
        base_url = cfg.MINIAPP_URL if cfg.MINIAPP_URL.endswith("index.html") else cfg.MINIAPP_URL.rstrip('/') + "/index.html"
        return [InlineKeyboardButton(text=get_text(lang, "btn_app"), web_app=WebAppInfo(url=f"{base_url}?v=1050"))]
    return []


@router.callback_query(lambda c: c.data in ["lang_ru", "lang_uz"])
async def cb_language_selection(callback: CallbackQuery):
    lang = callback.data.split("_")[1]  # "ru" or "uz"
    await db.set_user_language(callback.from_user.id, lang)
    
    from bot.services.texts import get_text
    from bot.handlers.commands import input_keyboard, open_app_keyboard
    
    markup = open_app_keyboard(lang, callback.from_user.id)
    try:
        await callback.message.delete()
    except Exception:
        pass  # Сообщение уже удалено или недоступно — игнорируем
    
    if markup:
        await callback.message.answer(
            get_text(lang, "welcome", name=callback.from_user.first_name),
            reply_markup=markup
        )
    else:
        await callback.message.answer(
            get_text(lang, "welcome_no_app", name=callback.from_user.first_name)
        )
    
    await callback.answer(get_text(lang, "lang_selected"))


@router.callback_query(lambda c: c.data and c.data.startswith("delete_tx:"))
async def cb_delete_tx(callback: CallbackQuery):
    tx_id = int(callback.data.split(":")[1])
    success = await db.delete_transaction(tx_id)
    if success:
        user = await db.get_or_create_user(callback.from_user.id)
        balance = user.balance
        lang = user.language or "ru"
        extra = open_app_btn(lang)
        markup = InlineKeyboardMarkup(inline_keyboard=[extra]) if extra else None
        
        from bot.services.texts import get_text
        text_cancelled = "↩️ Отменено." if lang == "ru" else "↩️ Bekor qilindi."
        text_balance = "Баланс" if lang == "ru" else "Balans"
        text_deleted = "Удалено ✅" if lang == "ru" else "O'chirildi ✅"
        
        await callback.message.edit_text(
            f"{text_cancelled} {text_balance}: *{fmt(balance)}*",
            reply_markup=markup
        )
        await callback.answer(text_deleted)
    else:
        text_not_found = "Не найдено" if callback.data else "Topilmadi"
        await callback.answer(text_not_found, show_alert=True)


@router.callback_query(lambda c: c.data == "set_balance")
async def cb_set_balance(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.manual import BalanceForm
    await state.set_state(BalanceForm.waiting_amount)
    await callback.message.answer("Введи новый баланс (сум):")
    await callback.answer()


@router.callback_query(lambda c: c.data == "manual_add")
async def cb_manual_add(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.manual import start_manual_add
    await start_manual_add(callback.message, state)
    await callback.answer()

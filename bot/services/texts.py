TEXTS = {
    "ru": {
        "welcome": "Привет, {name}! 👋\n\nОтправь голосовое или напиши трату — я запишу.\nВся статистика в приложении 👇",
        "welcome_no_app": "Привет, {name}! 👋\n\nОтправь голосовое или напиши трату — я запишу.\n\n_Чтобы открыть дашборд, запусти ngrok и перезапусти бота._",
        "btn_add": "➕ Добавить вручную",
        "btn_app": "📊 Открыть Balancy",
        "placeholder": "🎙️ Или запиши голосовым...",
        "help": "🎙️ Скажи или напиши что потратил/получил:\n\n• _Такси 15 тысяч_\n• _Продукты 120к_\n• _Зарплата 5 миллионов_\n\nВсё остальное — в приложении.",
        "lang_selected": "🇷🇺 Выбран русский язык!",
        "voice_premium_only": "🎙️ Голосовой ввод доступен только по подписке Premium.\n\nС подпиской ты сможешь просто отправлять голосовые, а искусственный интеллект сам всё распознает и распределит по категориям!",
        "btn_buy_premium": "⭐️ Купить Premium (30 000 сум/мес)",
        "premium_invoice_title": "Balancy Premium ⭐️",
        "premium_invoice_desc": "Подписка на 1 месяц. Включает умный голосовой ввод и безлимитное использование ИИ.",
        "premium_success": "🎉 Спасибо за оплату!\n\nТвоя подписка Premium активна до: {date}.\nТеперь ты можешь отправлять голосовые сообщения 🎙️",
    },
    "uz": {
        "welcome": "Salom, {name}! 👋\n\nOvozli xabar yuboring yoki xarajatni yozing — men saqlayman.\nBarcha statistika ilovada 👇",
        "welcome_no_app": "Salom, {name}! 👋\n\nOvozli xabar yuboring yoki xarajatni yozing — men saqlayman.\n\n_Ilovani ochish uchun ngrok-ni ishga tushiring va botni qayta ishga tushiring._",
        "btn_add": "➕ Qo'lda qo'shish",
        "btn_app": "📊 Balancy-ni ochish",
        "placeholder": "🎙️ Yoki ovozli xabar qoldiring...",
        "help": "🎙️ Nimaga sarflaganingizni yoki olganingizni ayting/yozing:\n\n• _Taksi 15 ming_\n• _Oziq-ovqat 120k_\n• _Oylik 5 million_\n\nQolgan barchasi — ilovada.",
        "lang_selected": "🇺🇿 O'zbek tili tanlandi!",
        "voice_premium_only": "🎙️ Ovozli kiritish faqat Premium obunasi bilan mavjud.\n\nObuna bilan siz oddiygina ovozli xabar yuborishingiz mumkin, va sun'iy intellektning o'zi hammasini tanib, toifalarga ajratadi!",
        "btn_buy_premium": "⭐️ Premium sotib olish (30 000 so'm/oy)",
        "premium_invoice_title": "Balancy Premium ⭐️",
        "premium_invoice_desc": "1 oylik obuna. Aqlli ovozli kiritish va cheksiz AI foydalanishni o'z ichiga oladi.",
        "premium_success": "🎉 To'lov uchun rahmat!\n\nSizning Premium obunangiz {date} gacha faol.\nEndi siz ovozli xabarlar yuborishingiz mumkin 🎙️",
    }
}

def get_text(lang: str | None, key: str, **kwargs) -> str:
    lang = lang if lang in ["ru", "uz"] else "ru"
    text = TEXTS[lang].get(key, TEXTS["ru"].get(key, ""))
    return text.format(**kwargs) if kwargs else text

# Balancy 🤖💰

> Telegram-бот с Mini App для голосового учёта личных финансов

## Возможности

- 🎙️ **Голосовой ввод** — отправь голосовое, бот всё поймёт
- 🧠 **AI-распознавание** — Whisper STT + GPT-4o-mini NLP
- 📊 **Дашборд** — красивый Mini App внутри Telegram
- 💾 **PostgreSQL** — масштабируемая база данных
- 🌍 **Русский язык** — отлично понимает сленг и акценты

## Структура проекта

```
Balancy/
├── bot/                    # Telegram бот (Python + aiogram 3)
│   ├── main.py             # Точка входа
│   ├── config.py           # Конфиг из .env
│   ├── handlers/
│   │   ├── voice.py        # Обработка голоса/текста
│   │   ├── commands.py     # /start /balance /history /stats
│   │   └── callbacks.py    # Inline-кнопки
│   ├── services/
│   │   ├── whisper.py      # STT: голос → текст
│   │   ├── nlp.py          # NLP: текст → JSON
│   │   └── db.py           # CRUD операции
│   └── models/
│       └── database.py     # SQLAlchemy модели
├── miniapp/                # Telegram Mini App (HTML/CSS/JS)
│   ├── index.html
│   ├── css/style.css       # Glassmorphism UI
│   └── js/
│       ├── app.js          # Логика дашборда
│       └── api.js          # API запросы
├── .env.example            # Шаблон переменных
├── requirements.txt
└── README.md
```

## Быстрый старт

### 1. Клонируй и настрой окружение

```bash
cd Balancy
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Создай .env файл

```bash
copy .env.example .env
```

Заполни значения:
- `BOT_TOKEN` — получи у [@BotFather](https://t.me/BotFather)
- `OPENAI_API_KEY` — на [platform.openai.com](https://platform.openai.com/api-keys)
- `DATABASE_URL` — строка подключения PostgreSQL

### 3. Запусти PostgreSQL

```bash
# Через Docker (рекомендуется):
docker run -d --name balancy-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=balancy \
  -p 5432:5432 postgres:16
```

### 4. Запусти бота

```bash
cd bot
python main.py
```

## Команды бота

| Команда | Описание |
|---------|---------|
| `/start` | Запуск, приветствие |
| `/balance` | Текущий баланс |
| `/setbalance 1000000` | Установить начальный баланс |
| `/history` | Последние 10 транзакций |
| `/stats` | Статистика по категориям |
| 🎙️ Голосовое | Записать трату/доход |

## API ключи

| Ключ | Где взять | Для чего |
|------|----------|---------|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) | Сам бот |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) | Whisper STT + GPT-4o-mini NLP |

## Стек технологий

- **Python 3.11+** + **aiogram 3.x**
- **OpenAI Whisper** (STT)
- **GPT-4o-mini** (NLP)
- **PostgreSQL** + **SQLAlchemy 2.0** (async)
- **HTML/CSS/JS** (Mini App)

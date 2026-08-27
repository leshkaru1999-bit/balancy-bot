import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./balancy.db")
DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
MINIAPP_URL: str = os.getenv("MINIAPP_URL", "")  # ngrok URL + /miniapp
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")  # e.g., https://balancy.app/webhook
ADMIN_IDS: list[int] = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env файле!")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не задан в .env файле!")

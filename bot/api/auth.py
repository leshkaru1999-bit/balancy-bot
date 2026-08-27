import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from fastapi import Request, HTTPException, Depends
from bot.config import BOT_TOKEN

def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Проверяет валидность initData от Telegram Web App.
    Возвращает распаршенный словарь данных, если подпись верна, иначе выбрасывает ValueError.
    """
    if not init_data:
        raise ValueError("initData is empty")

    parsed_data = dict(parse_qsl(init_data))
    if "hash" not in parsed_data:
        raise ValueError("hash is missing")
    
    received_hash = parsed_data.pop("hash")
    
    # Сортируем ключи по алфавиту и собираем строку
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )
    
    # Создаем секретный ключ HMAC-SHA-256 от bot_token со строкой "WebAppData"
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    
    # Хешируем data_check_string с полученным ключом
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if calculated_hash != received_hash:
        raise ValueError("Invalid hash")
        
    return parsed_data

async def verify_telegram_auth(request: Request) -> dict:
    """
    FastAPI Dependency для проверки авторизации Mini App.
    Ожидает заголовок X-Telegram-Init-Data.
    Возвращает распаршенный JSON объекта user.
    """
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data header")
        
    try:
        parsed = verify_telegram_init_data(init_data, BOT_TOKEN)
        user_str = parsed.get("user")
        if not user_str:
            raise ValueError("No user data in initData")
        user = json.loads(user_str)
        return user
    except ValueError as e:
        raise HTTPException(status_code=403, detail=f"Invalid Telegram authentication: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=403, detail="Authentication failed")

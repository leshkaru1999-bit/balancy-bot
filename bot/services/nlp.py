import openai
import json
import re
from bot.config import OPENAI_API_KEY

client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

def get_system_prompt(lang: str, custom_cats_str: str) -> str:
    lang_name = "узбекском (или смешанном)" if lang == "uz" else "русском"
    return f"""
Ты — парсер финансовых записей. 
Пользователь описывает финансовую операцию голосом или текстом на {lang_name} языке.

Твоя задача: извлечь структурированные данные и вернуть ТОЛЬКО валидный JSON с массивом транзакций.

Важное правило: Категория и Тип ("type", "category", "description") всегда должны быть на РУССКОМ языке для базы данных, независимо от языка пользователя!

Правила для каждой транзакции:
- "amount": только число (целое или с точкой), в сумах. 
  На узбекском: "ming" (тысяч, *1000), "million" (миллион, *1_000_000). 
  На русском: "тысяч", "тыс", "тысяча" (*1000). "Миллион", "млн" (*1_000_000).
- "type": "income" (доход) или "expense" (расход).
- "category": категория СТРОГО НА РУССКОМ. Выбери наиболее подходящую категорию из следующего списка: Еда, Кафе/Ресторан, Транспорт, Такси, Продукты, Одежда, Здоровье, Развлечения, Зарплата, Фриланс, Связь, Коммунальные, Прочее, {custom_cats_str}
- "description": краткое описание (2-4 слова на РУССКОМ языке)

Верни ТОЛЬКО JSON в таком формате, без markdown:
{{"transactions": [{{"amount": ..., "type": "...", "category": "...", "description": "..."}}]}}
"""


async def extract_transaction(text: str, lang: str = "ru", custom_categories: list[dict] = None) -> list[dict]:
    """
    Отправляет распознанный текст в GPT-4o-mini.
    Возвращает список словарей с полями: type, amount, category, description.
    """
    custom_cats_str = ""
    if custom_categories:
        custom_cats_str = ", ".join([c["name"] for c in custom_categories])

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": get_system_prompt(lang, custom_cats_str)},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,  # Детерминированный результат для парсинга
        max_tokens=200
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    
    transactions = data.get("transactions", [])
    if not transactions:
        raise ValueError(f"GPT вернул пустой массив транзакций: {raw}")

    valid_txs = []
    for tx in transactions:
        # Валидация обязательных полей
        if "amount" not in tx or "type" not in tx:
            continue # пропускаем невалидные объекты
        
        try:
            tx["amount"] = float(tx["amount"])
        except ValueError:
            continue
            
        tx.setdefault("category", "Прочее")
        tx.setdefault("description", text[:50])
        valid_txs.append(tx)
        
    if not valid_txs:
        raise ValueError("Ни одна транзакция не прошла валидацию")

    return valid_txs

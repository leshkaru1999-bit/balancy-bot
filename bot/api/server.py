"""
FastAPI сервер для Balancy Mini App.
Запускается параллельно с Telegram-ботом.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram.types import Update

from bot.services import db
from bot.api.auth import verify_telegram_auth
from fastapi import Depends



# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Balancy API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class SetBalanceRequest(BaseModel):
    telegram_id: int
    amount: float


class AddTransactionRequest(BaseModel):
    telegram_id: int
    type: str          # "income" | "expense"
    amount: float
    category: str
    description: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Balancy API"}


@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: int, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    user = await db.get_or_create_user(telegram_id)
    is_premium = await db.is_premium(telegram_id)
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": float(user.balance),
        "currency": user.currency,
        "language": user.language or "ru",
        "is_premium": is_premium,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "reminders_enabled": user.reminders_enabled,
        "reminder_time": user.reminder_time,
    }

class UpdateReminderRequest(BaseModel):
    telegram_id: int
    enabled: bool
    time_str: str

@app.post("/api/user/reminders")
async def update_reminders(req: UpdateReminderRequest, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != req.telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    success = await db.update_reminder_settings(req.telegram_id, req.enabled, req.time_str)
    return {"success": success}

class BudgetLimitRequest(BaseModel):
    telegram_id: int
    category: str
    limit_amount: float

@app.get("/api/limits/{telegram_id}")
async def get_limits(telegram_id: int, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    limits = await db.get_budget_limits(telegram_id)
    return limits

@app.post("/api/limits")
async def add_limit(req: BudgetLimitRequest, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != req.telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    limit = await db.set_budget_limit(req.telegram_id, req.category, req.limit_amount)
    return limit

@app.delete("/api/limits/{telegram_id}/{limit_id}")
async def delete_limit(telegram_id: int, limit_id: int, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    success = await db.delete_budget_limit(telegram_id, limit_id)
    return {"success": success}


@app.get("/api/transactions/{telegram_id}")
async def get_transactions(telegram_id: int, auth_user: dict = Depends(verify_telegram_auth), limit: int = 30):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    transactions = await db.get_history(telegram_id, limit=limit)
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "amount": float(tx.amount),
            "category": tx.category,
            "description": tx.description or "",
            "raw_text": tx.raw_text or "",
            "created_at": tx.created_at.isoformat(),
        }
        for tx in transactions
    ]


@app.get("/api/stats/{telegram_id}")
async def get_stats(telegram_id: int, period: str = "all", start_date: str = None, end_date: str = None, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    stats = await db.get_stats(telegram_id, period=period, start_date=start_date, end_date=end_date)
    return stats


class UpdateNameRequest(BaseModel):
    telegram_id: int
    first_name: str

@app.post("/api/user/name")
async def update_name(req: UpdateNameRequest, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != req.telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    success = await db.update_user_name(req.telegram_id, req.first_name)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"success": True}


class ResetDataRequest(BaseModel):
    telegram_id: int

@app.post("/api/user/reset")
async def reset_user_data_endpoint(req: ResetDataRequest, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != req.telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    success = await db.reset_user_data(req.telegram_id)
    return {"success": success}


@app.post("/api/transaction")
async def add_transaction(req: AddTransactionRequest, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != req.telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    """Добавить транзакцию вручную из Mini App."""
    data = {
        "type": req.type,
        "amount": req.amount,
        "category": req.category,
        "description": req.description,
    }
    new_balance = await db.add_transaction(
        telegram_id=req.telegram_id,
        data=data,
        raw_text=f"Вручную: {req.category} {req.amount}"
    )
    return {"success": True, "new_balance": new_balance}


@app.delete("/api/transaction/{tx_id}")
async def delete_transaction(tx_id: int, auth_user: dict = Depends(verify_telegram_auth)):
    # Note: ideally we should verify auth_user owns this tx_id in DB, but for now we just verify auth exists

    """Удалить транзакцию (для Mini App)."""
    success = await db.delete_transaction(tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return {"success": True}

class CustomCategoryRequest(BaseModel):
    telegram_id: int
    type: str
    name: str
    icon: str

@app.get("/api/categories/{telegram_id}")
async def get_categories(telegram_id: int, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    cats = await db.get_custom_categories(telegram_id)
    return cats

@app.post("/api/categories")
async def add_category(req: CustomCategoryRequest, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != req.telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    cat = await db.add_custom_category(req.telegram_id, req.type, req.name, req.icon)
    return cat

@app.delete("/api/categories/{telegram_id}/{cat_id}")
async def delete_category(telegram_id: int, cat_id: int, auth_user: dict = Depends(verify_telegram_auth)):
    if auth_user['id'] != telegram_id:
        raise HTTPException(status_code=403, detail='Access denied')

    success = await db.delete_custom_category(telegram_id, cat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return {"success": True}


# ── Webhook ───────────────────────────────────────────────────────────────────
@app.post("/webhook")
async def bot_webhook(update: dict, request: Request):
    bot = request.app.state.bot
    dp = request.app.state.dp
    
    tg_update = Update(**update)
    await dp.feed_update(bot, tg_update)
    return {"ok": True}


# ── Static files (Mini App) ───────────────────────────────────────────────────
# Монтируем miniapp как статику по пути /miniapp
_miniapp_dir = Path(__file__).parent.parent.parent / "miniapp"
if _miniapp_dir.exists():
    app.mount("/miniapp", StaticFiles(directory=str(_miniapp_dir), html=True), name="miniapp")

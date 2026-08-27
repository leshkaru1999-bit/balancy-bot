"""Добавить delete_transaction в db.py"""
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.database import SessionLocal, User, Transaction, Category, CustomCategory, BudgetLimit
from decimal import Decimal


async def get_or_create_user(telegram_id: int, username: str | None = None, first_name: str | None = None) -> User:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name, balance=0)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def set_user_language(telegram_id: int, lang: str) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.language = lang
            await session.commit()
            return True
        return False

async def update_user_name(telegram_id: int, first_name: str) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.first_name = first_name
            await session.commit()
            return True
        return False


from datetime import datetime, timedelta

async def add_premium_days(telegram_id: int, days: int) -> datetime:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            # Если юзера нет, создадим
            user = User(telegram_id=telegram_id, balance=0)
            session.add(user)
        
        now = datetime.utcnow()
        if user.premium_until and user.premium_until > now:
            user.premium_until += timedelta(days=days)
        else:
            user.premium_until = now + timedelta(days=days)
        
        await session.commit()
        return user.premium_until

async def is_premium(telegram_id: int) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(select(User.premium_until).where(User.telegram_id == telegram_id))
        premium_until = result.scalar_one_or_none()
        if premium_until:
            # Учитываем таймзоны (если premium_until offset-aware или naive)
            # Если naive, сравниваем с utcnow
            # SQLAlchemy DateTime() может возвращать naive UTC
            return premium_until > datetime.utcnow()
        return False


async def set_balance(telegram_id: int, amount: float) -> float:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.balance = Decimal(str(amount))
            await session.commit()
            return float(user.balance)
        return 0.0


async def add_transaction(telegram_id: int, data: dict, raw_text: str = "") -> float:
    """Сохраняет транзакцию и обновляет баланс. Возвращает новый баланс."""
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return 0.0

        amount = Decimal(str(data["amount"]))
        if data["type"] == "expense":
            user.balance -= amount
        else:
            user.balance += amount

        tx = Transaction(
            user_id=telegram_id,
            type=data["type"],
            amount=amount,
            category=data.get("category", "Прочее"),
            description=data.get("description", ""),
            raw_text=raw_text,
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return float(user.balance)


async def get_balance(telegram_id: int) -> float:
    async with SessionLocal() as session:
        result = await session.execute(select(User.balance).where(User.telegram_id == telegram_id))
        balance = result.scalar_one_or_none()
        return float(balance) if balance is not None else 0.0


async def get_history(telegram_id: int, limit: int = 10) -> list[Transaction]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == telegram_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_stats(telegram_id: int, period: str = "all", start_date: str = None, end_date: str = None) -> list[dict]:
    """Статистика по категориям за выбранный период."""
    now = datetime.utcnow()
    query = select(Transaction.category, Transaction.type, func.sum(Transaction.amount)).where(Transaction.user_id == telegram_id)
    
    if period == "custom" and start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.where(Transaction.created_at >= start, Transaction.created_at <= end)
    elif period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(Transaction.created_at >= start)
    elif period == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(Transaction.created_at >= start)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.where(Transaction.created_at >= start)
        
    query = query.group_by(Transaction.category, Transaction.type)

    async with SessionLocal() as session:
        result = await session.execute(query)
        rows = result.all()
        return [{"category": r[0], "type": r[1], "total": float(r[2])} for r in rows]


async def delete_transaction(tx_id: int) -> bool:
    """Удаляет транзакцию по ID и откатывает баланс. Возвращает True если успешно."""
    async with SessionLocal() as session:
        result = await session.execute(select(Transaction).where(Transaction.id == tx_id))
        tx = result.scalar_one_or_none()
        if not tx:
            return False

        # Откат баланса
        user_result = await session.execute(select(User).where(User.telegram_id == tx.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            if tx.type == "expense":
                user.balance += tx.amount   # возвращаем потраченное
            else:
                user.balance -= tx.amount   # убираем добавленный доход

        await session.delete(tx)
        await session.commit()
        return True

async def reset_user_data(telegram_id: int) -> bool:
    """Удаляет все транзакции пользователя и обнуляет баланс."""
    async with SessionLocal() as session:
        # Удаляем все транзакции
        await session.execute(delete(Transaction).where(Transaction.user_id == telegram_id))
        
        # Обнуляем баланс
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.balance = 0
            
        await session.commit()
        return True
async def get_custom_categories(telegram_id: int) -> list[dict]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(CustomCategory).where(CustomCategory.user_id == telegram_id)
        )
        cats = result.scalars().all()
        return [{"id": c.id, "type": c.type, "name": c.name, "icon": c.icon} for c in cats]

async def add_custom_category(telegram_id: int, type: str, name: str, icon: str) -> dict:
    async with SessionLocal() as session:
        cat = CustomCategory(user_id=telegram_id, type=type, name=name, icon=icon)
        session.add(cat)
        await session.commit()
        await session.refresh(cat)
        return {"id": cat.id, "type": cat.type, "name": cat.name, "icon": cat.icon}

async def delete_custom_category(telegram_id: int, cat_id: int) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(
            select(CustomCategory).where(
                CustomCategory.id == cat_id,
                CustomCategory.user_id == telegram_id
            )
        )
        cat = result.scalar_one_or_none()
        if cat:
            await session.delete(cat)
            await session.commit()
            return True
        return False
async def update_reminder_settings(telegram_id: int, enabled: bool, time_str: str) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.reminders_enabled = enabled
            user.reminder_time = time_str
            await session.commit()
            return True
        return False

async def get_users_for_reminder(time_str: str) -> list[int]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(User.telegram_id)
            .where(User.reminders_enabled == True, User.reminder_time == time_str)
        )
        return list(result.scalars().all())

async def get_budget_limits(telegram_id: int) -> list[dict]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(BudgetLimit).where(BudgetLimit.user_id == telegram_id)
        )
        limits = result.scalars().all()
        return [{"id": l.id, "category": l.category, "limit_amount": float(l.limit_amount)} for l in limits]

async def set_budget_limit(telegram_id: int, category: str, limit_amount: float) -> dict:
    async with SessionLocal() as session:
        result = await session.execute(
            select(BudgetLimit).where(
                BudgetLimit.user_id == telegram_id,
                BudgetLimit.category == category
            )
        )
        limit = result.scalar_one_or_none()
        if limit:
            limit.limit_amount = Decimal(str(limit_amount))
        else:
            limit = BudgetLimit(user_id=telegram_id, category=category, limit_amount=Decimal(str(limit_amount)))
            session.add(limit)
        await session.commit()
        await session.refresh(limit)
        return {"id": limit.id, "category": limit.category, "limit_amount": float(limit.limit_amount)}

async def delete_budget_limit(telegram_id: int, limit_id: int) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(
            select(BudgetLimit).where(
                BudgetLimit.user_id == telegram_id,
                BudgetLimit.id == limit_id
            )
        )
        limit = result.scalar_one_or_none()
        if limit:
            await session.delete(limit)
            await session.commit()
            return True
        return False

async def check_budget_limit(telegram_id: int, category: str, amount_to_add: float) -> tuple[bool, float, float]:
    """Возвращает (is_exceeded, current_spent, limit_amount). Считает траты за ТЕКУЩИЙ МЕСЯЦ."""
    async with SessionLocal() as session:
        # Проверяем, есть ли лимит
        result = await session.execute(
            select(BudgetLimit.limit_amount).where(
                BudgetLimit.user_id == telegram_id,
                BudgetLimit.category == category
            )
        )
        limit_amount = result.scalar_one_or_none()
        if not limit_amount:
            return False, 0.0, 0.0
            
        # Считаем траты за месяц по этой категории
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == telegram_id,
                Transaction.category == category,
                Transaction.type == "expense",
                Transaction.created_at >= start_of_month
            )
        )
        spent_so_far = result.scalar_one_or_none() or Decimal(0)
        
        # Добавляем новую транзакцию
        total_spent = float(spent_so_far) + amount_to_add
        limit_float = float(limit_amount)
        
        return total_spent > limit_float, total_spent, limit_float


async def get_total_users_count() -> int:
    async with SessionLocal() as session:
        result = await session.execute(select(func.count(User.telegram_id)))
        return result.scalar() or 0

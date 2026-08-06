from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Numeric, DateTime, ForeignKey, CheckConstraint, Text, Integer
from datetime import datetime
from bot.config import DATABASE_URL


# SQLite: используем aiosqlite | PostgreSQL: asyncpg подключается автоматически
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    # telegram_id как PRIMARY KEY — уникальный и не требует autoincrement
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="UZS")
    language: Mapped[str | None] = mapped_column(String(5), default=None)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    reminders_enabled: Mapped[bool] = mapped_column(default=False)
    reminder_time: Mapped[str] = mapped_column(String(5), default="20:00")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BudgetLimit(Base):
    __tablename__ = "budget_limits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    limit_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('income', 'expense')", name="chk_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    type: Mapped[str] = mapped_column(String(10)) # expense, income


class CustomCategory(Base):
    __tablename__ = "custom_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    type: Mapped[str] = mapped_column(String(10)) # expense, income
    name: Mapped[str] = mapped_column(String(50))
    icon: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    """Создаёт все таблицы в БД (безопасно — не падает если таблицы уже есть)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

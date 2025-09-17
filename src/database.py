"""
Модели базы данных и функции для работы с ними
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config.settings import DATABASE_URL
import enum

Base = declarative_base()

class BetStatus(enum.Enum):
    """Статусы ставок"""
    PENDING = "pending"  # В ожидании
    WON = "won"         # Выиграна
    LOST = "lost"       # Проиграна
    CANCELLED = "cancelled"  # Отменена

class EventStatus(enum.Enum):
    """Статусы событий"""
    UPCOMING = "upcoming"    # Предстоящее
    LIVE = "live"           # В процессе
    FINISHED = "finished"   # Завершено
    CANCELLED = "cancelled" # Отменено

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)  # Telegram user ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    balance = Column(Float, default=1000.0)  # Начальный баланс
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Связи
    bets = relationship("Bet", back_populates="user")

class Event(Base):
    """Модель события для ставок"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(Enum(EventStatus), default=EventStatus.UPCOMING)
    created_by = Column(Integer, nullable=False)  # ID админа, создавшего событие
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Связи
    outcomes = relationship("Outcome", back_populates="event", cascade="all, delete-orphan")
    bets = relationship("Bet", back_populates="event")

class Outcome(Base):
    """Модель исхода события"""
    __tablename__ = 'outcomes'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    title = Column(String(255), nullable=False)  # Например: "Победа команды А", "Ничья"
    odds = Column(Float, nullable=False)  # Коэффициент
    is_winning = Column(Boolean, nullable=True)  # True если исход выиграл, False если проиграл, None если не определен
    total_amount = Column(Float, default=0.0)  # Общая сумма ставок на этот исход
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Связи
    event = relationship("Event", back_populates="outcomes")
    bets = relationship("Bet", back_populates="outcome")

class Bet(Base):
    """Модель ставки"""
    __tablename__ = 'bets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    outcome_id = Column(Integer, ForeignKey('outcomes.id'), nullable=False)
    amount = Column(Float, nullable=False)  # Сумма ставки
    odds = Column(Float, nullable=False)    # Коэффициент на момент ставки
    potential_win = Column(Float, nullable=False)  # Потенциальный выигрыш
    status = Column(Enum(BetStatus), default=BetStatus.PENDING)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Связи
    user = relationship("User", back_populates="bets")
    event = relationship("Event", back_populates="bets")
    outcome = relationship("Outcome", back_populates="bets")

# Настройка подключения к базе данных
if DATABASE_URL.startswith('sqlite'):
    # Для SQLite используем синхронный движок
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    def get_db():
        db = SessionLocal()
        try:
            return db
        finally:
            db.close()
else:
    # Для PostgreSQL используем асинхронный движок
    async_engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession)
    
    async def get_async_db():
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

async def init_db():
    """Инициализация базы данных"""
    if DATABASE_URL.startswith('sqlite'):
        # Синхронная инициализация для SQLite
        Base.metadata.create_all(bind=engine)
    else:
        # Асинхронная инициализация для PostgreSQL
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

# Функции для работы с пользователями
async def get_user(user_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        return db.query(User).filter(User.user_id == user_id).first()
    else:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()

async def create_user(user_id: int, username: str, first_name: str, last_name: str = None) -> User:
    """Создать нового пользователя"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    else:
        async with AsyncSessionLocal() as session:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

async def update_user_balance(user_id: int, amount: float) -> bool:
    """Обновить баланс пользователя"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.balance += amount
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False
    else:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.balance += amount
                user.updated_at = datetime.now(timezone.utc)
                await session.commit()
                return True
            return False

# Функции для работы с событиями
async def get_active_events() -> List[Event]:
    """Получить активные события"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        return db.query(Event).filter(
            Event.status.in_([EventStatus.UPCOMING, EventStatus.LIVE])
        ).all()
    else:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Event).where(
                    Event.status.in_([EventStatus.UPCOMING, EventStatus.LIVE])
                )
            )
            return result.scalars().all()

async def get_event_by_id(event_id: int) -> Optional[Event]:
    """Получить событие по ID"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        return db.query(Event).filter(Event.id == event_id).first()
    else:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Event).where(Event.id == event_id)
            )
            return result.scalar_one_or_none()

async def create_event(title: str, description: str, start_time: datetime, created_by: int) -> Event:
    """Создать новое событие"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        event = Event(
            title=title,
            description=description,
            start_time=start_time,
            created_by=created_by
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    else:
        async with AsyncSessionLocal() as session:
            event = Event(
                title=title,
                description=description,
                start_time=start_time,
                created_by=created_by
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

# Функции для работы со ставками
async def get_user_bets(user_id: int) -> List[Bet]:
    """Получить ставки пользователя"""
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        return db.query(Bet).filter(Bet.user_id == user_id).all()
    else:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Bet).where(Bet.user_id == user_id)
            )
            return result.scalars().all()

async def create_bet(user_id: int, event_id: int, outcome_id: int, amount: float, odds: float) -> Optional[Bet]:
    """Создать новую ставку"""
    # Проверяем баланс пользователя
    user = await get_user(user_id)
    if not user or user.balance < amount:
        return None
    
    potential_win = amount * odds
    
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        
        # Создаем ставку
        bet = Bet(
            user_id=user_id,
            event_id=event_id,
            outcome_id=outcome_id,
            amount=amount,
            odds=odds,
            potential_win=potential_win
        )
        
        # Обновляем баланс пользователя
        user.balance -= amount
        user.updated_at = datetime.now(timezone.utc)
        
        # Обновляем общую сумму ставок на исход
        outcome = db.query(Outcome).filter(Outcome.id == outcome_id).first()
        if outcome:
            outcome.total_amount += amount
            outcome.updated_at = datetime.now(timezone.utc)
        
        db.add(bet)
        db.commit()
        db.refresh(bet)
        return bet
    else:
        async with AsyncSessionLocal() as session:
            # Создаем ставку
            bet = Bet(
                user_id=user_id,
                event_id=event_id,
                outcome_id=outcome_id,
                amount=amount,
                odds=odds,
                potential_win=potential_win
            )
            
            # Обновляем баланс пользователя
            user.balance -= amount
            user.updated_at = datetime.now(timezone.utc)
            
            # Обновляем общую сумму ставок на исход
            outcome_result = await session.execute(
                select(Outcome).where(Outcome.id == outcome_id)
            )
            outcome = outcome_result.scalar_one_or_none()
            if outcome:
                outcome.total_amount += amount
                outcome.updated_at = datetime.now(timezone.utc)
            
            session.add(bet)
            await session.commit()
            await session.refresh(bet)
            return bet

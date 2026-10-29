import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, ForeignKey, DateTime, Float, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///./development.db'), pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
def db_session():
    with SessionLocal() as session:
        yield session

class User(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class LoginSession(Base):
    __tablename__='sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
class Field(Base):
    __tablename__='fields'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(100))
    crop: Mapped[str] = mapped_column(String(100))
    area: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String(200), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Scan(Base):
    __tablename__='scans'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    field_id: Mapped[int | None] = mapped_column(ForeignKey('fields.id'), nullable=True, index=True)
    image_key: Mapped[str] = mapped_column(String(80))
    notes: Mapped[str] = mapped_column(String(2000), default='')
    prediction: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Followup(Base):
    __tablename__='followups'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey('scans.id'))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)

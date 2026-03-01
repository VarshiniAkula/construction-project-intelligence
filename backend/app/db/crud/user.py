from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.user import User
from app.core.security import get_password_hash


class UserCRUD:
    def get(self, db: Session, user_id: str) -> User | None:
        return db.get(User, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalars().first()

    def create(self, db: Session, *, email: str, password: str, full_name: str | None = None) -> User:
        u = User(email=email.lower().strip(), hashed_password=get_password_hash(password), full_name=full_name)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u


user = UserCRUD()

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate

async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> Optional[User]:
    """
    Retrieve a user by their Firebase UID.
    """
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Retrieve a user by their email address.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Create a new User locally in the database.
    """
    db_user = User(
        firebase_uid=user_in.firebase_uid,
        email=user_in.email,
        full_name=user_in.full_name,
        photo_url=user_in.photo_url,
        role=user_in.role or "student",
        status="active",
        origin=user_in.origin or "external_user",
        is_verified=user_in.is_verified or False,
        last_login=func.now()
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, firebase_uid: str, user_in: UserUpdate) -> Optional[User]:
    """
    Update user metadata (full name, photo, status, roles).
    """
    db_user = await get_user_by_firebase_uid(db, firebase_uid)
    if not db_user:
        return None

    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user

import asyncio
from sqlalchemy import select
from app.database.session import SessionLocal

# Import all models to register them with SQLAlchemy
from app.users.models import User
from app.students.models import StudentProfile
from app.organizations.models import Organization
from app.programs.models import Program
from app.applications.models import Application, ApplicationStatusHistory
from app.documents.models import Document

async def main():
    async with SessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"Total users in DB: {len(users)}")
        for u in users:
            print(f"ID: {u.id} | Email: {u.email} | Firebase UID: {u.firebase_uid} | Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(main())

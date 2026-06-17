import asyncio
from sqlalchemy import text
from app.database.session import SessionLocal

async def check_programs():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT id, title, is_active FROM programs"))
        programs = result.fetchall()
        for p in programs:
            print(f"ID: {p.id}, Title: {p.title}, Active: {p.is_active}")

if __name__ == "__main__":
    asyncio.run(check_programs())

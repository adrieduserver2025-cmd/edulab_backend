import asyncio
from sqlalchemy import text
from app.database.session import SessionLocal

async def remove_test_program():
    async with SessionLocal() as session:
        query = text("DELETE FROM programs WHERE title LIKE '%Test Dinamica%'")
        await session.execute(query)
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(remove_test_program())

import asyncio
from sqlalchemy import delete
from app.database.session import SessionLocal
from app.programs.models import Program
from app.main import seed_programs_db

async def cleanup():
    async with SessionLocal() as db:
        print("Cleaning up program 'beca-test-dinamica'...")
        await db.execute(delete(Program).where(Program.slug == "beca-test-dinamica"))
        await db.commit()
    print("Re-running database seeding...")
    await seed_programs_db()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(cleanup())

import asyncio
import logging
from app.main import seed_programs_db

logging.basicConfig(level=logging.INFO)

async def main():
    print("Running seed_programs_db...")
    await seed_programs_db()
    print("Seeding finished!")

if __name__ == "__main__":
    asyncio.run(main())

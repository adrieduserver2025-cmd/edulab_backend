import asyncio
from pydantic import BaseModel
import app.main # This triggers all model registrations

async def main():
    from app.database.session import SessionLocal
    from app.users.models import User
    from sqlalchemy import select
    
    async with SessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        if not user:
            print("No users found.")
            return

    print(f"Testing application creation logic for user {user.id} ({user.email})...")
    from app.applications.router import start_application
    from app.applications.router import ApplicationCreate
    
    payload = ApplicationCreate(
        program_id=10,
        answers=[],
        uploaded_documents={}
    )
    
    async with SessionLocal() as session:
        try:
            app_result = await start_application(
                payload=payload,
                db=session,
                current_user=user
            )
            print("Success:", app_result)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

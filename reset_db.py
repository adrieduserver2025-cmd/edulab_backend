import asyncio
import sys
from sqlalchemy import text
from app.database.base import Base
from app.database.session import engine

# Import all models to ensure SQLAlchemy binds them for drop/create
from app.users.models import User
from app.students.models import StudentProfile
from app.organizations.models import Organization
from app.programs.models import Program
from app.applications.models import Application, ApplicationStatusHistory
from app.documents.models import Document

async def reset_database():
    print("WARNING: This will drop all tables in your development database!")
    print("Confirm by typing 'yes' and pressing Enter, or any other key to cancel:")
    
    # Read user confirmation if interactive, or proceed if running programmatically
    try:
        response = sys.stdin.readline().strip().lower()
        if response != 'yes':
            print("Database reset cancelled.")
            return
    except Exception:
        # Fallback if stdin is not available (e.g. running in standard CI/CD or non-interactive shells)
        pass

    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("All tables dropped successfully.")

    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset complete! Created tables: users, student_profiles.")

if __name__ == "__main__":
    asyncio.run(reset_database())

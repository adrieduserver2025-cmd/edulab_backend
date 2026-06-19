import asyncio
import json
import datetime
from sqlalchemy import select
from app.database.session import SessionLocal
from app.database.base import Base

# Import all models to ensure they are registered
from app.users.models import User
from app.students.models import StudentProfile
from app.organizations.models import Organization
from app.programs.models import Program
from app.applications.models import Application, ApplicationStatusHistory
from app.documents.models import Document

# Serialization helper
def serialize_val(val):
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    if isinstance(val, (list, dict)):
        return val
    return val

async def export_data():
    print("⏳ Iniciando exportación de datos locales...")
    
    # Order of tables to fetch
    models = [
        ("User", User),
        ("Organization", Organization),
        ("StudentProfile", StudentProfile),
        ("Program", Program),
        ("Application", Application),
        ("ApplicationStatusHistory", ApplicationStatusHistory),
        ("Document", Document)
    ]
    
    backup_data = {}
    
    async with SessionLocal() as db:
        for name, model in models:
            print(f"Reading {name} table...")
            result = await db.execute(select(model))
            instances = result.scalars().all()
            
            records = []
            for inst in instances:
                # Convert model instance columns to a dictionary
                record = {}
                for col in model.__table__.columns:
                    val = getattr(inst, col.name)
                    record[col.name] = serialize_val(val)
                records.append(record)
                
            backup_data[name] = records
            print(f"✅ Read {len(records)} records from {name}.")
            
    with open("db_backup.json", "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
    print("\n🎉 Exportación completada con éxito!")
    print("El archivo de copia de seguridad se ha guardado como 'db_backup.json'.")
    print("Copia este archivo 'db_backup.json' a tu otra laptop en la misma carpeta.")

if __name__ == "__main__":
    asyncio.run(export_data())

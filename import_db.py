import asyncio
import json
import datetime
import os
from sqlalchemy import select
from sqlalchemy.types import Date, DateTime
from app.database.session import SessionLocal, engine
from app.database.base import Base

# Import all models to ensure they are registered
from app.users.models import User
from app.students.models import StudentProfile
from app.organizations.models import Organization
from app.programs.models import Program
from app.applications.models import Application, ApplicationStatusHistory
from app.documents.models import Document

# Deserialization helper
def deserialize_val(val, col_type):
    if val is None:
        return None
    if isinstance(col_type, DateTime):
        # Handle cases where there might be a 'Z' at the end or microsecond mismatch
        # fromisoformat handles standard ISO strings
        val_str = val.replace('Z', '+00:00') if isinstance(val, str) else val
        return datetime.datetime.fromisoformat(val_str)
    if isinstance(col_type, Date):
        return datetime.date.fromisoformat(val)
    return val

async def import_data():
    if not os.path.exists("db_backup.json"):
        print("❌ Error: No se encontró el archivo 'db_backup.json' en este directorio.")
        print("Asegúrate de copiarlo desde tu otra laptop a esta misma carpeta.")
        return

    print("⚠️ ADVERTENCIA: Este script restaurará la base de datos local.")
    print("Para evitar errores de duplicación, se recomienda limpiar las tablas existentes.")
    print("¿Deseas vaciar y recrear la base de datos antes de importar? (escribe 'yes' para limpiar, o presiona Enter para intentar importar directamente):")
    
    try:
        import sys
        confirm = sys.stdin.readline().strip().lower()
    except Exception:
        confirm = ""
        
    if confirm == "yes":
        print("Dropping all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Base de datos recreada y vacía.")
    else:
        print("⚠️ Continuando sin limpiar la base de datos (podrían ocurrir errores de clave duplicada).")

    with open("db_backup.json", "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    # Order of tables to write
    models = [
        ("User", User),
        ("Organization", Organization),
        ("StudentProfile", StudentProfile),
        ("Program", Program),
        ("Application", Application),
        ("ApplicationStatusHistory", ApplicationStatusHistory),
        ("Document", Document)
    ]

    async with SessionLocal() as db:
        for name, model in models:
            records = backup_data.get(name, [])
            if not records:
                print(f"No records to import for {name}.")
                continue
                
            print(f"Importing {len(records)} records into {name}...")
            
            for rec in records:
                # Convert rec dictionary into dict of parsed model parameters
                model_kwargs = {}
                for col in model.__table__.columns:
                    if col.name in rec:
                        val = rec[col.name]
                        model_kwargs[col.name] = deserialize_val(val, col.type)
                
                # Create instance
                instance = model(**model_kwargs)
                db.add(instance)
            
            # Flush after each table to maintain foreign key integrity
            await db.flush()
            print(f"✅ Imported {name} successfully.")
            
        await db.commit()
        
    print("\n🎉 Restauración completada con éxito!")

if __name__ == "__main__":
    asyncio.run(import_data())

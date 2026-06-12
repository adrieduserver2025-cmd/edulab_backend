import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.firebase import initialize_firebase
from app.api.v1.router import router as api_v1_router
from app.database.base import Base
from app.database.session import engine

# Explicitly import all models to register them with Base.metadata on startup
from app.users.models import User
from app.students.models import StudentProfile
from app.programs.models import Program
from app.applications.models import Application, ApplicationStatusHistory
from app.documents.models import Document
from app.organizations.models import Organization

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

async def seed_programs_db():
    from app.database.session import SessionLocal
    from app.programs.models import Program
    from sqlalchemy import select

    logger.info("🌱 Seeding database programs/opportunities...")
    
    seeds = [
        {
            "title": "Beca de Excelencia Global DAAD Alemania",
            "description": "Beca completa para estudios de Master y Doctorado en universidades alemanas.",
            "type": "scholarship",
            "organization": "Servicio Alemán de Intercambio Académico (DAAD)",
            "country": "Alemania",
            "deadline": datetime.date(2026, 10, 15),
            "eligibility": "Graduados universitarios con excelente promedio académico.",
            "benefits": "Matrícula completa, estipendio mensual de €1200 y seguro médico.",
            "slots": 15,
            "slug": "daad-beca",
            "organization_name": "DAAD",
            "status": "open",
            "short_description": "Estudia tu postgrado gratis en Alemania con financiamiento completo.",
            "activities": ["Estudio académico", "Investigación", "Prácticas profesionales"],
            "requirements": ["Promedio mayor a 8.5", "Nivel de inglés B2 o alemán B1", "Título universitario"],
            "benefits_json": ["Matrícula cubierta", "Beca mensual de 1200 euros", "Seguro médico y de viaje"],
            "dates_info": "Convocatoria anual con límite en Octubre 2026",
            "support_ai": ["Evaluación de CV", "Revisión de propuesta de investigación"],
            "facebook_url": "https://www.facebook.com/DAAD.Worldwide",
            "instagram_url": "https://www.instagram.com/daad_worldwide/",
            "youtube_url": "https://www.youtube.com/@DAADWorldwide",
            "video_url": "https://www.youtube.com/watch?v=daad-video",
            "image_url": "/assets/images/daad.png",
            "is_demo": True
        },
        {
            "title": "Summer School en Liderazgo y Sostenibilidad Oxford",
            "description": "Programa intensivo de verano enfocado en políticas ambientales globales.",
            "type": "summer_school",
            "organization": "University of Oxford",
            "country": "Reino Unido",
            "deadline": datetime.date(2026, 6, 30),
            "eligibility": "Estudiantes de grado con interés en sostenibilidad y liderazgo.",
            "benefits": "Alojamiento, alimentación y pase de biblioteca.",
            "slots": 25,
            "slug": "oxford-summer-school",
            "organization_name": "University of Oxford",
            "status": "open",
            "short_description": "Curso intensivo de verano sobre liderazgo ambiental en Oxford.",
            "activities": ["Conferencias académicas", "Visitas de campo", "Grupos de debate"],
            "requirements": ["Estudiante activo de grado", "Inglés fluido C1", "Ensayo de motivación"],
            "benefits_json": ["Alojamiento en campus", "Alimentación completa", "Certificado de Oxford"],
            "dates_info": "Salida en Julio 2026, límite de aplicación en Junio",
            "support_ai": ["Redacción de ensayo con IA", "Preparación de entrevista rápida"],
            "facebook_url": "https://www.facebook.com/the.university.of.oxford",
            "instagram_url": "https://www.instagram.com/oxford_uni/",
            "youtube_url": "https://www.youtube.com/@oxford",
            "video_url": "https://www.youtube.com/watch?v=oxford-video",
            "image_url": "/assets/images/oxford.png",
            "is_demo": True
        },
        {
            "title": "Intercambio Académico Global U-Tokyo",
            "description": "Semestre académico en ingeniería o ciencias computacionales.",
            "type": "exchange",
            "organization": "University of Tokyo",
            "country": "Japón",
            "deadline": datetime.date(2026, 8, 1),
            "eligibility": "Estudiantes de ciencias e ingeniería de universidades socias.",
            "benefits": "Exención de matrícula académica y apoyo de instalación.",
            "slots": 10,
            "slug": "u-tokyo-exchange",
            "organization_name": "University of Tokyo",
            "status": "open",
            "short_description": "Cursa un semestre en una de las mejores universidades asiáticas.",
            "activities": ["Clases presenciales", "Investigación en laboratorio", "Inmersión cultural"],
            "requirements": ["Tener aprobado el 50% de la carrera", "Inglés B2 o japonés N3", "Carta de recomendación"],
            "benefits_json": ["Exención de matrícula", "Subsidio de instalación", "Acceso a bibliotecas"],
            "dates_info": "Semestre de Otoño 2026, aplicación hasta Agosto",
            "support_ai": ["Matching inteligente de asignaturas", "Revisión de CV en inglés"],
            "facebook_url": "https://www.facebook.com/UTokyo.News",
            "instagram_url": "https://www.instagram.com/utokyo/",
            "youtube_url": "https://www.youtube.com/@utokyo",
            "video_url": "https://www.youtube.com/watch?v=tokyo-video",
            "image_url": "/assets/images/tokyo.png",
            "is_demo": True
        },
        {
            "title": "Voluntariado en AIESEC",
            "description": "El voluntariado de AIESEC es una experiencia internacional de corta duración que permite a jóvenes participar en proyectos sociales en distintos países, con el objetivo de generar impacto positivo en comunidades mientras desarrollan habilidades personales y profesionales.\n\nMás allá del trabajo voluntario, AIESEC busca formar líderes globales. Durante el programa, los jóvenes fortalecen competencias como comunicación intercultural, trabajo en equipo, adaptabilidad y resolución de problemas en entornos reales.\n\nAdemás, el voluntariado incluye acompañamiento antes, durante y después de la experiencia, así como espacios de integración cultural que permiten al participante sumergirse en la realidad del país anfitrión.",
            "type": "volunteering",
            "organization": "AIESEC International",
            "country": "Global",
            "deadline": datetime.date(2026, 9, 30),
            "eligibility": "Jóvenes entre 18 y 30 años con ganas de generar impacto social.",
            "benefits": "Hospedaje local, desarrollo de liderazgo y certificado internacional.",
            "slots": 50,
            "slug": "aiesec-voluntariado",
            "organization_name": "AIESEC",
            "status": "open",
            "short_description": "Vive una experiencia internacional que transforma tu forma de ver el mundo.",
            "activities": [
                "Enseñanza en comunidades 📚",
                "Proyectos sociales 🤝",
                "Campañas ambientales 🌱",
                "Actividades interculturales 🌍"
            ],
            "requirements": [
                "Tener entre 18 y 30 años",
                "Interés en voluntariado internacional",
                "Nivel básico/intermedio de inglés",
                "Disponibilidad para viajar"
            ],
            "benefits_json": [
                "Experiencia internacional 🌍",
                "Desarrollo de liderazgo 🧠",
                "Red global de contactos 🤝",
                "Certificado internacional 📜"
            ],
            "dates_info": "Convocatoria: Abierta durante el año | Salidas: Según proyecto",
            "support_ai": [
                "Elegir el mejor voluntariado según el perfil del usuario",
                "Preparar la aplicación",
                "Redactar carta de motivación con IA"
            ],
            "facebook_url": "https://www.facebook.com/AIESECglobal",
            "instagram_url": "https://www.instagram.com/aiesecglobal/",
            "youtube_url": "https://www.youtube.com/@aiesecglobal",
            "video_url": "https://www.youtube.com/watch?v=7h43WCAVXdY",
            "image_url": "/assets/images/aiesec_hero.jpg",
            "is_demo": False
        },
        {
            "title": "Voluntariado de Conservación Ambiental ONU",
            "description": "Apoyo en áreas protegidas para reforestación, educación ecológica y monitoreo de especies nativas.",
            "type": "volunteering",
            "organization": "Voluntarios de las Naciones Unidas (VNU)",
            "country": "Costa Rica",
            "deadline": datetime.date(2026, 11, 15),
            "eligibility": "Jóvenes mayores de 18 años con estudios o interés afín en ecología/medioambiente.",
            "benefits": "Alojamiento, subsidio de alimentación y cobertura médica.",
            "slots": 15,
            "slug": "onu-voluntariado",
            "organization_name": "ONU",
            "status": "open",
            "short_description": "Protege la biodiversidad de Costa Rica como voluntario de las Naciones Unidas.",
            "activities": ["Monitoreo de especies", "Planes de reforestación", "Charlas de educación ecológica"],
            "requirements": ["Tener al menos 18 años", "Interés genuino en conservación ecológica", "Inglés o español intermedio"],
            "benefits_json": ["Alojamiento local", "Subsidio mensual para alimentación", "Seguro médico de las Naciones Unidas"],
            "dates_info": "Inicio Noviembre 2026, límite de registro 15 de Noviembre",
            "support_ai": ["Redacción de carta de interés", "Revisión de CV internacional"],
            "facebook_url": "https://www.facebook.com/unvolunteers",
            "instagram_url": "https://www.instagram.com/unvolunteers/",
            "youtube_url": "https://www.youtube.com/@UNVolunteersVideo",
            "video_url": "https://www.youtube.com/watch?v=onu-video",
            "image_url": "/assets/images/un_volunteering.jpg",
            "is_demo": True
        }
    ]

    async with SessionLocal() as db:
        for seed_data in seeds:
            result = await db.execute(
                select(Program).where(Program.slug == seed_data["slug"])
            )
            existing = result.scalars().first()
            if not existing:
                new_program = Program(**seed_data)
                db.add(new_program)
                logger.info(f"Added seed program: '{seed_data['title']}' ({seed_data['slug']})")
        await db.commit()
    logger.info("🌱 Database programs/opportunities seeding finished successfully.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing Firebase Admin SDK...")
    initialize_firebase()

    if settings.DEV_MODE:
        logger.info("🔧 DEV_MODE active: Ensuring database tables exist...")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables initialized successfully.")
            # Run database seeding
            await seed_programs_db()
        except Exception as e:
            logger.error(f"❌ Failed to auto-initialize database tables: {e}")
            logger.warning("Make sure PostgreSQL is running, or DATABASE_URL is configured correctly.")

    yield
    # Shutdown actions (if any)
    logger.info("Stopping EDULAB Application Server...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="EDULAB - Intelligent Educational Opportunities SaaS API",
    version="1.0.0",
    lifespan=lifespan
)

# Apply CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register main API router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Standard JSON endpoint for systems monitoring.
    """
    db_ok = False
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    return {
        "status": "healthy" if db_ok else "degraded",
        "project": settings.PROJECT_NAME,
        "database": "connected" if db_ok else "disconnected",
        "firebase_mode": "mock_dev" if not settings.FIREBASE_CREDENTIALS_JSON and not settings.FIREBASE_CREDENTIALS_PATH else "production"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

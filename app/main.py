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
        },
        {
            "title": "Beca Fulbright",
            "description": "El programa Fulbright es una iniciativa del gobierno de Estados Unidos orientada a promover el intercambio educativo y cultural entre países. Ofrece becas a profesionales y estudiantes internacionales para realizar estudios de posgrado, investigación o actividades académicas en universidades estadounidenses.\n\nSu objetivo principal es formar profesionales con alta preparación académica y una visión global, capaces de contribuir al desarrollo de sus países de origen.\n\nA diferencia de otras becas, Fulbright no solo evalúa el rendimiento académico, sino también el perfil profesional, el potencial de liderazgo y el compromiso con la comunidad.\n\nAdemás del financiamiento, los becarios pasan a formar parte de la red internacional Fulbright, que incluye miles de egresados en distintas áreas a nivel mundial.",
            "type": "scholarship",
            "organization": "Fulbright Program / Gobierno de Estados Unidos",
            "country": "Estados Unidos",
            "deadline": None,
            "eligibility": "Título universitario, buen nivel académico, inglés TOEFL/IELTS, ensayos de motivación, cartas de recomendación, experiencia relevante y compromiso con el país de origen.",
            "benefits": "Matrícula completa, pasajes internacionales, estipendio mensual, seguro médico, apoyo inicial de instalación y acceso a red internacional Fulbright.",
            "slots": None,
            "slug": "fulbright-beca",
            "organization_name": "Fulbright",
            "status": "approved",
            "short_description": "Fulbright ofrece becas completas para estudios de posgrado, investigación o actividades académicas en universidades de Estados Unidos, formando líderes con visión global e impacto social.",
            "activities": [
                "Estudios de maestría en universidades de EE.UU. 🎓",
                "Investigación académica o científica 🔬",
                "Intercambio cultural y liderazgo 🌍",
                "Networking con becarios internacionales 🤝"
            ],
            "requirements": [
                "Título universitario",
                "Buen nivel académico",
                "Certificado de inglés TOEFL/IELTS",
                "Ensayos: historia personal y plan de estudios",
                "Cartas de recomendación",
                "Experiencia relevante",
                "Compromiso con el país de origen"
            ],
            "benefits_json": [
                "Matrícula completa 💸",
                "Pasajes internacionales ✈️",
                "Estipendio mensual",
                "Seguro médico",
                "Apoyo inicial de instalación",
                "Acceso a red internacional Fulbright 🌍"
            ],
            "dates_info": "Convocatoria variable según país | Generalmente cierra en Octubre",
            "support_ai": [
                "Crear ensayo paso a paso",
                "Mejorar perfil automáticamente",
                "Practicar entrevista",
                "Preparar cartas de motivación",
                "Revisar requisitos antes de postular"
            ],
            "facebook_url": "https://www.facebook.com/FulbrightProgram",
            "instagram_url": "https://www.instagram.com/fulbrightprogram/",
            "youtube_url": "https://www.youtube.com/@FulbrightProgram",
            "video_url": "https://www.youtube.com/watch?v=fulbright-video",
            "image_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80",
            "is_demo": False,
            # Extended fields
            "city": "Variable según universidad",
            "institution": "Fulbright Foreign Student Program",
            "level": "Maestría / Investigación",
            "funding_type": "100% completa",
            "area": "Multidisciplinaria",
            "language": "Inglés",
            "duration": "1–2 años",
            "official_url": "https://foreign.fulbrightonline.org/",
            "ideal_profile": [
                {"emoji": "🏆", "title": "Profesionales con liderazgo", "tags": ["Liderazgo probado", "Gestión de equipos"]},
                {"emoji": "🤝", "title": "Compromiso social", "tags": ["Voluntariado", "Impacto comunitario"]},
                {"emoji": "🌐", "title": "Visión global", "tags": ["Mentalidad global", "Diversidad cultural"]},
                {"emoji": "💡", "title": "Interés en generar impacto", "tags": ["Innovación", "Retorno al país"]}
            ],
            "testimonials": [
                {"name": "Valeria Montoya", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Columbia University", "program": "Políticas Públicas", "quote": "Fulbright cambió mi vida. No solo aprendí en las mejores aulas del mundo, sino que construí una red de contactos que me permite generar impacto real en Bolivia.", "avatar": "VM"},
                {"name": "Carlos Quispe", "country": "🇧🇴 Bolivia", "year": "2022", "university": "Johns Hopkins", "program": "Salud Pública", "quote": "El proceso de aplicación fue desafiante, pero EDULAB me ayudó a preparar mis ensayos y simular entrevistas. Hoy trabajo en políticas de salud pública.", "avatar": "CQ"},
                {"name": "Sofía Gutiérrez", "country": "🇵🇪 Perú", "year": "2024", "university": "Georgetown University", "program": "Derecho Internacional", "quote": "Lo que más valoro de Fulbright es la red alumni. Hay ex-becarios en cada ministerio, empresa global y organismo internacional.", "avatar": "SG"}
            ],
            "faq": [
                {"question": "¿Necesito experiencia laboral para postular?", "answer": "Sí, se recomienda tener al menos 2 años de experiencia profesional relevante. Fulbright valora el impacto que has tenido en tu campo y tu potencial de liderazgo."},
                {"question": "¿Qué nivel de inglés exigen?", "answer": "Se requiere TOEFL iBT 79+ o IELTS 6.5+ mínimo. Los puntajes exactos pueden variar según el programa y universidad destino."},
                {"question": "¿Puedo aplicar desde Bolivia?", "answer": "Sí. La Comisión Fulbright Bolivia gestiona las aplicaciones locales. Debes contactarles directamente para conocer las fechas exactas de la convocatoria."},
                {"question": "¿Cuándo abre la convocatoria?", "answer": "Generalmente la convocatoria abre entre junio y agosto, con cierre en octubre. Las fechas varían según el país. EDULAB te notifica cuando abre."},
                {"question": "¿Puedo elegir en qué universidad estudiar?", "answer": "En parte. Fulbright trabaja con más de 1,500 universidades. Puedes proponer preferencias en tu aplicación, aunque la asignación final depende de disponibilidad y tu perfil."},
                {"question": "¿Tengo que regresar después de la beca?", "answer": "Sí, el programa requiere que los becarios regresen a su país de origen para aplicar sus conocimientos. Esto forma parte del compromiso J-1 visa."},
                {"question": "¿Cómo me ayuda EDULAB en el proceso?", "answer": "EDULAB te ayuda a preparar tus ensayos con IA, simular entrevistas, optimizar tu CV, revisar requisitos y hacer seguimiento de tu aplicación en tiempo real."}
            ]
        }
    ]

    from app.organizations.models import Organization
    from app.users.models import User
    from sqlalchemy import func

    async def get_or_create_seed_org(db, name: str, email: str, user_uid: str) -> int:
        # Check if organization already exists with name matching the program's organization_name (case-insensitive)
        result = await db.execute(select(Organization).where(func.lower(Organization.name) == name.lower()))
        org = result.scalars().first()
        if org:
            logger.info(f"Using existing organization '{org.name}' (ID: {org.id}, Status: {org.status}) for seed programs.")
            return org.id
            
        # If AIESEC or others don't exist, create mock user and organization
        user_res = await db.execute(select(User).where(User.email == email))
        user = user_res.scalars().first()
        if not user:
            user = User(
                firebase_uid=user_uid,
                email=email,
                full_name=name,
                role="organization",
                status="active"
            )
            db.add(user)
            await db.flush()
            
        org = Organization(
            user_id=user.id,
            name=name,
            type="ONG" if name == "AIESEC" else "Universidad" if "University" in name else "Fundación",
            country="Global",
            city="Global",
            contact_name=f"Admin {name}",
            contact_position="Director",
            contact_email=email,
            contact_phone="12345678",
            status="APPROVED"
        )
        db.add(org)
        await db.flush()
        await db.commit()
        return org.id

    async with SessionLocal() as db:
        for seed_data in seeds:
            # Normalize status to approved
            seed_data["status"] = "approved"
            
            # Fetch/create respective organization
            org_name = seed_data["organization_name"] or seed_data["organization"]
            org_email = f"{org_name.lower().replace(' ', '').replace('-', '')}@test.com"
            org_uid = f"mock-{org_name.lower().replace(' ', '').replace('-', '')}-uid"
            
            org_id = await get_or_create_seed_org(db, org_name, org_email, org_uid)
            seed_data["organization_id"] = org_id
            
            result = await db.execute(
                select(Program).where(Program.slug == seed_data["slug"])
            )
            existing = result.scalars().first()
            if not existing:
                new_program = Program(**seed_data)
                db.add(new_program)
                logger.info(f"Added seed program: '{seed_data['title']}' ({seed_data['slug']}) linked to Org ID {org_id}")
            else:
                if existing.organization_id is None:
                    existing.organization_id = org_id
                existing.status = "approved"
                db.add(existing)
                logger.info(f"Ensured seed program: '{seed_data['title']}' ({seed_data['slug']}) is approved and linked to Org ID {existing.organization_id}")
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

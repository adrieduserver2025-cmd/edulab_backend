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
            "title": "Voluntariado con TECHO (Sedes Internacionales)",
            "description": "Voluntariado enfocado en el desarrollo comunitario y la construcción de viviendas de emergencia en asentamientos precarios. Los voluntarios trabajan junto a las familias para mejorar su entorno social.\n\nMás de 1.2 millones de jóvenes ya se sumaron a nuestro voluntariado. Somos una organización constituida por jóvenes que destinan fuerzas, tiempo y ganas a transformar la realidad de Latinoamérica, junto con las familias que habitan en asentamientos populares.\n\n¿Por qué ser voluntario/a?\nEl voluntariado es el motor de la organización, es la fuerza transformadora de la realidad en la que vivimos. Gracias a los voluntarios y voluntarias de TECHO, las familias de los barrios populares pueden vivir mejor.",
            "type": "volunteering",
            "organization": "TECHO Internacional / TECHO Bolivia",
            "country": "Bolivia & Latinoamérica (18 países)",
            "city": "La Paz, Santa Cruz, Cochabamba, Sucre, Tarija",
            "institution": "TECHO Internacional / TECHO Bolivia",
            "level": "Voluntariado Social & Desarrollo Comunitario",
            "funding_type": "No financiado (Gastos de traslado y cuota logística mínima)",
            "area": "Urbanismo Social & Reducción de Pobreza",
            "language": "Español",
            "duration": "Recurrente / Fines de semana",
            "deadline": None,
            "official_url": "https://techo.org/",
            "eligibility": "Jóvenes bolivianos e internacionales interesados en el urbanismo social, trabajo comunitario de campo y reducción de la pobreza. Motivación por el trabajo de campo y capacidad de trabajo en equipo.",
            "benefits": "Certificado oficial TECHO, desarrollo de competencias de liderazgo y trabajo de campo, integración comunitaria y red de más de 1.2 millones de voluntarios en Latinoamérica.",
            "slots": 100,
            "slug": "techo-voluntariado",
            "organization_name": "TECHO",
            "status": "approved",
            "short_description": "Voluntariado enfocado en el desarrollo comunitario y la construcción de viviendas de emergencia en asentamientos precarios.",
            "activities": [
                "Construcciones de viviendas de emergencia los fines de semana 🏠",
                "Trabajos continuos en asentamientos populares y equipos de soporte TECHO 🛠️",
                "Voluntariado con colegios, grupos familiares y corporativo (RSE) 👥",
                "Diagnóstico comunitario e inmersión social 📊"
            ],
            "requirements": [
                "Motivación por el trabajo de campo comunitario",
                "Capacidad de trabajo en equipo y adaptabilidad",
                "Disponibilidad los fines de semana o jornadas de construcción",
                "Cubrir gastos personales de traslado y cuota logística mínima"
            ],
            "benefits_json": [
                "Transformación social directa en asentamientos populares 🏠",
                "Formación en liderazgo social y trabajo comunitario 🧠",
                "Red de +1.2 millones de voluntarios en 18 países de LATAM 🌍",
                "Certificado oficial de voluntariado TECHO 📜"
            ],
            "dates_info": "Convocatoria abierta y recurrente durante todo el año",
            "support_ai": [
                "Orientación sobre las modalidades de voluntariado TECHO",
                "Preparación de perfil de voluntario social",
                "Coordinación de sedes de contacto en Bolivia (La Paz, Santa Cruz, Cochabamba, Sucre, Tarija)"
            ],
            "facebook_url": "https://www.facebook.com/TECHO.org",
            "instagram_url": "https://www.instagram.com/techo_org/",
            "youtube_url": "https://www.tiktok.com/@techo_latam",
            "video_url": "https://www.tiktok.com/@techo_enbolivia/video/7522875353610587398",
            "image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🏠", "title": "Jóvenes Comprometidos", "tags": ["Construcción comunitaria", "Fines de semana"]},
                {"emoji": "🇧🇴", "title": "Sedes en Bolivia", "tags": ["La Paz", "Santa Cruz", "Cochabamba", "Sucre", "Tarija"]},
                {"emoji": "🤝", "title": "Trabajo en Equipo", "tags": ["Desarrollo social", "RSE Corporativo"]}
            ],
            "testimonials": [
                {"name": "Emi Vrančić", "country": "🇧🇴 Bolivia", "year": "2024", "university": "TECHO Bolivia", "program": "Voluntariado Social", "quote": "La experiencia de construir junto a las familias de los asentamientos te cambia la perspectiva por completo.", "avatar": "EV"},
                {"name": "Emanuel Buezo", "country": "🇧🇴 Bolivia", "year": "2024", "university": "TECHO Bolivia", "program": "Voluntariado Social", "quote": "Ser voluntario en TECHO es aportar energía y trabajo real para transformar vidas en nuestras comunidades.", "avatar": "EB"}
            ],
            "faq": [
                {"question": "¿Cuáles son las formas de participar como voluntario/a?", "answer": "Puedes participar en construcciones de fines de semana, en equipos permanentes de trabajo, con tu colegio, en grupos de familia/amigos o mediante voluntariado corporativo (RSE)."},
                {"question": "¿En qué ciudades de Bolivia está presente TECHO?", "answer": "TECHO trabaja en Bolivia desde 2009 con sedes en La Paz (2009), Santa Cruz (2012), y desde 2021 en Tarija, Cochabamba y Sucre."},
                {"question": "¿El voluntariado requiere cuota?", "answer": "Es un voluntariado no financiado. El voluntario cubre sus gastos de traslado y una cuota logística mínima orientada al transporte y materiales."}
            ]
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
        },
        {
            "title": "Chevening Scholarships",
            "slug": "chevening-beca",
            "type": "scholarship",
            "organization": "Gobierno del Reino Unido (FCDO)",
            "organization_name": "Chevening UK",
            "country": "Reino Unido",
            "city": "Londres y otras ciudades del Reino Unido",
            "institution": "Universidades del Reino Unido (UK Universities)",
            "level": "Maestría",
            "funding_type": "100% completa",
            "area": "Multidisciplinaria",
            "language": "Inglés",
            "duration": "1 año académico (12 meses)",
            "deadline": "2026-10-07",
            "official_url": "https://www.chevening.org",
            "short_description": "Programa de élite del gobierno británico que busca profesionales bolivianos con alto potencial de liderazgo y compromiso social para realizar una maestría de un año en cualquier universidad del Reino Unido.",
            "description": "Programa de élite del gobierno británico que busca profesionales bolivianos con alto potencial de liderazgo y compromiso social para realizar una maestría de un año en cualquier universidad del Reino Unido. Cubre matrícula, manutención, pasajes y costo de visa.\n\nChevening evalúa el potencial de liderazgo, la excelencia académica y la red de contactos profesionales del postulante. Al finalizar, el becario debe retornar a Bolivia por al menos 2 años.\n\nUno de los programas más prestigiosos del mundo. La carta de motivación y las entrevistas son decisivas. Las horas de voluntariado en organizaciones formales sí cuentan como experiencia.",
            "eligibility": "Ciudadanía boliviana, título universitario equivalente a 2:1 británico, mínimo 2.800 horas (aprox. 2 años) de experiencia laboral o voluntariado post-grado, certificado de inglés (IELTS/TOEFL) y compromiso de retorno por 2 años.",
            "benefits": "Matrícula completa, pasajes internacionales ida y vuelta, estipendio mensual (£1.690 en Londres / £1.378 fuera de Londres), costo de visa, asignación de llegada (£1.236) y despedida (£619). Valor total aprox. £30.000.",
            "slots": None,
            "status": "approved",
            "activities": [
                "Estudios de maestría de 1 año en el Reino Unido 🇬🇧",
                "Networking en la Red Global de Becarios Chevening 🤝",
                "Eventos diplomáticos y culturales del FCDO 🏛️",
                "Proyectos de retorno e impacto social en Bolivia 🇧🇴"
            ],
            "requirements": [
                "Ciudadanía boliviana",
                "Título universitario equivalente a 2:1 británico",
                "Mínimo 2.800 horas de experiencia laboral post-grado (o voluntariado)",
                "Certificado de inglés (IELTS/TOEFL) al estándar Chevening",
                "Seleccionar 3 opciones de maestría en el Reino Unido",
                "Compromiso de retorno mínimo de 2 años a Bolivia tras la beca"
            ],
            "benefits_json": [
                "Matrícula completa 💸",
                "Pasajes internacionales ida y vuelta ✈️",
                "Estipendio mensual de hasta £1.690/mes 💰",
                "Costo de visa de estudiante cubierto 🛡️",
                "Asignación de llegada (£1.236) e instalación 📦",
                "Acceso a la Red Global Chevening (+50.000 alumni) 🌐"
            ],
            "dates_info": "Cierre 7 de Octubre de 2026 | Apertura en Agosto 2026",
            "support_ai": [
                "Redactar ensayos de liderazgo y networking Chevening",
                "Calcular y certificar 2.800 horas de experiencia laboral/voluntariado",
                "Simulacro de entrevista de selección en inglés",
                "Preparar postulación a las 3 universidades británicas"
            ],
            "facebook_url": "https://www.facebook.com/cheveningfcdo",
            "instagram_url": "https://www.instagram.com/cheveningfcdo/",
            "youtube_url": "https://www.youtube.com/@CheveningFCDO",
            "video_url": "https://www.youtube.com/watch?v=chevening-video",
            "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇬🇧", "title": "Líderes con potencial", "tags": ["Liderazgo demostrado", "Impacto social"]},
                {"emoji": "💼", "title": "2.800+ Horas experiencia", "tags": ["Laboral / Voluntariado", "Post-bachelor"]},
                {"emoji": "🗣️", "title": "Dominio del inglés", "tags": ["IELTS / TOEFL", "Comunicación directa"]}
            ],
            "testimonials": [
                {"name": "Mateo Morales", "country": "🇧🇴 Bolivia", "year": "2023", "university": "London School of Economics (LSE)", "program": "Desarrollo Internacional", "quote": "Chevening no solo financió mi maestría en LSE, sino que me abrió puertas en redes globales de diplomacia y desarrollo.", "avatar": "MM"},
                {"name": "Camila Vargas", "country": "🇧🇴 Bolivia", "year": "2022", "university": "University of Oxford", "program": "Políticas Públicas", "quote": "El proceso exige claridad en tus objetivos de liderazgo. EDULAB me guió paso a paso para estructurar mis ensayos.", "avatar": "CV"}
            ],
            "faq": [
                {"question": "¿Las horas de voluntariado cuentan como experiencia?", "answer": "Sí, las horas de voluntariado en organizaciones formales post-titulación cuentan para completar las 2.800 horas requeridas."},
                {"question": "¿Debo tener admisión universitaria antes de postular?", "answer": "No es obligatorio al momento de enviar la solicitud, pero debes elegir 3 programas en el Reino Unido y obtener al menos una oferta incondicional más adelante."},
                {"question": "¿Es obligatorio el retorno a Bolivia?", "answer": "Sí, Chevening exige retornar a Bolivia por un mínimo de 2 años al finalizar la maestría para aplicar los conocimientos adquiridos."}
            ]
        },
        {
            "title": "Becas Fundación Carolina",
            "slug": "fundacion-carolina-beca",
            "type": "scholarship",
            "organization": "Fundación Carolina (Sector público y privado español)",
            "organization_name": "Fundación Carolina",
            "country": "España",
            "city": "Madrid, Barcelona, Valencia y varias ciudades de España",
            "institution": "Universidades e Institutos de Investigación de España",
            "level": "Posgrado / Doctorado",
            "funding_type": "Total o Parcial",
            "area": "Multidisciplinaria (Objetivos de Desarrollo Sostenible)",
            "language": "Español",
            "duration": "1 año académico",
            "deadline": "2026-03-02",
            "official_url": "https://www.fundacioncarolina.es",
            "short_description": "Programa de becas iberoamericano gestionado desde España para profesionales latinoamericanos. La convocatoria ofrece 736 becas en 203 programas académicos alineados con los ODS.",
            "description": "Programa de becas iberoamericano gestionado desde España, dirigido a profesionales latinoamericanos. La convocatoria ofrece 736 becas en 203 programas académicos, alineados con los Objetivos de Desarrollo Sostenible (ODS).\n\nNo se postula a la universidad directamente; se postula a través del portal de la Fundación Carolina seleccionando el programa específico del catálogo. Se pueden elegir hasta dos programas por convocatoria.\n\nSuele cubrir entre el 50% y 100% de matrícula, manutención mensual, seguro médico y, en muchos casos, pasajes aéreos.",
            "eligibility": "Ciudadanía iberoamericana (Bolivia incluida), título universitario de licenciatura, excelente expediente académico y postulación a los programas del catálogo Carolina.",
            "benefits": "Matrícula cubierta del 50% al 100%, estipendio mensual de manutención, seguro médico no farmacéutico y billetes de avión ida y vuelta.",
            "slots": None,
            "status": "approved",
            "activities": [
                "Estudios de posgrado o doctorado en universidades españolas 🇪🇸",
                "Integración en la Red Iberoamericana de Becarios Carolina 🌐",
                "Participación en seminarios y actividades sobre ODS 🌿"
            ],
            "requirements": [
                "Ciudadanía de un país iberoamericano (Bolivia)",
                "Título universitario de licenciatura",
                "Excelente expediente académico destacado",
                "Cumplir con los requisitos específicos del programa elegido",
                "Postular únicamente mediante el portal oficial de Fundación Carolina"
            ],
            "benefits_json": [
                "Matrícula del 50% al 100% financiada 💸",
                "Pasajes aéreos internacionales ida y vuelta ✈️",
                "Asignación mensual para manutención 💰",
                "Seguro médico internacional 🛡️",
                "Membresía en la Red de Exbecarios Carolina 🌐"
            ],
            "dates_info": "Posgrado: Enero a Marzo | Doctorado: Enero a Abril",
            "support_ai": [
                "Seleccionar las 2 mejores opciones del catálogo Carolina",
                "Redactar carta de motivación para la Fundación",
                "Optimizar CV según estándar europeo",
                "Validación de requisitos y promedio académico"
            ],
            "facebook_url": "https://www.facebook.com/FundacionCarolina",
            "instagram_url": "https://www.instagram.com/fundacioncarolina/",
            "youtube_url": "https://www.youtube.com/@FundacionCarolinaES",
            "video_url": "https://www.youtube.com/watch?v=carolina-video",
            "image_url": "https://images.unsplash.com/photo-1543783207-ec64e4d95325?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇪🇸", "title": "Licenciados de alto nivel", "tags": ["Título universitario", "Promedio destacado"]},
                {"emoji": "🌿", "title": "Impacto en ODS", "tags": ["Desarrollo sostenible", "Compromiso Iberoamericano"]},
                {"emoji": "🎯", "title": "Perfil definido", "tags": ["Máximo 2 programas", "Postulación directa portal"]}
            ],
            "testimonials": [
                {"name": "Lucía Torrez", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Universidad Complutense de Madrid", "program": "Periodismo Científico", "quote": "La Beca Carolina me permitió especializarme en España y conectar con profesionales de toda Iberoamérica.", "avatar": "LT"}
            ],
            "faq": [
                {"question": "¿Debo postular directo a la universidad en España?", "answer": "No. La postulación se hace 100% a través del portal de la Fundación Carolina seleccionando hasta dos programas del catálogo."},
                {"question": "¿Cubre el 100% de los gastos?", "answer": "Depende del convenio del programa. Muchas becas cubren el 100% de la matrícula y alojamiento, mientras que otras son cofinanciadas al 50-80%."}
            ]
        },
        {
            "title": "Becas Simón I. Patiño (Bélgica y Suiza)",
            "slug": "patino-beca",
            "type": "scholarship",
            "organization": "Fundación Simón I. Patiño",
            "organization_name": "Fundación Patiño",
            "country": "Bélgica y Suiza",
            "city": "Ginebra, Lausana, Bruselas, Berna y otras ciudades",
            "institution": "Universidades de Suiza (UNIGE, UNIL, EPFL, BFH) y Bélgica (ULB, VUB)",
            "level": "Maestría",
            "funding_type": "100% integral",
            "area": "Multidisciplinaria (Excepto Medicina y Odontología)",
            "language": "Inglés (C1/TOEFL≥90) / Francés / Alemán",
            "duration": "1 a 2 años",
            "deadline": "2026-11-30",
            "official_url": "https://patino.org/becas/",
            "short_description": "Becas de maestría de financiamiento 100% integral en prestigiosas universidades de Suiza y Bélgica para profesionales bolivianos comprometidos con el desarrollo del país.",
            "description": "A quienes encarnan la excelencia y el compromiso, la Fundación Patiño ofrece mucho más que apoyo: ofrece confianza.\n\nNuestras becas apoyan trayectorias profesionales prometedoras, tanto en Bolivia como a nivel internacional, para que cada talento pueda desarrollarse plenamente, con rigor, altos estándares y una sensación de recompensa.\n\nAprender es crecer. Transmitir el conocimiento es asegurar su impacto perdurable. Creemos que las mentes iluminadas, nutridas por el conocimiento y la responsabilidad, son las artífices de una Bolivia orgullosa, justa y radiante.\n\nOfrece financiamiento 100% integral incluyendo colegiatura, estadía completa y pasajes internacionales. Exige compromiso formal de retorno a Bolivia por un mínimo de 3 años tras culminar los estudios.",
            "eligibility": "Tener nacionalidad boliviana, menos de 30 años, título universitario de licenciatura en Bolivia, promedio académico ≥80/100 (UNIGE, UNIL, ULB, VUB, BFH) o ≥90/100 (EPFL), buen nivel de inglés (C1 o TOEFL≥90) y un proyecto para el desarrollo de Bolivia.",
            "benefits": "Matrícula completa, colegiatura, estadía integral (alojamiento y alimentación), seguro de salud y pasajes internacionales de ida y vuelta.",
            "slots": 15,
            "status": "approved",
            "activities": [
                "Estudios de maestría en UNIGE, UNIL, EPFL, ULB, BFH o VUB en Suiza/Bélgica 🇨🇭🇧🇪",
                "Desarrollo de proyecto de investigación enfocado en el desarrollo de Bolivia 🇧🇴",
                "Retorno obligatorio a Bolivia por un mínimo de 3 años para aplicar el conocimiento 🤝"
            ],
            "requirements": [
                "Tener nacionalidad boliviana",
                "Tener menos de 30 años",
                "Tener un título universitario boliviano (al menos licenciatura)",
                "Calificación académica requerida: ≥80/100 (UNIGE, UNIL, ULB, VUB, BFH) o ≥90/100 (EPFL)",
                "Buen conocimiento del inglés: Nivel C1 o TOEFL de al menos 90 puntos",
                "Proyecto específico para contribuir al desarrollo de Bolivia",
                "Exclusión explícita: No aplica para Medicina ni Odontología"
            ],
            "benefits_json": [
                "Matrícula y colegiatura 100% cubiertas 💸",
                "Pasajes aéreos internacionales ida y vuelta ✈️",
                "Estadía integral (alojamiento y manutención) 🏠",
                "Seguro de salud internacional 🛡️",
                "Acompañamiento institucional Fundación Patiño 🤝"
            ],
            "dates_info": "Convocatoria anual con cierre en Noviembre",
            "support_ai": [
                "Evaluación y verificación de promedio académico (80/100 o 90/100)",
                "Redacción de Carta de Motivación y Plan de Impacto para Bolivia",
                "Asistencia en postulación a universidades suizas (UNIGE, UNIL, EPFL, BFH) y belgas (ULB, VUB)",
                "Simulacro interactivo de entrevista institucional Patiño"
            ],
            "facebook_url": "https://www.facebook.com/FundacionPatino",
            "instagram_url": "https://www.instagram.com/fundacionpatino/",
            "youtube_url": "https://www.youtube.com/@FundacionPatino",
            "video_url": "https://www.youtube.com/watch?v=patino-video",
            "image_url": "https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇧🇴", "title": "Nacionalidad Boliviana", "tags": ["Residente en Bolivia", "Menor de 30 años"]},
                {"emoji": "🎓", "title": "Licenciatura y Excelencia", "tags": ["Título universitario", "Promedio ≥80/100 o ≥90/100"]},
                {"emoji": "🌐", "title": "Dominio de Inglés C1", "tags": ["TOEFL ≥90 pts", "Inglés C1 / Idioma oficial"]},
                {"emoji": "🚀", "title": "Proyecto para Bolivia", "tags": ["Desarrollo nacional", "Retorno 3 años"]}
            ],
            "testimonials": [
                {"name": "Gabriel Mendoza", "country": "🇧🇴 Bolivia", "year": "2022", "university": "EPFL Suiza", "program": "Ingeniería Ambiental", "quote": "La beca Patiño fue la llave para estudiar en una de las mejores politécnicas de Europa y aportar hoy a mi país.", "avatar": "GM"},
                {"name": "Camila Vargas", "country": "🇧🇴 Bolivia", "year": "2023", "university": "UNIGE Suiza", "program": "Maestría en Biología Molecular", "quote": "El respaldo de la Fundación Patiño me permitió formarme al más alto nivel sin preocupaciones financieras.", "avatar": "CV"}
            ],
            "faq": [
                {"question": "¿Puedo postular si estudio Medicina u Odontología?", "answer": "No. La Fundación Patiño excluye explícitamente las carreras de medicina y odontología de sus convocatorias de beca."},
                {"question": "¿Qué promedio necesito según la universidad?", "answer": "Necesitas un promedio mínimo de 80/100 para UNIGE, UNIL, ULB, VUB y BFH, y de al menos 90/100 para la EPFL (Lausanne)."},
                {"question": "¿Qué nivel de inglés se requiere?", "answer": "Se exige un nivel C1 de inglés o un puntaje mínimo de 90 puntos en el examen TOEFL iBT, o el nivel avanzado en el idioma de impartición del programa."},
                {"question": "¿Cuál es la consecuencia si la universidad no me admite?", "answer": "La beca Patiño queda sin efecto (revocada) si el estudiante seleccionado no logra obtener la carta de admisión formal de la universidad elegida en Suiza o Bélgica."},
                {"question": "¿Cuál es el compromiso al finalizar los estudios?", "answer": "Existe el compromiso formal de retornar a Bolivia inmediatamente después de culminar los estudios para trabajar y aplicar los conocimientos durante un período mínimo de 3 años."}
            ]
        },
        {
            "title": "Erasmus Mundus Joint Masters",
            "slug": "erasmus-mundus-beca",
            "type": "scholarship",
            "organization": "Unión Europea (Agencia Ejecutiva EACEA)",
            "organization_name": "Unión Europea",
            "country": "Unión Europea (Múltiples países)",
            "city": "Consorcio de universidades europeas",
            "institution": "Universidades Consorcio Erasmus Mundus",
            "level": "Maestría Conjunta",
            "funding_type": "100% completa",
            "area": "Multidisciplinaria",
            "language": "Inglés",
            "duration": "1 a 2 años académicos (12 a 24 meses)",
            "deadline": "2027-01-31",
            "official_url": "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
            "short_description": "Programa estrella de la Unión Europea para maestrías conjuntas impartidas por consorcios de al menos tres universidades europeas con movilidad internacional obligatoria entre países.",
            "description": "Programa estrella de la Unión Europea para maestrías conjuntas impartidas por consorcios de al menos tres universidades europeas. Ofrece experiencia multicultural única con movilidad obligatoria entre países.\n\nCubre un estipendio mensual de €1.400 (hasta €33.600 por 24 meses), matrícula completa, seguro médico internacional, gastos de viaje y costos de visa.\n\nEl estudiante debe elegir un programa del catálogo online de Erasmus Mundus y postular directamente al consorcio que lo imparte. Ideal para quienes buscan movilidad internacional sin límite de edad.",
            "eligibility": "Graduados universitarios de cualquier país (Bolivia totalmente elegible), sin límite de edad, con título de licenciatura (o último año) y dominio de inglés B2/C1.",
            "benefits": "Estipendio mensual de €1.400/mes (€33.600 total por 24 meses), matrícula 100% cubierta, seguro médico internacional, pasajes y costos de visa.",
            "slots": None,
            "status": "approved",
            "activities": [
                "Estudios en al menos 2 o 3 universidades europeas distintas 🇪🇺",
                "Obtención de título múltiple o conjunto reconocido globalmente 🎓",
                "Inmersión cultural y lingüística multicultural 🌍"
            ],
            "requirements": [
                "Título de licenciatura (o estar cursando el último año)",
                "Dominio de inglés certificado (B2 / C1 IELTS o TOEFL)",
                "CV en formato Europass",
                "Cartas de recomendación académicas o profesionales",
                "Postulación directa al consorcio del catálogo Erasmus Mundus"
            ],
            "benefits_json": [
                "Estipendio mensual de €1.400 / mes 💰",
                "Matrícula universitaria 100% financiada 💸",
                "Seguro de salud completo internacional 🛡️",
                "Subsidio para viajes y costos de visa ✈️",
                "Movilidad internacional garantizada en Europa 🇪🇺"
            ],
            "dates_info": "Cierres entre Noviembre 2026 y Febrero 2027",
            "support_ai": [
                "Búsqueda guiada en el catálogo de maestrías Erasmus Mundus",
                "Construcción de CV Europass estandarizado",
                "Redacción de Letter of Motivation por consorcio",
                "Verificación de créditos ECTS y titulación"
            ],
            "facebook_url": "https://www.facebook.com/EUErasmusPlusProgrammes",
            "instagram_url": "https://www.instagram.com/erasmus_mundus/",
            "youtube_url": "https://www.youtube.com/@EUErasmusPlus",
            "video_url": "https://www.youtube.com/watch?v=erasmus-video",
            "image_url": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇪🇺", "title": "Estudiantes internacionales", "tags": ["Movilidad obligatoria", "Multiculturalidad"]},
                {"emoji": "♾️", "title": "Sin límite de edad", "tags": ["Cualquier profesional", "Licenciatura lista"]},
                {"emoji": "🎓", "title": "Título conjunto europeo", "tags": ["Consorcio 3+ universidades", "Prestigio global"]}
            ],
            "testimonials": [
                {"name": "Alejandro Siles", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Consorcio Francia - Italia - España", "program": "Nanotecnología", "quote": "Estudiar en tres países europeos durante mi maestría fue la experiencia académica más enriquecedora de mi vida.", "avatar": "AS"}
            ],
            "faq": [
                {"question": "¿Hay límite de edad para Erasmus Mundus?", "answer": "No. Erasmus Mundus no tiene límite de edad para los postulantes."},
                {"question": "¿Puedo postular si aún no tengo el título físico?", "answer": "Sí, siempre y cuando estés en tu último semestre y te gradúes antes del inicio oficial de las clases en Europa."}
            ]
        },
        {
            "title": "Global Korea Scholarship (GKS-G)",
            "slug": "gks-korea-beca",
            "type": "scholarship",
            "organization": "Gobierno de Corea del Sur (NIIED)",
            "organization_name": "Gobierno de Corea",
            "country": "Corea del Sur",
            "city": "Seúl, Busan, Incheon, Daejeon",
            "institution": "Universidades de Corea del Sur",
            "level": "Maestría / Doctorado",
            "funding_type": "100% completa",
            "area": "Multidisciplinaria",
            "language": "Coreano / Inglés",
            "duration": "3 años (1 año idioma + 2 años maestría)",
            "deadline": "2026-02-28",
            "official_url": "https://www.studyinkorea.go.kr/",
            "short_description": "Beca integral del gobierno coreano para maestrías. Incluye un año obligatorio de inmersión en el idioma coreano antes de iniciar el programa académico en universidades de Corea del Sur.",
            "description": "Beca integral otorgada por el gobierno de Corea del Sur (NIIED) que cubre pasajes aéreos, matrícula universitaria completa, estipendio mensual, seguro médico y un año de curso intensivo de idioma coreano antes de la maestría.\n\nEs una de las becas más completas disponibles para profesionales bolivianos interesados en estudiar en el continente asiático y vivir una experiencia tecnológica y cultural de vanguardia.",
            "eligibility": "Nacionalidad boliviana (postulante y padres no coreanos), menor de 40 años al momento de postular, promedio académico superior al 80% (GPA equivalente) y salud física/mental óptima.",
            "benefits": "Pasajes aéreos ida y vuelta, curso de coreano por 1 año, matrícula universitaria completa, asignación mensual de manutención, subsidio de impresión de tesis y seguro de salud.",
            "slots": None,
            "status": "approved",
            "activities": [
                "1 año intensivo de aprendizaje de idioma coreano 🇰🇷",
                "Estudios de maestría en universidades líderes de Corea del Sur 🎓",
                "Intercambio tecnológico, cultural e industrial 🔬"
            ],
            "requirements": [
                "Nacionalidad boliviana (postulante y padres)",
                "Menor de 40 años de edad al momento de postular",
                "Título universitario de licenciatura",
                "Promedio académico acumulado mínimo del 80% (o GPA 2.64/4.0)",
                "Certificado médico oficial de salud óptima",
                "Personal Statement y Study Plan en inglés o coreano"
            ],
            "benefits_json": [
                "Matrícula universitaria 100% financiada 💸",
                "1 año de curso intensivo de idioma coreano 🇰🇷",
                "Pasajes aéreos internacionales ida y vuelta ✈️",
                "Estipendio mensual de manutención 💰",
                "Seguro médico e impresión de tesis 📄"
            ],
            "dates_info": "Convocatoria anual abierta en Febrero",
            "support_ai": [
                "Cálculo y certificación de promedio 80% / GPA",
                "Redacción de Personal Statement y Study Plan GKS",
                "Estrategia de postulación por vía Embajada vs Vía Universidad",
                "Simulacro de entrevista de selección"
            ],
            "facebook_url": "https://www.facebook.com/studyinkorea",
            "instagram_url": "https://www.instagram.com/studyinkorea_niied/",
            "youtube_url": "https://www.youtube.com/@StudyinKoreaNIIED",
            "video_url": "https://www.youtube.com/watch?v=gks-video",
            "image_url": "https://images.unsplash.com/photo-1538485399081-7191377e8241?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇰🇷", "title": "Pasión por Corea", "tags": ["Cultura e innovación", "Aprender coreano"]},
                {"emoji": "📊", "title": "Promedio 80%+", "tags": ["Alto rendimiento", "Menor de 40 años"]},
                {"emoji": "🌏", "title": "Visión Asia-Pacífico", "tags": ["Tecnología", "Intercambio global"]}
            ],
            "testimonials": [
                {"name": "Valeria Choque", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Seoul National University", "program": "Ingeniería de Software", "quote": "El año de idioma coreano fue desafiante y fascinante. GKS te da todo el respaldo para triunfar en Corea."}
            ],
            "faq": [
                {"question": "¿Necesito saber coreano antes de postular?", "answer": "No. La beca incluye un año completo de curso de idioma coreano en Corea antes de empezar la maestría."},
                {"question": "¿Cuál es la edad máxima para postular a maestría?", "answer": "Debes tener menos de 40 años al año de la postulación."}
            ]
        },
        {
            "title": "Beca Monbukagakusho (MEXT) - Undergraduate Students",
            "slug": "mext-japon-beca",
            "type": "scholarship",
            "organization": "Gobierno del Japón (Ministerio de Educación - MEXT)",
            "organization_name": "MEXT Japón",
            "country": "Japón",
            "city": "Tokio / Universidades Nacionales",
            "institution": "Universidades Nacionales de Japón",
            "level": "Pregrado (Licenciatura)",
            "funding_type": "100% completa",
            "area": "Todas las áreas del conocimiento",
            "language": "Japonés / Inglés",
            "duration": "5 años (1 año idioma + 4 años carrera)",
            "deadline": "2026-05-25",
            "official_url": "https://www.bo.emb-japan.go.jp/itpr_es/becas-pregrado.html",
            "short_description": "El programa de becas más prestigioso del Gobierno del Japón. Ofrece formación académica rigurosa con 1 año de idioma y carrera completa en universidades nacionales.",
            "description": "Es el programa de becas más prestigioso del Gobierno del Japón. Ofrece formación académica rigurosa que comienza con un año intensivo de idioma japonés y cultura, seguido de la carrera universitaria completa en universidades nacionales de alto nivel.\n\nCubre el 100% de la matrícula, pasajes aéreos ida y vuelta, estipendio mensual de manutención y exención de tasas de examen de ingreso a la universidad.",
            "eligibility": "Bachilleres bolivianos entre 17 y 24 años con excelente rendimiento académico y disposición para aprender idioma japonés desde cero.",
            "benefits": "Matrícula completa, pasajes aéreos ida y vuelta, estipendio mensual de manutención, exención de tasas de examen de ingreso.",
            "slots": 10,
            "status": "approved",
            "activities": [
                "1 año de estudio intensivo de idioma y cultura japonesa 🇯🇵",
                "4 años de carrera universitaria completa 🎓",
                "Exámenes y prácticas en universidades nacionales de Japón 🔬",
                "Inmersión cultural y académica 🌸"
            ],
            "requirements": [
                "Nacionalidad boliviana",
                "Edad entre 17 y 24 años al momento de postular",
                "Bachillerato concluido con excelente rendimiento académico",
                "Disposición para aprender el idioma japonés desde cero",
                "Exámenes escritos (matemáticas, inglés, japonés) y entrevista presencial en Embajada"
            ],
            "benefits_json": [
                "100% Matrícula universitaria cubierta 💸",
                "Pasajes aéreos ida y vuelta ✈️",
                "Estipendio mensual de manutención",
                "1 año de curso intensivo de japonés 🗣",
                "Exención de tasas de examen de ingreso"
            ],
            "dates_info": "Convocatoria 2026 para inicio en abril 2027 (cierre habitual en mayo vía Embajada del Japón en La Paz)",
            "support_ai": [
                "Simulador de entrevista presencial con la Embajada del Japón",
                "Plan de estudios y guías para exámenes escritos de matemáticas e inglés",
                "Redacción de carta de motivación"
            ],
            "facebook_url": "https://www.bo.emb-japan.go.jp",
            "instagram_url": "https://www.instagram.com/japan_emb_bolivia",
            "youtube_url": "https://www.youtube.com/@MEXT_Japan",
            "video_url": "https://www.youtube.com/watch?v=mext-japan",
            "image_url": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇯🇵", "title": "Pasión por Japón", "tags": ["Aprender japonés", "Cultura nipona"]},
                {"emoji": "📊", "title": "Excelencia Académica", "tags": ["17 a 24 años", "Matemáticas e Inglés"]},
                {"emoji": "🎓", "title": "Grado Completo", "tags": ["5 años de estudio", "Universidades Nacionales"]}
            ],
            "testimonials": [
                {"name": "Kenji Arakaki", "country": "🇧🇴 Bolivia", "year": "2023", "university": "University of Tokyo", "program": "Ingeniería de Sistemas", "quote": "El año de idioma en Tokio fue intenso pero te prepara perfectamente para afrontar la carrera en Japón."}
            ],
            "faq": [
                {"question": "¿Necesito saber japonés antes de postular?", "answer": "No. La beca incluye un año intensivo de idioma japonés desde nivel principiante."},
                {"question": "¿Dónde se rinden los exámenes?", "answer": "Los exámenes escritos y la entrevista personal se realizan presencialmente en la Embajada del Japón en La Paz."}
            ]
        },
        {
            "title": "Beca Türkiye Burslari",
            "slug": "turkiye-burslari-beca",
            "type": "scholarship",
            "organization": "Presidencia para los Turcos en el Extranjero y Comunidades Afines (YTB)",
            "organization_name": "Gobierno de Turquía",
            "country": "Turquía",
            "city": "Estambul, Ankara, Izmir",
            "institution": "Universidades Públicas de Turquía",
            "level": "Pregrado, Maestría y Doctorado",
            "funding_type": "100% completa",
            "area": "Multidisciplinaria",
            "language": "Turco / Inglés",
            "duration": "1 año turco + duración del programa (Licenciatura 4 años, Maestría 1-2 años, Doctorado 4 años)",
            "deadline": "2027-02-20",
            "official_url": "https://www.turkiyeburslari.gov.tr",
            "short_description": "Beca 100% integral del Gobierno de Turquía que incluye colocación universitaria, curso de turco gratuito de 1 año, alojamiento en residencia, estipendio mensual y pasajes.",
            "description": "Beca del gobierno turco dirigida a estudiantes internacionales. Incluye colocación universitaria automática, curso de turco gratuito de un año, alojamiento en residencia, estipendio mensual, pasajes de avión ida y vuelta y seguro médico.\n\nAplicación 100% online en el portal TBBS. Es una de las becas más completas de Europa/Asia para postulantes bolivianos sin requisito previo de idioma.",
            "eligibility": "Pregrado: menores de 21 años con promedio mínimo 70%. Maestría: menores de 30 años con promedio mínimo 75%. Doctorado: menores de 35 años con promedio mínimo 75%.",
            "benefits": "Matrícula completa, alojamiento universitario gratuito, estipendio mensual (4.500 TL pregrado / 6.500 TL maestría / 9.000 TL doctorado), pasajes ida y vuelta, seguro médico y curso de turco.",
            "slots": 20,
            "status": "approved",
            "activities": [
                "1 año de curso de idioma turco gratuito 🇹🇷",
                "Estudios universitarios de licenciatura, maestría o doctorado 🎓",
                "Intercambio cultural y actividades comunitarias YTB 🤝"
            ],
            "requirements": [
                "70% mínimo académico para Pregrado / 75% mínimo para Posgrado",
                "Límite de edad según nivel (Pregrado <21, Maestría <30, Doctorado <35)",
                "Carta de motivación obligatoria en portal TBBS",
                "No requiere certificado de idioma previo para programas en turco"
            ],
            "benefits_json": [
                "100% Matrícula y colocación universitaria 💸",
                "Residencia universitaria gratuita 🏠",
                "Estipendio mensual de 4.500 TL (Pregrado) / 6.500 TL (Maestría) / 9.000 TL (Doctorado)",
                "Pasajes aéreos internacionales ida y vuelta ✈️",
                "Seguro médico e inmersión en idioma turco 🇹🇷"
            ],
            "dates_info": "Convocatoria anual: Del 10 de Enero al 20 de Febrero de cada año",
            "support_ai": [
                "Redacción de Carta de Motivación para TBBS",
                "Selección inteligente de universidades y ciudades en Turquía",
                "Simulador de entrevista online YTB"
            ],
            "facebook_url": "https://www.facebook.com/turkiyeburslari",
            "instagram_url": "https://www.instagram.com/turkiyeburslari",
            "youtube_url": "https://www.youtube.com/@turkiyeburslari",
            "video_url": "https://www.youtube.com/watch?v=turkiye-burslari",
            "image_url": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇹🇷", "title": "Estudiantes Globales", "tags": ["Pregrado y Posgrado", "Sin idioma previo"]},
                {"emoji": "🏠", "title": "Alojamiento Cubierto", "tags": ["Residencia universitaria", "Estipendio mensual"]},
                {"emoji": "🌐", "title": "Proceso 100% Online", "tags": ["Portal TBBS", "Multidisciplinario"]}
            ],
            "testimonials": [
                {"name": "Mateo Morales", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Istanbul University", "program": "Relaciones Internacionales", "quote": "La beca te cubre todo y Turquía es un puente cultural increíble para estudiar."}
            ],
            "faq": [
                {"question": "¿Es necesario hablar turco antes de postular?", "answer": "No. La beca incluye un año completo de curso de idioma turco gratuito antes de iniciar tus estudios académicos."},
                {"question": "¿Cómo se realiza la postulación?", "answer": "La aplicación es 100% online a través del sistema oficial TBBS (Turkiye Burslari)."}]
        },
        {
            "title": "Stipendium Hungaricum Scholarship",
            "slug": "stipendium-hungaricum-beca",
            "type": "scholarship",
            "organization": "Gobierno de Hungría (Fundación Pública Tempus)",
            "organization_name": "Gobierno de Hungría",
            "country": "Hungría",
            "city": "Budapest, Debrecen, Szeged, Pécs",
            "institution": "30+ Universidades de Hungría",
            "level": "Pregrado, Maestría y Doctorado",
            "funding_type": "100% completa",
            "area": "Más de 900 programas académicos",
            "language": "Inglés (B2) / Húngaro",
            "duration": "2 a 4 años según nivel (Licenciatura 3-4, Maestría 1-2, Doctorado 4)",
            "deadline": "2027-01-15",
            "official_url": "https://www.stipendiumhungaricum.hu",
            "short_description": "Programa estrella del gobierno húngaro para educación superior. Bolivia es elegible vía SEGIB con más de 900 programas en inglés.",
            "description": "Programa estrella del gobierno húngaro para internacionalizar la educación superior. Bolivia es elegible a través del marco SEGIB (Secretaría General Iberoamericana), con 30+ universidades participantes y más de 900 programas en inglés.\n\nCubre matrícula completa, estipendio mensual, alojamiento o subsidio para él y seguro médico básico.",
            "eligibility": "Ciudadanía boliviana (marco SEGIB); título previo según nivel; certificado de idioma (inglés B2 o húngaro); admisión en hasta 2 elecciones del catálogo.",
            "benefits": "Matrícula completa, estipendio mensual, residencia universitaria o subsidio de alquiler, seguro médico de cobertura nacional.",
            "slots": 15,
            "status": "approved",
            "activities": [
                "Estudios universitarios de grado o posgrado en inglés 🇪🇺",
                "Investigación y laboratorios de vanguardia en Hungría 🔬",
                "Movilidad estudiantil en la Unión Europea 🌍"
            ],
            "requirements": [
                "Ciudadanía boliviana elegible vía SEGIB",
                "Título académico previo según nivel",
                "Certificado de idioma inglés B2 mínimo (algunos programas no exigen IELTS)",
                "Aplicación online a máximo 2 elecciones en portal apply.stipendiumhungaricum.hu"
            ],
            "benefits_json": [
                "100% Matrícula universitaria exenta 💸",
                "Estipendio mensual de manutención",
                "Residencia universitaria o subsidio de alojamiento 🏠",
                "Seguro médico nacional húngaro 🏥"
            ],
            "dates_info": "Convocatoria anual: Cierre el 15 de Enero a las 14:00 CET",
            "support_ai": [
                "Selección de las 2 opciones universitarias óptimas",
                "Redacción de Carta de Motivación en inglés",
                "Verificación de exenciones de examen de idioma"
            ],
            "facebook_url": "https://www.facebook.com/stipendiumhungaricum",
            "instagram_url": "https://www.instagram.com/stipendiumhungaricum",
            "youtube_url": "https://www.youtube.com/@stipendiumhungaricum",
            "video_url": "https://www.youtube.com/watch?v=hungary-stipendium",
            "image_url": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇭🇺", "title": "Estudios en Europa", "tags": ["900+ Programas", "Clases en Inglés"]},
                {"emoji": "🇧🇴", "title": "Elegibilidad Bolivia", "tags": ["Convenio SEGIB", "Licenciatura y Posgrado"]},
                {"emoji": "💶", "title": "Financiación Total", "tags": ["Matrícula", "Estipendio", "Alojamiento"]}
            ],
            "testimonials": [
                {"name": "Lucía Fernández", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Eötvös Loránd University (ELTE)", "program": "Maestría en Biotecnología", "quote": "Hungría ofrece una calidad académica excelente en Europa y la beca cubre tus gastos holgadamente."}
            ],
            "faq": [
                {"question": "¿Bolivia califica a la Beca Stipendium Hungaricum?", "answer": "Sí, Bolivia forma parte de los países elegibles mediante el acuerdo marco SEGIB."},
                {"question": "¿A cuántas carreras puedo aplicar?", "answer": "Puedes seleccionar un máximo de 2 opciones académicas en el portal oficial."}]
        },
        {
            "title": "Chevening Scholarships",
            "slug": "chevening-uk-beca",
            "type": "scholarship",
            "organization": "Gobierno del Reino Unido (FCDO)",
            "organization_name": "Gobierno del Reino Unido",
            "country": "Reino Unido",
            "city": "Londres, Edimburgo, Manchester, Oxford, Cambridge",
            "institution": "Cualquier Universidad del Reino Unido",
            "level": "Maestría (1 año)",
            "funding_type": "100% completa",
            "area": "Todas las áreas del conocimiento",
            "language": "Inglés (TOEFL/IELTS)",
            "duration": "1 año académico (12 meses)",
            "deadline": "2026-10-07",
            "official_url": "https://www.chevening.org",
            "short_description": "Programa de élite del gobierno británico para maestrías de 1 año en el Reino Unido. Cubre matrícula completa, estipendio de £1.690/mes, vuelos y visa.",
            "description": "Programa de élite del gobierno británico que busca profesionales bolivianos con alto potencial de liderazgo y compromiso social para realizar una maestría de un año en cualquier universidad del Reino Unido.\n\nCubre matrícula completa, estipendio mensual (£1.690 en Londres / £1.378 fuera de Londres), pasajes aéreos ida y vuelta, costo de visa y asignación de llegada (£1.236) y despedida (£619). Valor estimado superior a £30.000.",
            "eligibility": "Ciudadanía boliviana; título universitario equivalente a 2:1 británico; mínimo 2.800 horas (aprox 2 años) de experiencia laboral o voluntariado; compromiso de retorno por 2 años.",
            "benefits": "Matrícula completa, estipendio mensual, pasajes internacionales, visa, asignación de llegada (£1.236) y despedida (£619).",
            "slots": 8,
            "status": "approved",
            "activities": [
                "Maestría de 1 año en universidad británica de prestigio 🇬🇧",
                "Talleres y conferencias de liderazgo FCDO 🤝",
                "Conexión con red global de becarios Chevening 🌍"
            ],
            "requirements": [
                "Ciudadanía boliviana",
                "Título universitario de licenciatura",
                "Mínimo 2.800 horas de experiencia laboral o voluntariado comprobable",
                "Cumplir requisito de inglés oficial",
                "Compromiso de retorno a Bolivia por un mínimo de 2 años tras la beca"
            ],
            "benefits_json": [
                "Matrícula universitaria 100% financiada (sin tope en la mayoría de programas) 💸",
                "Estipendio mensual de £1.690 (Londres) / £1.378 (resto del Reino Unido)",
                "Pasajes aéreos ida y vuelta en clase económica ✈️",
                "Costo de visa de estudiante cubierto",
                "Asignación de llegada (£1.236) y de salida (£619)"
            ],
            "dates_info": "Convocatoria anual: Abre en Agosto y cierra el 7 de Octubre",
            "support_ai": [
                "Redacción y pulido de los 4 Ensayos Chevening (Leadership, Networking, Studying in UK, Career Plan)",
                "Cálculo de horas de experiencia profesional y voluntariado",
                "Simulador de entrevista presencial con Embajada Británica"
            ],
            "facebook_url": "https://www.facebook.com/cheveningfcdo",
            "instagram_url": "https://www.instagram.com/cheveningfcdo",
            "youtube_url": "https://www.youtube.com/@cheveningfcdo",
            "video_url": "https://www.youtube.com/watch?v=chevening-video",
            "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇬🇧", "title": "Liderazgo Destacado", "tags": ["Potencial social", "Red de contactos"]},
                {"emoji": "💼", "title": "2+ Años Experiencia", "tags": ["2.800 horas laborales", "Voluntariado suma"]},
                {"emoji": "🎓", "title": "Maestría de 1 Año", "tags": ["UK Universities", "100% Financiada"]}
            ],
            "testimonials": [
                {"name": "Sebastián Arze", "country": "🇧🇴 Bolivia", "year": "2023", "university": "LSE (London School of Economics)", "program": "MSc Public Policy", "quote": "Chevening no solo paga tus estudios en UK, te forma como líder transformador para Bolivia."}
            ],
            "faq": [
                {"question": "¿Las horas de voluntariado cuentan como experiencia laboral?", "answer": "Sí. Las horas de voluntariado formalmente certificado suman dentro de las 2.800 horas requeridas."},
                {"question": "¿Debo regresar a Bolivia al terminar la maestría?", "answer": "Sí. Existe el compromiso de retornar a Bolivia por al menos 2 años tras culminar la beca."}]
        },
        {
            "title": "Beca OEA - GCUB (Brasil)",
            "slug": "oea-gcub-brasil-beca",
            "type": "scholarship",
            "organization": "OEA & Grupo de Cooperación Internacional de Universidades Brasileñas (GCUB)",
            "organization_name": "OEA / GCUB",
            "country": "Brasil",
            "city": "San Pablo, Río de Janeiro, Brasilia",
            "institution": "50+ Universidades Brasileñas",
            "level": "Maestría y Doctorado",
            "funding_type": "100% completa (Matrícula + Estipendio)",
            "area": "Todas las áreas académicas",
            "language": "Portugués / Español",
            "duration": "Hasta 24 meses (2 años)",
            "deadline": "2026-07-31",
            "official_url": "https://www.gcub.org.br/",
            "short_description": "Alianza de movilidad de la OEA con 50+ universidades brasileñas. Exención total de matrícula y estipendio mensual para maestrías y doctorados.",
            "description": "Una de las alianzas de movilidad académica más grandes de la región. Permite a profesionales bolivianos realizar maestrías en más de 50 universidades brasileñas en casi todas las áreas del conocimiento.\n\nCubre exención total de matrícula académica y estipendio mensual pagado por la universidad anfitriona en Brasil. Se puede postular hasta a 5 programas en diferentes universidades de Brasil en un solo formulario.",
            "eligibility": "Ciudadanos de estados miembros de la OEA (Bolivia incluido) con título de licenciatura de universidad reconocida. No tener nacionalidad brasileña.",
            "benefits": "Exención total de matrícula universitaria y estipendio mensual variable pagado por la universidad anfitriona.",
            "slots": 30,
            "status": "approved",
            "activities": [
                "Maestría presencial en universidades de Brasil 🇧🇷",
                "Investigación científica y proyectos académicos 🔬",
                "Postulación simultánea a hasta 5 programas diferentes 📚"
            ],
            "requirements": [
                "Título universitario de Licenciatura",
                "No tener nacionalidad brasileña",
                "Declaración de buena salud física y mental",
                "No es obligatorio saber portugués al momento de postular"
            ],
            "benefits_json": [
                "Exención 100% de matrícula y tasas académicas 💸",
                "Estipendio mensual de subsistencia durante la maestría 💰",
                "Acceso a laboratorios e instalaciones de 50+ universidades 🇧🇷"
            ],
            "dates_info": "Convocatoria anual: Abre habitualmente a mitad de año (cierre en Julio)",
            "support_ai": [
                "Selección óptima de los 5 programas universitarios en Brasil",
                "Estructuración de hoja de vida académica",
                "Carta de declaración de objetivos"
            ],
            "facebook_url": "https://www.facebook.com/gcub.org.br",
            "instagram_url": "https://www.instagram.com/gcub.oficial",
            "youtube_url": "https://www.youtube.com/@gcub",
            "video_url": "https://www.youtube.com/watch?v=oea-gcub",
            "image_url": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇧🇷", "title": "50+ Universidades", "tags": ["Brasil", "Multi-opción hasta 5 carreras"]},
                {"emoji": "🎓", "title": "Maestría y Posgrado", "tags": ["Exención de matrícula", "Estipendio mensual"]},
                {"emoji": "🗣", "title": "Sin portugués previo", "tags": ["Aprendizaje en campus", "Elegible Bolivia"]}
            ],
            "testimonials": [
                {"name": "Diego Torrico", "country": "🇧🇴 Bolivia", "year": "2023", "university": "USP (Universidad de San Pablo)", "program": "Maestría en Ciencia de Datos", "quote": "Postular a 5 opciones en un solo formulario aumenta muchísimo las oportunidades de quedar en Brasil."}
            ],
            "faq": [
                {"question": "¿A cuántos programas puedo postular en la Beca OEA-GCUB?", "answer": "Puedes seleccionar hasta 5 programas diferentes en universidades distintas de Brasil en una misma postulación."},
                {"question": "¿Necesito certificado de idioma portugués para aplicar?", "answer": "No es obligatorio saber portugués al momento de la postulación."}]
        },
        {
            "title": "Becas SISS / Global Professionals (Suecia)",
            "slug": "swedish-institute-siss-beca",
            "type": "scholarship",
            "organization": "Instituto Sueco (Swedish Institute)",
            "organization_name": "Gobierno de Suecia",
            "country": "Suecia",
            "city": "Estocolmo, Lund, Uppsala, Gotemburgo",
            "institution": "Universidades de Suecia",
            "level": "Maestría (1 a 2 años)",
            "funding_type": "100% completa",
            "area": "Sostenibilidad, Innovación, Gobierno, Agenda 2030",
            "language": "Inglés C1",
            "duration": "1 a 2 años académicos",
            "deadline": "2027-02-28",
            "official_url": "https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/",
            "short_description": "Programa del Instituto Sueco enfocado en líderes globales. Cubre matrícula completa, estipendio de 11.000 SEK/mes, seguro y pasajes.",
            "description": "Programa enfocado en desarrollar líderes globales que contribuyan a la Agenda 2030 para el Desarrollo Sostenible. Financia maestrías de excelencia en Suecia con uno de los mejores estipendios de vida en Europa del Norte.\n\nCubre el 100% de la matrícula académica, un estipendio mensual de aprox. 11.000 SEK, seguro médico de cobertura completa y subsidio para pasajes internacionales.",
            "eligibility": "Profesionales bolivianos con mínimo 3.000 horas de experiencia laboral demostrable, liderazgo probado y haber postulado previamente a la universidad sueca en Enero.",
            "benefits": "Matrícula pagada directamente a la universidad, estipendio mensual de 11.000 SEK, pasajes aéreos y seguro de salud.",
            "slots": 10,
            "status": "approved",
            "activities": [
                "Maestría en universidades suecas de ranking mundial 🇸🇪",
                "Membresía en la red Network for Future Global Leaders (NFGL) 🌟",
                "Talleres de innovación y liderazgo sostenible en Escandinavia 🌲"
            ],
            "requirements": [
                "Mínimo 3.000 horas de experiencia laboral o voluntariado certificado",
                "Demostrar experiencia de liderazgo",
                "Haber postulado a una universidad sueca a través del portal nacional University Admissions en Enero"
            ],
            "benefits_json": [
                "100% Matrícula universitaria cubierta directamente 💸",
                "Estipendio mensual de 11.000 SEK (manutención de alto nivel en Suecia) 💰",
                "Asignación de viaje y pasajes aéreos ✈️",
                "Seguro de salud y accidentes completo 🏥"
            ],
            "dates_info": "Convocatoria anual: Postulación universitaria en Enero, postulación a beca SISS en Febrero",
            "support_ai": [
                "Cálculo y desglose del certificado de 3.000 horas laborales",
                "Redacción de Carta de Recomendación de Liderazgo para el Instituto Sueco",
                "Guía de postulación en University Admissions"
            ],
            "facebook_url": "https://www.facebook.com/swedishinstitute",
            "instagram_url": "https://www.instagram.com/swedishinstitute",
            "youtube_url": "https://www.youtube.com/@swedishinstitute",
            "video_url": "https://www.youtube.com/watch?v=sweden-siss",
            "image_url": "https://images.unsplash.com/photo-1509356843151-3e7d96241e11?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇸🇪", "title": "Líderes Sostenibles", "tags": ["Agenda 2030", "Innovación escandinava"]},
                {"emoji": "💼", "title": "3.000 Horas Experiencia", "tags": ["Trabajo comprobable", "Demostrar liderazgo"]},
                {"emoji": "💶", "title": "Estipendio 11.000 SEK", "tags": ["100% Matrícula", "Pasajes incluidos"]}
            ],
            "testimonials": [
                {"name": "Andrés Roca", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Lund University", "program": "MSc Environmental Management", "quote": "El nivel de vida en Suecia y la red de becarios del Instituto Sueco son insuperables."}
            ],
            "faq": [
                {"question": "¿Cuál es el primer paso para la Beca del Instituto Sueco?", "answer": "Primero debes aplicar a un programa de maestría en el portal nacional University Admissions en Enero, y luego solicitar la beca SISS en Febrero."},
                {"question": "¿Cuántas horas de experiencia exigen?", "answer": "Se exigen al menos 3.000 horas demostrables de trabajo remunerado o voluntariado."}]
        },
        {
            "title": "Becas ARES (Bélgica)",
            "slug": "ares-belgica-beca",
            "type": "scholarship",
            "organization": "Academia de Investigación y de Enseñanza Superior (ARES)",
            "organization_name": "Gobierno de Bélgica",
            "country": "Bélgica",
            "city": "Bruselas, Lieja, Lovaina la Nueva",
            "institution": "Universidades Francófonas de Bélgica",
            "level": "Maestría de Especialización",
            "funding_type": "100% completa",
            "area": "Salud Pública, Gestión de Riesgos, Recursos Hídricos, Pedagogía",
            "language": "Francés / Inglés",
            "duration": "1 año (12 meses)",
            "deadline": "2027-01-31",
            "official_url": "https://www.ares-ac.be/",
            "short_description": "Becas de maestría de especialización totalmente financiadas en Bélgica para profesionales enfocados en desarrollo y gestión de proyectos.",
            "description": "Becas de maestría de especialización dirigidas a profesionales de países socios que buscan adquirir habilidades para resolver problemáticas de desarrollo en sus países de origen.\n\nOfrece estipendio mensual de subsistencia, gastos de instalación iniciales, matrícula 100% exenta, seguro médico completo y billetes de avión ida y vuelta a Bélgica.",
            "eligibility": "Profesionales bolivianos menores de 40 años con título universitario de licenciatura, 2 años de experiencia profesional y dominio del idioma requerido (Francés o Inglés).",
            "benefits": "Estipendio mensual de subsistencia, gastos de instalación, matrícula, seguro médico y vuelos ida y vuelta.",
            "slots": 12,
            "status": "approved",
            "activities": [
                "Maestría de especialización práctica de 1 año en Bélgica 🇧🇪",
                "Investigación aplicada a desarrollo sostenible y salud pública 🔬",
                "Prácticas en laboratorios e institutos belgas 💡"
            ],
            "requirements": [
                "Título universitario de licenciatura",
                "Al menos 2 años de experiencia profesional post-grado",
                "Tener menos de 40 años al iniciar el programa",
                "Dominio de idioma (Francés B2 o Inglés B2 según el programa)"
            ],
            "benefits_json": [
                "100% Matrícula y aranceles universitarios cubiertos 💸",
                "Estipendio mensual completo de subsistencia 💰",
                "Asignación inicial para gastos de instalación",
                "Pasajes aéreos internacionales ida y vuelta ✈️",
                "Seguro médico integral 🏥"
            ],
            "dates_info": "Convocatoria anual: Abre en Agosto y cierra entre Enero y Febrero",
            "support_ai": [
                "Orientación en áreas elegibles de ARES (Salud pública, Agua, Riesgos)",
                "Redacción de justificación de proyecto para Bolivia",
                "Traducción de CV a formato europeo"
            ],
            "facebook_url": "https://www.facebook.com/ares.ac.be",
            "instagram_url": "https://www.instagram.com/ares_be",
            "youtube_url": "https://www.youtube.com/@ARES_be",
            "video_url": "https://www.youtube.com/watch?v=ares-belgica",
            "image_url": "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇧🇪", "title": "Especialización Bélgica", "tags": ["1 año duración", "Francófono e Inglés"]},
                {"emoji": "💼", "title": "2 Años Experiencia", "tags": ["Profesionales <40 años", "Impacto social"]},
                {"emoji": "💶", "title": "Financiación Completa", "tags": ["Estipendio", "Vuelos", "Instalación"]}
            ],
            "testimonials": [
                {"name": "Mariana Calle", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Université de Liège", "program": "Maestría en Gestión de Riesgos y Desastres", "quote": "ARES se enfoca en resolver problemas reales de desarrollo de nuestros países."}
            ],
            "faq": [
                {"question": "¿Cuál es el límite de edad para la Beca ARES de Bélgica?", "answer": "Debes tener menos de 40 años al momento de iniciar la maestría."},
                {"question": "¿Requiere experiencia laboral previa?", "answer": "Sí, se exigen al menos 2 años de experiencia profesional tras la titulación."}]
        },
        {
            "title": "Becas de Investigación de Corta Duración DAAD",
            "slug": "daad-investigacion-beca",
            "type": "scholarship",
            "organization": "Servicio Alemán de Intercambio Académico (DAAD)",
            "organization_name": "DAAD Alemania",
            "country": "Alemania",
            "city": "Göttingen, Heidelberg, Berlín, Múnich",
            "institution": "Universidades e Institutos de Investigación de Alemania",
            "level": "Investigación / Doctorado",
            "funding_type": "100% completa",
            "area": "Todas las áreas de investigación",
            "language": "Inglés / Alemán",
            "duration": "1 a 6 meses",
            "deadline": "2026-08-31",
            "official_url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
            "short_description": "Estancias de investigación de corta duración (1 a 6 meses) en Alemania para doctorandos y jóvenes científicos bolivianos.",
            "description": "Becas diseñadas para permitir a estudiantes de doctorado y jóvenes investigadores bolivianos realizar una estancia de investigación en una universidad o centro de investigación alemán. Ideal para recopilación de datos, uso de laboratorios específicos o trabajo de tesis.",
            "eligibility": "Estudiantes de doctorado, jóvenes académicos y científicos bolivianos con proyecto de investigación detallado y carta de invitación del profesor anfitrión en Alemania.",
            "benefits": "Estipendio mensual de 934€ a 1.200€, seguro médico completo y asignación para gastos de viaje internacional.",
            "slots": 15,
            "status": "approved",
            "activities": [
                "Trabajo científico de laboratorio o archivo en Alemania 🔬",
                "Uso de tecnología de punta e infraestructuras alemanas 📊",
                "Redacción de artículos científicos e intercambio académico 🤝"
            ],
            "requirements": [
                "Proyecto de investigación estructurado acordado con un supervisor en Alemania",
                "Carta de invitación oficial del profesor anfitrión alemán",
                "Dominio de inglés o alemán académico"
            ],
            "benefits_json": [
                "Estipendio mensual de 934€ a 1.200€ según grado académico 💶",
                "Seguro de salud, accidentes y responsabilidad civil 🏥",
                "Subsidio para pasajes internacionales ida y vuelta ✈️"
            ],
            "dates_info": "Dos cierres anuales habituales: En Abril y en Agosto",
            "support_ai": [
                "Estructuración de propuesta de investigación DAAD",
                "Redacción de modelo de contacto para profesores anfitriones alemanes",
                "Formulación de cronograma de laboratorio"
            ],
            "facebook_url": "https://www.facebook.com/DAAD.Worldwide",
            "instagram_url": "https://www.instagram.com/daad_worldwide",
            "youtube_url": "https://www.youtube.com/@DAADWorldwide",
            "video_url": "https://www.youtube.com/watch?v=daad-research",
            "image_url": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇩🇪", "title": "Estancia en Alemania", "tags": ["1 a 6 meses", "Laboratorios de punta"]},
                {"emoji": "🔬", "title": "Doctorandos e Investigadores", "tags": ["Tesis doctoral", "Recopilación datos"]},
                {"emoji": "💶", "title": "Beca Mensual DAAD", "tags": ["934€ a 1.200€/mes", "Seguro y Vuelos"]}
            ],
            "testimonials": [
                {"name": "Dr. Fernando Zeballos", "country": "🇧🇴 Bolivia", "year": "2023", "university": "TU Munich", "program": "Estancia Doctoral en Física", "quote": "El DAAD te da acceso a laboratorios alemanes con financiamiento impecable."}
            ],
            "faq": [
                {"question": "¿Cuál es la clave para obtener la Beca de Investigación DAAD?", "answer": "Tener un contacto previo sólido y contar con la carta de invitación firmada por un profesor anfitrión en una universidad o centro alemán."},
                {"question": "¿Qué duración tienen las estancias?", "answer": "Tienen una duración flexible de 1 a 6 meses."}]
        },
        {
            "title": "Humboldt Research Fellowship",
            "slug": "humboldt-research-beca",
            "type": "scholarship",
            "organization": "Fundación Alexander von Humboldt",
            "organization_name": "Fundación Humboldt",
            "country": "Alemania",
            "city": "Berlín, Bonn, Heidelberg, Múnich",
            "institution": "Universidades e Institutos de Investigación de Alemania",
            "level": "Postdoctorado / Investigación PhD",
            "funding_type": "100% completa",
            "area": "Todas las disciplinas académicas y científicas",
            "language": "Inglés / Alemán",
            "duration": "6 a 24 meses",
            "deadline": None,
            "official_url": "https://www.humboldt-foundation.de/en/apply/sponsorship-programmes/humboldt-research-fellowship",
            "short_description": "Becas postdoctorales de alto prestigio internacional para desarrollar proyectos de investigación autónomos en Alemania de 6 a 24 meses.",
            "description": "Programa destinado a investigadores con un perfil académico sobresaliente que deseen llevar a cabo un proyecto de investigación de libre elección en Alemania en colaboración con un anfitrión académico.\n\nSin cuotas por país: la selección se basa exclusivamente en la excelencia académica individual. Incluye estipendio mensual de 2.600€ a 3.100€, apoyo económico para cónyuges e hijos, gastos de viaje y cursos de alemán.",
            "eligibility": "Investigadores de todo el mundo con doctorado (PhD) obtenido en los últimos 4 a 12 años e historial sobresaliente de publicaciones internacionales peer-reviewed.",
            "benefits": "Asignación mensual de 2.600€ a 3.100€, apoyo económico para familiares, gastos de viaje y curso de alemán.",
            "slots": 10,
            "status": "approved",
            "activities": [
                "Proyecto de investigación autónomo en universidad o centro en Alemania 🔬",
                "Publicación en revistas científicas internacionales de alto impacto 📚",
                "Membresía vitalicia en la red de Humboldt Fellows 🌐"
            ],
            "requirements": [
                "Título de Doctorado (PhD) obtenido en los últimos 4 a 12 años",
                "Historial sobresaliente de publicaciones en revistas internacionales",
                "Proyecto de investigación original acordado con anfitrión en Alemania"
            ],
            "benefits_json": [
                "Estipendio mensual de 2.600€ (Postdoc) a 3.100€ (Experienced Researcher) 💶",
                "Subsidio adicional para cónyuge e hijos 👨‍👩‍👧",
                "Gastos de viaje internacional ida y vuelta ✈️",
                "Curso intensivo de idioma alemán pagado 🗣"
            ],
            "dates_info": "Convocatoria abierta todo el año (evaluaciones en Marzo, Julio y Noviembre)",
            "support_ai": [
                "Revisión de propuesta de investigación post-doctoral",
                "Estrategia de presentación ante el anfitrión Humboldt",
                "Asesoramiento para historial de publicaciones"
            ],
            "facebook_url": "https://www.facebook.com/HumboldtFoundation",
            "instagram_url": "https://www.instagram.com/humboldtfoundation",
            "youtube_url": "https://www.youtube.com/@HumboldtFoundation",
            "video_url": "https://www.youtube.com/watch?v=humboldt-fellowship",
            "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇩🇪", "title": "Investigadores PhD", "tags": ["Postdoctorado", "Excelencia académica"]},
                {"emoji": "💶", "title": "2.600€ a 3.100€/mes", "tags": ["Apoyo a familiares", "6 a 24 meses"]},
                {"emoji": "🌐", "title": "Red Humboldt", "tags": ["Prestigio mundial", "Sin cuotas por país"]}
            ],
            "testimonials": [
                {"name": "Dra. Patricia Soruco", "country": "🇧🇴 Bolivia", "year": "2022", "university": "Humboldt University Berlin", "program": "Investigación Postdoctoral en Química", "quote": "La Fundación Humboldt ofrece libertad de investigación y un apoyo familiar formidable."}
            ],
            "faq": [
                {"question": "¿Cuándo se puede postular a la Humboldt Fellowship?", "answer": "La convocatoria está abierta los 365 días del año. Los comités de evaluación se reúnen 3 veces al año (Marzo, Julio y Noviembre)."},
                {"question": "¿Hay cuotas fijas por país?", "answer": "No. La selección se basa 100% en el mérito y la calidad del perfil del investigador."}]
        },
        {
            "title": "Fulbright Visiting Scholar Program",
            "slug": "fulbright-visiting-scholar-beca",
            "type": "scholarship",
            "organization": "Gobierno de los Estados Unidos (Embajada de EE.UU.)",
            "organization_name": "Fulbright EE.UU.",
            "country": "Estados Unidos",
            "city": "Universidades de Estados Unidos",
            "institution": "Universidades e Institutos de EE.UU.",
            "level": "Investigación / Docencia Académica",
            "funding_type": "Parcial o Total",
            "area": "Todas las disciplinas académicas",
            "language": "Inglés (TOEFL/IELTS)",
            "duration": "3 a 9 meses",
            "deadline": "2026-06-30",
            "official_url": "https://bo.usembassy.gov/es/intercambio-educativo/",
            "short_description": "Permite a académicos y profesionales bolivianos realizar investigaciones avanzadas en universidades de EE.UU. por 3 a 9 meses.",
            "description": "Permite a académicos y profesionales bolivianos con amplia experiencia realizar investigaciones avanzadas en universidades de los Estados Unidos.\n\nEs una oportunidad para crear redes de contacto académicas de alto nivel entre Bolivia y EE. UU. Cubre estipendio de manutención, pasajes aéreos y seguro médico.",
            "eligibility": "Docentes universitarios, investigadores y profesionales bolivianos con título de maestría o doctorado y proyecto de investigación definido.",
            "benefits": "Estipendio mensual de manutención, pasajes aéreos internacionales ida y vuelta, seguro médico integral.",
            "slots": 5,
            "status": "approved",
            "activities": [
                "Investigación avanzada en universidades estadounidenses 🇺🇸",
                "Networking académico con profesores e investigadores de EE.UU. 🤝",
                "Conferencias y seminarios especializados 🎓"
            ],
            "requirements": [
                "Nacionalidad boliviana",
                "Título de Maestría o Doctorado",
                "Proyecto de investigación definido con propuesta sólida",
                "Excelente nivel de inglés fluido",
                "Compromiso formal de retorno a Bolivia al finalizar"
            ],
            "benefits_json": [
                "Estipendio de manutención en EE.UU. 💰",
                "Pasajes aéreos ida y vuelta ✈️",
                "Seguro médico y de accidentes 🏥",
                "Red global de contactos Fulbright 🇺🇸"
            ],
            "dates_info": "Convocatoria anual: Cierre entre Mayo y Junio de cada año",
            "support_ai": [
                "Estructuración del proyecto de investigación para EE.UU.",
                "Redacción de carta de presentación institucional",
                "Simulación de entrevista con Embajada de EE.UU."
            ],
            "facebook_url": "https://www.facebook.com/bolivia.usembassy",
            "instagram_url": "https://www.instagram.com/usembassybolivia",
            "youtube_url": "https://www.youtube.com/@usembassybolivia",
            "video_url": "https://www.youtube.com/watch?v=fulbright-visiting",
            "image_url": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇺🇸", "title": "Investigadores PhD/MSc", "tags": ["Docentes Universitarios", "Investigación avanzada"]},
                {"emoji": "🔬", "title": "Proyectos de Impacto", "tags": ["3 a 9 meses", "Universidades de EE.UU."]},
                {"emoji": "🤝", "title": "Retorno a Bolivia", "tags": ["Networking científico", "Convenios Bilaterales"]}
            ],
            "testimonials": [
                {"name": "Dr. Sergio Miranda", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Harvard University", "program": "Visiting Scholar", "quote": "Establecer nexos con laboratorios en EE.UU. abrió oportunidades gigantes para nuestra facultad en Bolivia."}
            ],
            "faq": [
                {"question": "¿Quiénes pueden postular?", "answer": "Docentes universitarios e investigadores bolivianos con grado de Maestría o Doctorado."},
                {"question": "¿Cuál es la duración del programa?", "answer": "Tiene una duración de 3 a 9 meses académicos."}]
        },
        {
            "title": "Becas de Investigación del Gobierno Suizo",
            "slug": "suiza-research-fellowship-beca",
            "type": "scholarship",
            "organization": "Gobierno de Suiza (SBFI)",
            "organization_name": "Gobierno de Suiza",
            "country": "Suiza",
            "city": "Zúrich, Ginebra, Lausana, Basilea",
            "institution": "Universidades e Institutos Politécnicos de Suiza",
            "level": "Investigación / Posgrado",
            "funding_type": "100% completa",
            "area": "Biotecnología, Química, Física, Ingeniería, Salud",
            "language": "Inglés / Francés / Alemán",
            "duration": "Hasta 12 meses",
            "deadline": "2026-11-15",
            "official_url": "https://www.sbfi.admin.ch/scholarships_eng",
            "short_description": "Becas del Gobierno Suizo para realizar estancias de investigación de posgrado en instituciones de élite mundial en Suiza.",
            "description": "Destinadas a investigadores que deseen realizar una investigación de posgrado en Suiza sin necesariamente obtener un título suizo.\n\nSuiza es líder mundial en biotecnología, química y física; es una oportunidad de oro para investigadores en esas áreas. Cubre un estipendio mensual de 1.920 CHF, seguro médico y gastos de viaje.",
            "eligibility": "Investigadores bolivianos con título de maestría o doctorado, menores de 35 años (para posgrado), con proyecto de alta calidad y carta de aceptación suiza.",
            "benefits": "Estipendio mensual de 1.920 CHF, seguro médico integral, alojamiento subsidiado y gastos de viaje aéreo.",
            "slots": 8,
            "status": "approved",
            "activities": [
                "Investigación avanzada en institutos de Suiza (EPFL, ETH Zürich, UNIGE) 🇨🇭",
                "Acceso a infraestructura científica de vanguardia mundial 🔬",
                "Colaboración con grupos de investigación internacionales 🤝"
            ],
            "requirements": [
                "Nacionalidad boliviana",
                "Título de Maestría o Doctorado",
                "Tener menos de 35 años al momento de postular (para nivel posgrado)",
                "Proyecto de investigación de alta calidad científica",
                "Carta de aceptación firmada por un profesor en una universidad suiza"
            ],
            "benefits_json": [
                "Estipendio mensual de 1.920 CHF (manutención en Suiza) 🇨🇭",
                "Seguro de salud y accidentes completo 🏥",
                "Pasajes aéreos internacionales ida y vuelta ✈️"
            ],
            "dates_info": "Convocatoria anual: Cierre regular en Noviembre",
            "support_ai": [
                "Redacción de propuesta de investigación según formato SBFI",
                "Plantillas de contacto para docentes en ETH / EPFL / UNIGE",
                "Revisión de expediente académico"
            ],
            "facebook_url": "https://www.facebook.com/SwissGov",
            "instagram_url": "https://www.instagram.com/swissembassy",
            "youtube_url": "https://www.youtube.com/@SwissGov",
            "video_url": "https://www.youtube.com/watch?v=swiss-research",
            "image_url": "https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇨🇭", "title": "Investigación en Suiza", "tags": ["ETH / EPFL", "Líderes en ciencia"]},
                {"emoji": "🔬", "title": "Biotecnología & Física", "tags": ["12 meses", "1.920 CHF/mes"]},
                {"emoji": "📊", "title": "<35 Años", "tags": ["Maestría o PhD", "Carta de aceptación suiza"]}
            ],
            "testimonials": [
                {"name": "Dr. Raúl Camacho", "country": "🇧🇴 Bolivia", "year": "2023", "university": "ETH Zürich", "program": "Research Fellow", "quote": "La infraestructura suiza para ciencia e ingeniería no tiene comparación en el mundo."}
            ],
            "faq": [
                {"question": "¿Es obligatorio obtener un título en Suiza?", "answer": "No. La beca está diseñada para estancias de investigación de posgrado sin necesidad de titularse en Suiza."},
                {"question": "¿Cuál es el estipendio mensual?", "answer": "El Gobierno Suizo otorga 1.920 CHF mensuales más seguro y gastos de viaje."}]
        },
        {
            "title": "Becas TWAS para Países en Desarrollo",
            "slug": "twas-desarrollo-beca",
            "type": "scholarship",
            "organization": "The World Academy of Sciences (TWAS / CNPq)",
            "organization_name": "Academia Mundial de Ciencias",
            "country": "Brasil (Sur Global)",
            "city": "Universidades de Brasil, México, India",
            "institution": "Institutos del Sur Global (ej. Brasil / CNPq)",
            "level": "Doctorado / Postdoctorado",
            "funding_type": "100% completa",
            "area": "Ciencias Naturales, Biología, Química, Física, Agronomía",
            "language": "Inglés / Portugués / Español",
            "duration": "3 a 12 meses",
            "deadline": "2026-09-15",
            "official_url": "https://twas.org/opportunities/fellowships",
            "short_description": "Programa de la Academia Mundial de Ciencias para estancias de investigación en países del Sur Global (Brasil, México, India).",
            "description": "Programa de la Academia Mundial de Ciencias (TWAS) para que investigadores de países del sur global (como Bolivia) realicen estancias de investigación en países como Brasil, China, India o México.\n\nEs excelente para fortalecer la cooperación científica regional, especialmente los convenios TWAS-CNPq en Brasil. Cubre manutención completa y pasajes aéreos.",
            "eligibility": "Estudiantes de doctorado o doctores jóvenes en ciencias naturales con nacionalidad boliviana y trabajando en investigación en su país de origen.",
            "benefits": "Manutención mensual pagada por el país anfitrión, cobertura de pasajes aéreos y seguro de investigación.",
            "slots": 15,
            "status": "approved",
            "activities": [
                "Estancia de investigación doctoral o posdoctoral en el Sur Global 🇧🇷",
                "Uso de laboratorios y experimentos compartidos 🔬",
                "Publicación de papers en cooperación regional 📚"
            ],
            "requirements": [
                "Nacionalidad de un país en desarrollo (Bolivia elegible)",
                "Estar inscrito en un doctorado o poseer título de PhD joven",
                "Estar trabajando activamente en investigación en Bolivia",
                "Dominio del idioma del país de destino"
            ],
            "benefits_json": [
                "Manutención mensual completa 💰",
                "Pasajes aéreos cubiertos por TWAS o convenio ✈️",
                "Acceso a redes científicas del Sur Global 🌍"
            ],
            "dates_info": "Convocatorias anuales variables entre Junio y Septiembre",
            "support_ai": [
                "Selección de convenios TWAS prioritarios (ej. TWAS-CNPq Brasil)",
                "Formulación de plan de trabajo científico",
                "Revisión de perfil académico"
            ],
            "facebook_url": "https://www.facebook.com/TWAS.Science",
            "instagram_url": "https://www.instagram.com/twasnews",
            "youtube_url": "https://www.youtube.com/@twas_science",
            "video_url": "https://www.youtube.com/watch?v=twas-video",
            "image_url": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇧🇷", "title": "Investigación Sur Global", "tags": ["Convenio Brasil", "CNPq / TWAS"]},
                {"emoji": "🔬", "title": "Ciencias Naturales", "tags": ["Doctorandos", "3 a 12 meses"]},
                {"emoji": "🌍", "title": "Cooperación Regional", "tags": ["Elegible Bolivia", "100% Financiado"]}
            ],
            "testimonials": [
                {"name": "Dra. Karen Justiniano", "country": "🇧🇴 Bolivia", "year": "2023", "university": "UNICAMP Brasil", "program": "TWAS Fellow", "quote": "Los convenios TWAS te conectan con los centros de investigación más avanzados de Sudamérica."}
            ],
            "faq": [
                {"question": "¿Qué países son los más comunes para bolivianos en TWAS?", "answer": "Brasil es el destino más frecuente mediante el convenio histórico TWAS-CNPq."},
                {"question": "¿Cubre pasajes aéreos?", "answer": "Sí, en la mayoría de los convenios TWAS se cubre la manutención y el pasaje internacional."}]
        },
        {
            "title": "Emerging Leaders in the Americas Program (ELAP)",
            "slug": "elap-canada-beca",
            "type": "scholarship",
            "organization": "Gobierno de Canadá (EduCanada)",
            "organization_name": "Gobierno de Canadá",
            "country": "Canadá",
            "city": "Toronto, Vancouver, Montreal, Calgary",
            "institution": "Universidades de Canadá",
            "level": "Pregrado y Posgrado",
            "funding_type": "100% completa",
            "area": "Multidisciplinaria",
            "language": "Inglés / Francés",
            "duration": "4 meses (semestre) o 5-6 meses (investigación)",
            "deadline": "2027-03-20",
            "official_url": "https://www.educanada.ca/scholarships-bourses/can/institutions/elap-pfla.aspx?lang=eng",
            "short_description": "Becas del gobierno canadiense para realizar intercambios de 4 a 6 meses en universidades de Canadá para líderes emergentes.",
            "description": "Becas del gobierno canadiense para que estudiantes de Latinoamérica realicen intercambios de corta duración en universidades canadienses para fortalecer sus habilidades de liderazgo.\n\nOfrece asignaciones de entre 8,200 y 11,100 CAD dependiendo del nivel para cubrir vuelos, visado, seguro médico y manutención mensual.",
            "eligibility": "Estudiantes de pregrado o posgrado inscritos en universidades bolivianas que tengan un convenio previo con una universidad canadiense.",
            "benefits": "Asignación total de 8.200 CAD (Pregrado/Maestría) a 11.100 CAD (Doctorado/Investigación) para pasajes, visa, seguro y estancia.",
            "slots": 10,
            "status": "approved",
            "activities": [
                "Semestre académico de intercambio en Canadá 🇨🇦",
                "Investigación o estudio de curso completo en campus canadiense 📚",
                "Formación en liderazgo y networking internacional 🤝"
            ],
            "requirements": [
                "Estar inscrito como estudiante activo en universidad boliviana",
                "Existencia de convenio previo de intercambio con universidad canadiense",
                "Nominación directa realizada por la oficina internacional canadiense"
            ],
            "benefits_json": [
                "Beca completa de 8.200 a 11.100 CAD 💰",
                "Pasajes aéreos ida y vuelta ✈️",
                "Visa de estudiante y seguro de salud 🏥",
                "Estancia de 4 a 6 meses en Canadá 🇨🇦"
            ],
            "dates_info": "Convocatoria anual: Cierre en Marzo (postulación gestionada por universidad canadiense)",
            "support_ai": [
                "Verificación de convenios entre universidades bolivianas y canadienses",
                "Redacción de Carta de Intención para oficina de relaciones internacionales",
                "Certificación de promedio de calificaciones"
            ],
            "facebook_url": "https://www.facebook.com/EduCanada.Official",
            "instagram_url": "https://www.instagram.com/educanada.official",
            "youtube_url": "https://www.youtube.com/@EduCanadaOfficial",
            "video_url": "https://www.youtube.com/watch?v=elap-canada",
            "image_url": "https://images.unsplash.com/photo-1517935703635-27c735286572?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇨🇦", "title": "Intercambio en Canadá", "tags": ["4 a 6 meses", "8.200 - 11.100 CAD"]},
                {"emoji": "🎓", "title": "Pregrado y Posgrado", "tags": ["Estudiantes en Bolivia", "Convenios bilatelares"]},
                {"emoji": "🍁", "title": "Líderes Emergentes", "tags": ["EduCanada", "100% Financiado"]}
            ],
            "testimonials": [
                {"name": "Camila Zenteno", "country": "🇧🇴 Bolivia", "year": "2023", "university": "University of Alberta", "program": "ELAP Scholar", "quote": "ELAP te da la oportunidad de vivir un semestre de intercambio en Canadá con financiamiento completo."}
            ],
            "faq": [
                {"question": "¿Puedo postularme yo mismo directamente?", "answer": "No. La postulación la realiza la oficina de relaciones internacionales de la universidad canadiense asociada."},
                {"question": "¿Cuál es el monto de la beca?", "answer": "Otorga 8.200 CAD para 4 meses de grado/posgrado y 11.100 CAD para 5-6 meses de investigación."}]
        },
        {
            "title": "Programa SUSI (Study of the U.S. Institutes)",
            "slug": "susi-eeuu-beca",
            "type": "scholarship",
            "organization": "Departamento de Estado de los EE. UU. / Embajada de EE.UU.",
            "organization_name": "Departamento de Estado EE.UU.",
            "country": "Estados Unidos",
            "city": "Universidades e Institutos de EE.UU.",
            "institution": "Institutos Académicos de EE.UU.",
            "level": "Curso Corto / Liderazgo",
            "funding_type": "100% completa",
            "area": "Liderazgo, Políticas Públicas, Cultura y Sociedad",
            "language": "Inglés / Español (según categoría)",
            "duration": "5 a 6 semanas",
            "deadline": "2026-12-20",
            "official_url": "https://bo.usembassy.gov/es/education-exchanges-es/",
            "short_description": "Programas académicos intensivos de 5 a 6 semanas en EE.UU. para líderes estudiantiles universitarios y educadores.",
            "description": "Programas académicos intensivos que buscan proporcionar a líderes estudiantiles y educadores una comprensión profunda de la sociedad, cultura y valores de EE. UU. a través de seminarios y visitas culturales.\n\nEs una experiencia de inmersión cultural y académica de gran impacto. Cubre vuelos, alojamiento, comidas, estipendio para libros y seguro médico.",
            "eligibility": "Jóvenes líderes universitarios bolivianos (18-25 años) y educadores o administradores académicos con buen desempeño.",
            "benefits": "Pasajes aéreos ida y vuelta, alojamiento completo, alimentación, estipendio de libros, visitas culturales y seguro médico.",
            "slots": 12,
            "status": "approved",
            "activities": [
                "Seminarios académicos e inmersión cultural en EE.UU. 🇺🇸",
                "Visitas a instituciones gubernamentales y comunitarias 🏛️",
                "Red de líderes de todo el continente americano 🤝"
            ],
            "requirements": [
                "Nacionalidad boliviana",
                "Tener entre 18 y 25 años (para la categoría de líderes estudiantiles)",
                "Liderazgo demostrado en su universidad o comunidad",
                "Buen rendimiento académico",
                "Dominio de inglés (salvo programas específicos en español para líderes afro/indígenas)"
            ],
            "benefits_json": [
                "Pasajes aéreos internacionales ida y vuelta ✈️",
                "Alojamiento y alimentación 100% cubiertos 🏠",
                "Estipendio para libros y materiales 📚",
                "Seguro médico de viaje 🏥"
            ],
            "dates_info": "Convocatoria anual: Abre entre Noviembre y Diciembre de cada año",
            "support_ai": [
                "Estructuración de ensayo de liderazgo y compromiso social",
                "Preparación de entrevista presencial o virtual con la Embajada",
                "Certificación de liderazgo comunitario"
            ],
            "facebook_url": "https://www.facebook.com/bolivia.usembassy",
            "instagram_url": "https://www.instagram.com/usembassybolivia",
            "youtube_url": "https://www.youtube.com/@usembassybolivia",
            "video_url": "https://www.youtube.com/watch?v=susi-usa",
            "image_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇺🇸", "title": "Líderes 18-25 Años", "tags": ["Estudiantes universitarios", "5 a 6 semanas"]},
                {"emoji": "🏛️", "title": "Inmersión en EE.UU.", "tags": ["Seminarios académicos", "Cultura y Sociedad"]},
                {"emoji": "✈️", "title": "100% Financiado", "tags": ["Vuelos", "Hospedaje", "Comida"]}
            ],
            "testimonials": [
                {"name": "Bruno Paredes", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Amherst College EE.UU.", "program": "SUSI Fellow", "quote": "SUSI es una experiencia de inmersión cultural de 5 semanas que cambia tu forma de ver el liderazgo."}
            ],
            "faq": [
                {"question": "¿Se necesita inglés fluido?", "answer": "Sí, para la mayoría de los programas. Existen algunas ramas específicas de liderazgo social en español."},
                {"question": "¿Cuánto dura la estancia en EE.UU.?", "answer": "Dura entre 5 y 6 semanas intensivas durante las vacaciones universitarias."}]
        },
        {
            "title": "Becas de la OEA - Cursos de Desarrollo Profesional",
            "slug": "oea-cursos-desarrollo-beca",
            "type": "scholarship",
            "organization": "Organización de los Estados Americanos (OEA / ONE)",
            "organization_name": "OEA",
            "country": "Américas (Modalidad Presencial y Online)",
            "city": "Washington D.C. / Varias ciudades de LATAM",
            "institution": "Instituciones Miembros de la OEA",
            "level": "Capacitación / Cursos Cortos",
            "funding_type": "Parcial o Total",
            "area": "Gobernabilidad, Educación, Ciencia, Sostenibilidad, TICs",
            "language": "Español / Inglés",
            "duration": "1 semana a 3 meses",
            "deadline": "2026-10-31",
            "official_url": "https://www.oas.org/es/becas/desarrollo_profesional.asp",
            "short_description": "Cursos técnicos y de actualización profesional de 1 semana a 3 meses financiados por la OEA en modalidad presencial y virtual.",
            "description": "Cursos impartidos en modalidad presencial o virtual por instituciones de excelencia de los países miembros de la OEA sobre temas de gobernabilidad, educación, ciencia y sostenibilidad.\n\nLa postulación se realiza a través de la oficina de enlace nacional en Bolivia (ONE). Ofrece financiamiento parcial o total según la convocatoria del curso.",
            "eligibility": "Ciudadanos bolivianos graduados universitarios o técnicos con experiencia laboral relevante en el área del curso.",
            "benefits": "Exención de matrícula, material del curso y, en modalidades presenciales, alojamiento y pasajes según el convenio.",
            "slots": 25,
            "status": "approved",
            "activities": [
                "Cursos cortos intensivos presenciales o virtuales 💻",
                "Capacitación en gobernabilidad, sostenibilidad y tecnología 📊",
                "Certificación oficial emitida por la OEA e instituciones socias 📜"
            ],
            "requirements": [
                "Ciudadanía boliviana",
                "Título universitario o técnico relevante",
                "Estar trabajando en un área afín al curso",
                "Tramitación a través de la Oficina Nacional de Enlace (ONE Bolivia)"
            ],
            "benefits_json": [
                "100% de beca en matrícula del curso 💸",
                "Modalidades virtuales de alta flexibilidad 💻",
                "Certificado internacional OEA 📜"
            ],
            "dates_info": "Convocatorias recurrentes abiertas durante todo el año",
            "support_ai": [
                "Filtrado de convocatorias abiertas del catálogo OEA",
                "Redacción de Justificación Profesional",
                "Apoyo en trámites con la Oficina Nacional de Enlace (ONE)"
            ],
            "facebook_url": "https://www.facebook.com/OEAoficial",
            "instagram_url": "https://www.instagram.com/oea_oficial",
            "youtube_url": "https://www.youtube.com/@OEAoficial",
            "video_url": "https://www.youtube.com/watch?v=oea-cursos",
            "image_url": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🌎", "title": "Cursos Cortos OEA", "tags": ["1 semana a 3 meses", "Presencial u Online"]},
                {"emoji": "💻", "title": "Actualización Profesional", "tags": ["Gobernabilidad", "Tecnología", "Educación"]},
                {"emoji": "📜", "title": "Certificación Oficial", "tags": ["Respaldo OEA", "Elegible Bolivia"]}
            ],
            "testimonials": [
                {"name": "Lic. Gonzalo Tapia", "country": "🇧🇴 Bolivia", "year": "2023", "university": "OEA Virtual", "program": "Curso de Gestión Pública", "quote": "Los cursos de la OEA son muy prácticos y te permiten capacitarte sin dejar de trabajar."}
            ],
            "faq": [
                {"question": "¿Dónde se tramita la postulación en Bolivia?", "answer": "Se realiza a través de la Oficina Nacional de Enlace (ONE) en Bolivia."},
                {"question": "¿Hay cursos virtuales?", "answer": "Sí, gran parte de la oferta de desarrollo profesional de la OEA se dicta en línea."}]
        },
        {
            "title": "Becas de Excelencia del Politécnico de Milán",
            "slug": "politecnico-milano-beca",
            "type": "scholarship",
            "organization": "Politecnico di Milano (POLIMI)",
            "organization_name": "POLIMI Italia",
            "country": "Italia",
            "city": "Milán, Como, Lecco",
            "institution": "Politecnico di Milano",
            "level": "Maestría (Master of Science)",
            "funding_type": "100% completa (Exención Matrícula + Estipendio)",
            "area": "Ingeniería, Arquitectura, Diseño",
            "language": "Inglés C1",
            "duration": "2 años académicos",
            "deadline": "2027-03-10",
            "official_url": "https://www.polimi.it/en/international-prospective-students/",
            "short_description": "Becas por mérito académico otorgadas por el Politecnico di Milano para maestrías en Ingeniería, Arquitectura y Diseño en Italia.",
            "description": "El Politecnico di Milano ofrece becas por mérito académico a los estudiantes internacionales más talentosos admitidos en programas de Master of Science (Maestría).\n\nNo se requiere una aplicación separada; el comité de admisiones evalúa automáticamente a todos los candidatos admitidos. Cubre exención total de matrícula más un estipendio de entre €5,000 y €10,000 anuales.",
            "eligibility": "Graduados en Ingeniería, Arquitectura o Diseño con un promedio académico sobresaliente y carta de admisión al POLIMI.",
            "benefits": "Exención 100% de tasas universitarias más estipendio anual de manutención (entre 5.000€ y 10.000€) y alojamiento en residencia.",
            "slots": 15,
            "status": "approved",
            "activities": [
                "Maestría de 2 años en el Politécnico de Milán 🇮🇹",
                "Proyectos en laboratorios de diseño e ingeniería italianos 🔬",
                "Conexión directa con la industria tecnológica y de diseño europea 🤝"
            ],
            "requirements": [
                "Título universitario en Ingeniería, Arquitectura o Diseño",
                "Promedio académico sobresaliente en la licenciatura",
                "Certificación de inglés (TOEFL/IELTS)",
                "Portafolio de proyectos (obligatorio para Arquitectura y Diseño)"
            ],
            "benefits_json": [
                "Exención 100% de matrícula universitaria (aprox 3.900€/año) 💸",
                "Estipendio económico de 5.000€ a 10.000€ anuales 💰",
                "Alojamiento en residencia universitaria de Milán 🏠"
            ],
            "dates_info": "Convocatoria anual: Evaluación automática de solicitudes cerradas en Marzo",
            "support_ai": [
                "Revisión de portafolio de Arquitectura / Diseño",
                "Traducción y formato de expediente académico para Italia",
                "Guía de aplicación en el portal de admisiones POLIMI"
            ],
            "facebook_url": "https://www.facebook.com/polimi",
            "instagram_url": "https://www.instagram.com/polimi",
            "youtube_url": "https://www.youtube.com/@polimi",
            "video_url": "https://www.youtube.com/watch?v=polimi-milan",
            "image_url": "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800&q=80",
            "is_demo": False,
            "ideal_profile": [
                {"emoji": "🇮🇹", "title": "Politécnico de Milán", "tags": ["Top 1 en Italia", "Ingeniería y Diseño"]},
                {"emoji": "📊", "title": "Evaluación Automática", "tags": ["Por mérito", "Sin formulario extra"]},
                {"emoji": "💶", "title": "Exención + 10.000€/año", "tags": ["Matrícula libre", "Estipendio"]}
            ],
            "testimonials": [
                {"name": "Arq. Mateo Vaca", "country": "🇧🇴 Bolivia", "year": "2023", "university": "Politecnico di Milano", "program": "MSc Architecture and Urban Design", "quote": "Milán es la capital del diseño mundial y la beca de excelencia del POLIMI te premia por tu promedio."}
            ],
            "faq": [
                {"question": "¿Debo llenar un formulario separado para la beca del POLIMI?", "answer": "No. El comité evalúa automáticamente a todos los postulantes admitidos a la maestría."},
                {"question": "¿En qué idioma se imparten las maestrías?", "answer": "La gran mayoría de las maestrías internacionales del POLIMI se dictan totalmente en inglés."}]
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
            # Convert deadline string to date object if present
            if isinstance(seed_data.get("deadline"), str):
                try:
                    seed_data["deadline"] = datetime.datetime.strptime(seed_data["deadline"], "%Y-%m-%d").date()
                except Exception:
                    seed_data["deadline"] = None

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
                for k, v in seed_data.items():
                    setattr(existing, k, v)
                existing.organization_id = org_id
                existing.status = "approved"
                db.add(existing)
                logger.info(f"Ensured seed program: '{seed_data['title']}' ({seed_data['slug']}) is updated & approved linked to Org ID {existing.organization_id}")
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

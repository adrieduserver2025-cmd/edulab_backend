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

import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def format_student_profile(profile: Any) -> str:
    """
    Formats a StudentProfile SQLAlchemy object into a clean text representation for the LLM.
    """
    if not profile:
        return "No profile details available."
    if isinstance(profile, str):
        return profile

    lines = []
    lines.append(f"Ubicación: {profile.city}, {profile.country}")
    lines.append(f"Nivel de Educación: {profile.education_level}")
    if profile.current_institution:
        lines.append(f"Institución Actual: {profile.current_institution}")
    lines.append(f"Área de Especialidad: {profile.area}")
    lines.append(f"Nivel de Inglés: {profile.english_level}")
    if profile.other_languages:
        lines.append(f"Otros Idiomas: {', '.join(profile.other_languages)}")
    if profile.interests:
        lines.append(f"Intereses: {', '.join(profile.interests)}")
    if profile.bio:
        lines.append(f"Biografía/Resumen: {profile.bio}")

    if profile.work_experience:
        lines.append("\nExperiencia Laboral:")
        for idx, job in enumerate(profile.work_experience, 1):
            role = job.get("role", "N/A")
            company = job.get("company", "N/A")
            desc = job.get("description", "")
            lines.append(f"  {idx}. {role} en {company} - {desc}")

    if profile.volunteer_experience:
        lines.append("\nExperiencia de Voluntariado:")
        for idx, vol in enumerate(profile.volunteer_experience, 1):
            role = vol.get("role", "N/A")
            org = vol.get("organization", "N/A")
            desc = vol.get("description", "")
            lines.append(f"  {idx}. {role} en {org} - {desc}")

    return "\n".join(lines)

def format_winners_profiles(winners: List[Any]) -> str:
    """
    Formats a list of accepted applications and their student profiles into text.
    """
    if not winners:
        return "No se encontraron perfiles de ganadores previos registrados en el sistema."

    blocks = []
    for idx, win_app in enumerate(winners, 1):
        profile = getattr(win_app, "student_profile", None)
        profile_text = format_student_profile(profile) if profile else "Detalles de perfil no disponibles."
        letter = win_app.motivation_letter_draft or getattr(profile, "general_motivation_letter", "No disponible")
        
        block = f"--- GANADOR #{idx} ---\n{profile_text}\n\nCarta de Motivación de este Ganador:\n{letter}"
        blocks.append(block)
    
    return "\n\n".join(blocks)

def sanitize_improved_letter(letter_text: str, program: Any, profile: Any) -> str:
    if not letter_text:
        return letter_text

    org_name = getattr(program, "organization", "Comité de Selección") if hasattr(program, "organization") and getattr(program, "organization") else "Comité de Selección"
    prog_title = getattr(program, "title", "Programa de Beca") if hasattr(program, "title") and getattr(program, "title") else "Programa de Beca"

    city_country = "Santa Cruz, Bolivia"
    if not isinstance(profile, str) and hasattr(profile, "city") and getattr(profile, "city"):
        country = getattr(profile, "country", "Bolivia") or "Bolivia"
        city_country = f"{profile.city}, {country}"
    elif isinstance(profile, str) and "Ubicación:" in profile:
        for l in profile.split("\n"):
            if l.startswith("Ubicación:"):
                city_country = l.replace("Ubicación:", "").strip()

    import datetime
    months_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    now = datetime.datetime.now()
    date_str = f"{now.day} de {months_es[now.month - 1]} de {now.year}"

    replacements = [
        ("LUGAR, FECHA", f"**{city_country}**\n**{date_str}**"),
        ("[LUGAR, FECHA]", f"**{city_country}**\n**{date_str}**"),
        ("[Lugar, Fecha]", f"**{city_country}**\n**{date_str}**"),
        ("[NOMBRE DEL DESTINATARIO]", f"**Comité de Selección de {org_name}**"),
        ("[Nombre del Destinatario]", f"Comité de Selección de {org_name}"),
        ("[Posición]", f"Dirección de Admisiones y Becas"),
        ("[Institución]", f"**{org_name}**"),
        ("[Dirección]", f"Convocatoria: {prog_title}"),
        ("Estimado/a [Nombre del Destinatario],", f"Estimados miembros del Comité de Selección de {org_name},"),
        ("Estimado/a [Nombre],", f"Estimados miembros del Comité de Selección de {org_name},"),
        ("Estimado [Nombre del Destinatario],", f"Estimados miembros del Comité de Selección de {org_name},"),
        ("Estimados miembros de [Institución],", f"Estimados miembros del Comité de Selección de {org_name},"),
    ]

    sanitized = letter_text
    for placeholder, real_val in replacements:
        sanitized = sanitized.replace(placeholder, real_val)

    return sanitized


async def generate_ai_review(
    program: Any,
    profile: Any,
    motivation_letter: Optional[str],
    winners: List[Any]
) -> Dict[str, Any]:
    """
    Calls OpenAI to review and compare the applicant's CV/Profile and Motivation Letter
    against the opportunity's requirements and successful applicants (winners).
    """
    api_key = settings.OPENAI_API_KEY
    is_mock = not api_key or api_key.startswith("mock-") or api_key.startswith("your-")

    # Format candidate, program, location and date
    candidate_profile_str = format_student_profile(profile)
    motivation_letter_str = motivation_letter or "No proporcionada por el estudiante."
    
    org_name = getattr(program, "organization", "Organización Convocante") if hasattr(program, "organization") and getattr(program, "organization") else "Organización Convocante"
    prog_title = getattr(program, "title", "Programa de Oportunidad") if hasattr(program, "title") and getattr(program, "title") else "Programa de Oportunidad"

    city_country = "Santa Cruz, Bolivia"
    if not isinstance(profile, str) and hasattr(profile, "city") and getattr(profile, "city"):
        country = getattr(profile, "country", "Bolivia") or "Bolivia"
        city_country = f"{profile.city}, {country}"
    elif isinstance(profile, str) and "Ubicación:" in profile:
        for l in profile.split("\n"):
            if l.startswith("Ubicación:"):
                city_country = l.replace("Ubicación:", "").strip()

    import datetime
    months_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    now = datetime.datetime.now()
    current_date_es = f"{now.day} de {months_es[now.month - 1]} de {now.year}"

    program_info = (
        f"Título: {prog_title}\n"
        f"Organización/Institución: {org_name}\n"
        f"Descripción: {getattr(program, 'description', '')}\n"
        f"Tipo de Oportunidad: {getattr(program, 'type', '')}\n"
        f"Requisitos: {getattr(program, 'requirements', 'No especificados')}\n"
        f"Perfil Ideal: {getattr(program, 'ideal_profile', 'No especificado')}"
    )

    winners_data_str = format_winners_profiles(winners)

    if is_mock:
        logger.info("🤖 OPENAI_API_KEY is not configured or in mock mode. Generating mock review report.")
        # Return a high quality mock response using REAL program and profile parameters
        score = 82 if "beca" in prog_title.lower() else 75
        area_str = "tu area de especialidad" if isinstance(profile, str) else getattr(profile, "area", "tu área de especialidad")
        
        mock_letter = (
            f"**{city_country}**\n"
            f"**{current_date_es}**\n\n"
            f"**Comité de Selección de Becas y Admisiones**\n"
            f"**{org_name}**\n"
            f"**Programa: {prog_title}**\n\n"
            f"Estimados miembros del Comité de Selección de {org_name},\n\n"
            f"Me dirijo a ustedes con gran entusiasmo para presentar mi candidatura a la convocatoria de **{prog_title}**. Como estudiante enfocado en mi área académica en Bolivia, he alineado mi trayectoria hacia la innovación técnica y el impacto social tangible en mi comunidad.\n\n"
            f"A lo largo de mi formación, he buscado constantemente aplicar los conocimientos en proyectos prácticos de alcance real. Destacan iniciativas de desarrollo de software accesible e intervenciones comunitarias como mentor de tecnología, donde logré liderar talleres para más de 50 jóvenes, incrementando significativamente su retención y aprendizaje práctico.\n\n"
            f"Mi interés en **{prog_title}** radica en el prestigio de **{org_name}** y el impacto transformador de su plan de estudios. Estoy convencido de que sumergirme en esta oportunidad potenciará mis competencias con estándares internacionales.\n\n"
            f"Al finalizar la oportunidad, mi compromiso es replicar el conocimiento adquirido impulsando nuevos talleres e iniciativas en Bolivia. Agradezco su tiempo y consideración.\n\n"
            f"Atentamente,\n\n"
            f"**Sebastián Soliz Paniagua**\n"
            f"{area_str} | postulaciones@edulab.bo"
        )

        return {
            "score": score,
            "strengths": [
                f"Sólida formación y especialidad en {area_str}.",
                "Experiencia de voluntariado alineada con los valores del programa.",
                "Carta de motivación clara y estructurada."
            ],
            "weaknesses": [
                "Nivel de inglés podría reforzarse a un nivel superior si el programa es internacional.",
                "Falta mayor cuantificación de logros en la experiencia laboral detallada.",
                "La carta de motivación es un poco genérica en el párrafo de cierre."
            ],
            "recommendations_cv": [
                "Describe tus logros laborales usando métricas cuantitativas (ej. 'incrementé la eficiencia un 15%').",
                "Destaca certificaciones adicionales o cursos completados relevantes a la temática del programa.",
                "Actualiza tu sección de idiomas para detallar tu nivel conversacional."
            ],
            "recommendations_letter": [
                f"Haz énfasis explícito en cómo planeas aportar a la organización '{org_name}'.",
                "Conecta más íntimamente tus proyectos de voluntariado pasados con las actividades del programa.",
                "Mejora el gancho del primer párrafo para que sea más personal y memorable."
            ],
            "comparison_summary": (
                "Tu perfil tiene alta afinidad con los postulantes ganadores en el área de voluntariado. "
                "Sin embargo, los ganadores previos suelen poseer una descripción más robusta de su impacto "
                "profesional/académico y cartas de motivación con un tono de liderazgo más pronunciado."
            ),
            "improved_cv": (
                "# Sebastián Soliz Paniagua\n"
                f"**{area_str}** | {city_country}\n\n"
                "## Resumen Profesional\n"
                "Estudiante altamente motivado con formación técnica sólida y pasión por la tecnología y la innovación social. "
                "Poseo experiencia práctica en desarrollo de proyectos y un firme compromiso social demostrado en actividades de liderazgo y voluntariado.\n\n"
                "## Experiencia Laboral\n"
                "**Desarrollador de Proyectos Independiente** | *Freelance*\n"
                "*Enero 2025 - Presente*\n"
                "- Diseñé y desarrollé soluciones tecnológicas web optimizadas, mejorando la accesibilidad en un 30%.\n"
                "- Creé prototipos de sensores asistenciales para personas no videntes, incrementando la autonomía en un 25% durante pruebas.\n\n"
                "## Experiencia de Voluntariado\n"
                "**Mentor de Programación** | *CoderDojo / Voluntarios*\n"
                "*Junio 2024 - Presente*\n"
                "- Enseñé principios de lógica de programación y desarrollo web a más de 20 jóvenes en comunidades vulnerables.\n"
                "- Elaboré material pedagógico interactivo incrementando el interés tecnológico de los estudiantes.\n\n"
                "## Educación\n"
                "**Ingeniería de Sistemas** | *Universidad Escuela Militar de Ingeniería*\n"
                "*Promedio: 8.7 / 10*\n\n"
                "## Habilidades e Idiomas\n"
                "- **Idiomas:** Español (Nativo), Inglés (Intermedio B2).\n"
                "- **Habilidades Técnicas:** JavaScript, React, Python, PostgreSQL, HTML/CSS.\n"
                "- **Habilidades Blandas:** Liderazgo, resolución de problemas, pensamiento crítico."
            ),
            "improved_letter": mock_letter
        }

    # Initialize OpenAI Client
    client = AsyncOpenAI(api_key=api_key)

    system_prompt = (
        "Eres un asesor experto en becas, intercambios y voluntariados internacionales de EDULAB. "
        "Tu tarea es evaluar el perfil profesional (CV estructurado) y la carta de motivación de un postulante "
        "para un programa específico, y compararlo con perfiles de postulantes exitosos (ganadores/aceptados) si están disponibles. "
        "Debes responder en un formato JSON estructurado estricto con los siguientes campos en español:\n"
        "{\n"
        "  \"score\": 85, // número del 0 al 100 indicando la compatibilidad general\n"
        "  \"strengths\": [\"Fortaleza 1\", \"Fortaleza 2\"],\n"
        "  \"weaknesses\": [\"Debilidad/Brecha 1\", \"Debilidad/Brecha 2\"],\n"
        "  \"recommendations_cv\": [\"Recomendación de mejora de CV 1\"],\n"
        "  \"recommendations_letter\": [\"Recomendación de mejora de Carta 1\"],\n"
        "  \"comparison_summary\": \"Texto narrativo analizando la comparación con ganadores previos.\",\n"
        "  \"improved_cv\": \"Una propuesta del CV del postulante optimizado bajo el ESTÁNDAR HARVARD RESUME FORMAT (en Markdown), con encabezado centrado, secciones formales (EDUCACIÓN, EXPERIENCIA PROFESIONAL, LIDERAZGO Y VOLUNTARIADO, HABILIDADES), fechas alineadas y viñetas iniciadas con verbos de acción fuertes.\",\n"
        "  \"improved_letter\": \"Una propuesta de CARTA DE MOTIVACIÓN GANADORA COMPLETA (400 a 500 palabras en Markdown). REGLA CRÍTICA Y OBLIGATORIA: NUNCA INCLUYAS CORCHETES O TEXTOS PLACEHOLDER COMO [LUGAR, FECHA], [NOMBRE DEL DESTINATARIO], [Posición], [Institución], [Dirección], O Estimado/a [Nombre]. DEBES REEMPLAZARLOS SIEMPRE Y AUTOMÁTICAMENTE USANDO LOS DATOS REALES PROVISTOS EN EL PROMPT (Ciudad y país del postulante, fecha actual, Organización e Institución del programa).\"\n"
        "}"
    )

    user_content = (
        f"=== DATOS OBLIGATORIOS PARA EL ENCABEZADO Y CONTENIDO DE LA CARTA ===\n"
        f"- Ciudad y País real del Postulante: {city_country}\n"
        f"- Fecha de Hoy: {current_date_es}\n"
        f"- Institución / Organización Destino: {org_name}\n"
        f"- Nombre de la Convocatoria/Programa: {prog_title}\n\n"
        f"=== DATOS DE LA OPORTUNIDAD ===\n"
        f"{program_info}\n\n"
        f"=== PERFIL/CV DEL POSTULANTE ===\n"
        f"{candidate_profile_str}\n\n"
        f"=== CARTA DE MOTIVACIÓN DEL POSTULANTE ===\n"
        f"{motivation_letter_str}\n\n"
        f"=== PERFILES Y CARTAS DE GANADORES EXITOSOS (REFERENCIAS) ===\n"
        f"{winners_data_str}\n\n"
        f"Por favor realiza la revisión y comparación. RECUERDA: En 'improved_letter' NO USAR CORCHETES NI PLACEHOLDERS, coloca directamente los datos de la institución, programa, ciudad y fecha actual."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Post-sanitize letter to ensure no placeholder brackets leak through
        if "improved_letter" in result and result["improved_letter"]:
            result["improved_letter"] = sanitize_improved_letter(result["improved_letter"], program, profile)

        return result

    except Exception as e:
        logger.error(f"❌ Error al llamar a la API de OpenAI: {e}")
        # Fallback to structured dict in case of API error
        return {
            "score": 50,
            "strengths": ["Perfil con potencial de desarrollo."],
            "weaknesses": ["Error de conexión con el motor de IA en este momento."],
            "recommendations_cv": ["Por favor intente nuevamente más tarde."],
            "recommendations_letter": ["Por favor intente nuevamente más tarde."],
            "comparison_summary": f"La revisión automática no pudo completarse debido a un error técnico: {str(e)}",
            "improved_cv": "",
            "improved_letter": ""
        }

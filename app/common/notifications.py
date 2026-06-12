import logging

logger = logging.getLogger("uvicorn.error")

class MockEmailService:
    @staticmethod
    def send_registration_under_review_email(email: str, org_name: str) -> None:
        """
        Sends an email indicating the organization registration request is received and under review.
        """
        subject = "EDULAB - Tu solicitud de registro de organización está en revisión"
        body = (
            f"Hola,\n\n"
            f"Hemos recibido la solicitud de registro para la organización '{org_name}'.\n"
            f"El equipo de EDULAB revisará los detalles enviados. Este proceso puede demorar hasta 24 horas.\n"
            f"Te notificaremos por este medio en cuanto tu organización sea aprobada.\n\n"
            f"Atentamente,\n"
            f"El equipo de EDULAB"
        )
        logger.info(f"📧 Mock Email Sent to {email}:")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Body Preview: {body[:250]}...")

    @staticmethod
    def send_organization_approved_email(email: str, org_name: str) -> None:
        """
        Sends an email indicating the organization has been approved.
        """
        subject = "EDULAB - ¡Tu organización ha sido aprobada!"
        body = (
            f"Hola,\n\n"
            f"Nos complace informarte que la organización '{org_name}' ha sido aprobada por el equipo de EDULAB.\n"
            f"Ya puedes iniciar sesión en la plataforma usando tu correo institucional y contraseña.\n"
            f"Podrás acceder a tu panel para crear convocatorias y ver candidatos.\n\n"
            f"Atentamente,\n"
            f"El equipo de EDULAB"
        )
        logger.info(f"📧 Mock Email Sent to {email}:")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Body Preview: {body[:250]}...")

    @staticmethod
    def send_organization_rejected_email(email: str, org_name: str) -> None:
        """
        Sends an email indicating the organization registration request has been rejected.
        """
        subject = "EDULAB - Estado de tu solicitud de registro de organización"
        body = (
            f"Hola,\n\n"
            f"Lamentamos informarte que la solicitud de registro para la organización '{org_name}' "
            f"no ha sido aprobada por el equipo de EDULAB en esta ocasión.\n"
            f"Si consideras que esto es un error o deseas postular nuevamente con datos de respaldo adicionales, "
            f"por favor ponte en contacto con soporte@edulab.com.\n\n"
            f"Atentamente,\n"
            f"El equipo de EDULAB"
        )
        logger.info(f"📧 Mock Email Sent to {email}:")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Body Preview: {body[:250]}...")

    @staticmethod
    def send_application_status_update_email(email: str, student_name: str, program_title: str, new_status: str) -> None:
        """
        Sends an email and triggers an internal notification indicating the student's application status has changed.
        """
        subject = f"EDULAB - Actualización en tu postulación a '{program_title}'"
        body = (
            f"Hola {student_name},\n\n"
            f"Te informamos que tu postulación al programa '{program_title}' ha cambiado de estado.\n"
            f"El nuevo estado de tu postulación es: {new_status}.\n"
            f"Por favor, inicia sesión en tu panel de control de EDULAB para revisar los detalles del proceso.\n\n"
            f"Atentamente,\n"
            f"El equipo de EDULAB"
        )
        logger.info(f"📧 Mock Email Sent to {email}:")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Body/Notification: {body[:250]}...")
        # Internal notification simulation
        logger.info(f"🔔 NOTIFICACIÓN INTERNA EDULAB (Usuario {student_name}): Tu postulación para '{program_title}' cambió a {new_status}.")

import logging
import json
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

firebase_app = None

def initialize_firebase() -> firebase_admin.App | None:
    global firebase_app
    if firebase_app is not None:
        return firebase_app

    # Try JSON credentials string first
    if settings.FIREBASE_CREDENTIALS_JSON:
        try:
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully via credentials JSON string.")
            return firebase_app
        except Exception as e:
            logger.error(f"Failed to initialize Firebase with JSON string: {e}")

    # Try credentials path second
    elif settings.FIREBASE_CREDENTIALS_PATH:
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK initialized successfully from path: {settings.FIREBASE_CREDENTIALS_PATH}")
            return firebase_app
        except Exception as e:
            logger.error(f"Failed to initialize Firebase with credentials file path: {e}")

    # Fallback / Dev mode
    if settings.MOCK_FIREBASE_AUTH:
        logger.warning(
            "⚠️ Firebase credentials not configured or bypassed. MOCK_FIREBASE_AUTH is True. "
            "Real Firebase Token verification will be bypassed or mocked."
        )
        return None
    else:
        raise RuntimeError(
            "Firebase credentials are required. "
            "Configure FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH, "
            "or set MOCK_FIREBASE_AUTH=True explicitly for mock offline dev testing."
        )

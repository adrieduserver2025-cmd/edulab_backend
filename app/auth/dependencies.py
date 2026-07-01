import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.users import service as user_service
from app.users.models import User
from app.users.schemas import UserCreate
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates the Firebase Bearer token in the request header.
    Syncs the user to the local database if they don't exist yet.
    """
    token = credentials.credentials

    # Development Mock Bypass - ONLY allowed if MOCK_FIREBASE_AUTH is explicitly True
    if settings.MOCK_FIREBASE_AUTH and (token.startswith("mock-") or not settings.FIREBASE_CREDENTIALS_PATH):
        role = "student"
        uid = token
        email = f"{token}@edulab.com"

        # If it's a real JWT token but we are running in mock dev mode, let's decode it
        # without verification to get the real uid and email (avoiding database length constraint error)
        if not token.startswith("mock-") and len(token.split('.')) == 3:
            import base64
            import json
            try:
                parts = token.split('.')
                payload_b64 = parts[1]
                payload_b64 += '=' * (4 - len(payload_b64) % 4)
                payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
                payload = json.loads(payload_json)
                decoded_uid = payload.get("user_id") or payload.get("sub")
                decoded_email = payload.get("email")
                if decoded_uid and decoded_email:
                    uid = decoded_uid
                    email = decoded_email
            except Exception as e:
                logger.error(f"Error decoding JWT token in mock bypass mode: {e}")

        if "admin" in token:
            role = "admin"
            uid = "mock-admin-uid"
            email = "admin@gmail.com"
        elif "aiesec" in token:
            role = "organization"
            uid = "mock-aiesec-uid"
            email = "aiesec@test.com"
        elif "reviewer" in token:
            role = "reviewer"
            uid = "mock-reviewer-uid"
            email = "reviewer@edulab.com"
        elif "organization_pending" in token:
            role = "organization_pending"
            email = "org_pending@edulab.com"
        elif "organization" in token:
            role = "organization"
            email = "org@edulab.com"

        logger.debug(f"🔑 MOCK_FIREBASE_AUTH: Mock authentication bypass. User: {email} ({role})")
        
        local_user = await user_service.get_user_by_firebase_uid(db, uid)
        if not local_user:
            local_user = await user_service.create_user(
                db, UserCreate(
                    firebase_uid=uid, 
                    email=email, 
                    full_name=f"Mock {role.capitalize()}", 
                    role=role
                )
            )

        if local_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )

        if local_user.role == "organization_pending":
            from app.organizations.models import Organization
            from sqlalchemy import select
            org_res = await db.execute(select(Organization).where(Organization.user_id == local_user.id))
            org = org_res.scalars().first()
            if org:
                if org.status == "PENDING":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tu organización aún está en revisión. Te notificaremos por correo cuando sea aprobada."
                    )
                elif org.status == "REJECTED":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tu solicitud de organización ha sido rechazada."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tu organización aún está en revisión. Te notificaremos por correo cuando sea aprobada."
                )

        return local_user

    try:
        # Verify Token via Firebase Admin SDK
        decoded_token = firebase_auth.verify_id_token(token)
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        full_name = decoded_token.get("name")
        photo_url = decoded_token.get("picture")

        if not firebase_uid or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase ID Token does not contain uid or email."
            )

        # Check local DB
        local_user = await user_service.get_user_by_firebase_uid(db, firebase_uid)
        if not local_user:
            # Sync user profile to PostgreSQL (Lazy Sync)
            role = decoded_token.get("role", "student")
            local_user = await user_service.create_user(
                db, UserCreate(
                    firebase_uid=firebase_uid,
                    email=email,
                    full_name=full_name,
                    photo_url=photo_url,
                    role=role
                )
            )

        if local_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )

        if local_user.role == "organization_pending":
            from app.organizations.models import Organization
            from sqlalchemy import select
            org_res = await db.execute(select(Organization).where(Organization.user_id == local_user.id))
            org = org_res.scalars().first()
            if org:
                if org.status == "PENDING":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tu organización aún está en revisión. Te notificaremos por correo cuando sea aprobada."
                    )
                elif org.status == "REJECTED":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tu solicitud de organización ha sido rechazada."
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tu organización aún está en revisión. Te notificaremos por correo cuando sea aprobada."
                )

        return local_user

    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate Firebase ID Token: {str(e)}"
        )

def check_role(allowed_roles: list[str]):
    """
    Dependency factory to enforce role-based access control.
    """
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource."
            )
        return current_user
    return dependency

# Touch for uvicorn reload

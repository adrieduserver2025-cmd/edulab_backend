from fastapi import APIRouter
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.students.router import router as student_profile_router
from app.programs.router import router as programs_router, admin_programs_router
from app.opportunities.router import router as opportunities_router
from app.applications.router import router as applications_router
from app.documents.router import router as documents_router
from app.organizations.router import router as organizations_router, admin_router as admin_organizations_router

router = APIRouter()

# Register sub-routers
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(student_profile_router)
router.include_router(programs_router)
router.include_router(admin_programs_router)
router.include_router(opportunities_router)
router.include_router(applications_router)
router.include_router(documents_router)
router.include_router(organizations_router)
router.include_router(admin_organizations_router)

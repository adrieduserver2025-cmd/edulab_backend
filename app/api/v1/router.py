from fastapi import APIRouter
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.students.router import router as student_profile_router
# from app.programs.router import router as programs_router

router = APIRouter()

# Register sub-routers
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(student_profile_router)
# router.include_router(programs_router)
# Additional modules (documents, applications) can be included here in subsequent sprints

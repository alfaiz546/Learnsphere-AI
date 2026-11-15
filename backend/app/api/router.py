from fastapi import APIRouter
from app.api.endpoints import auth, student, subjects, lessons, assessments, ai, progress, gamification, admin, simulator

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(student.router)
api_router.include_router(subjects.router)
api_router.include_router(lessons.router)
api_router.include_router(assessments.router)
api_router.include_router(ai.router)
api_router.include_router(progress.router)
api_router.include_router(gamification.router)
api_router.include_router(admin.router)
api_router.include_router(simulator.router)

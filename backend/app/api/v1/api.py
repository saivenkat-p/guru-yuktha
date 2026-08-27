from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, dashboard, students, activities, attendance, materials, evidence, reports, rooms, public_resources
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(public_resources.router, prefix="/resources", tags=["resources"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

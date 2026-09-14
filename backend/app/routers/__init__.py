"""HTTP routers for /api/v1."""

from fastapi import APIRouter

from app.routers import auth, commitments, families, history, points

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(families.router, tags=["families"])
api_router.include_router(commitments.router, tags=["commitments"])
api_router.include_router(points.router, tags=["points"])
api_router.include_router(history.router, tags=["history"])

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.v1.api import api_router
from app.seed.seed_demo_data import seed_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Production CORS Configuration: allow configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    # Check if empty, run seed automatically
    db = SessionLocal()
    try:
        from app.models.models import Student
        count = db.query(Student).count()
        if count == 0:
            print("Auto-seeding empty Guru Yuktha database...")
            seed_db()
    except Exception as e:
        print(f"Startup DB check error: {e}")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "title": "Guru Yuktha API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "tagline": "Navigate. Monitor. Support."
    }

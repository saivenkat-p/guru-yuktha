import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import text
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

def run_production_safe_migrations():
    """Additive, idempotent database migration for PostgreSQL and SQLite."""
    try:
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            dialect = engine.dialect.name
            if dialect == "postgresql":
                # Activities
                conn.execute(text("ALTER TABLE activities ADD COLUMN IF NOT EXISTS teacher_id INTEGER REFERENCES teachers(id);"))
                conn.execute(text("ALTER TABLE activities ADD COLUMN IF NOT EXISTS room_id INTEGER REFERENCES rooms(id);"))
                conn.execute(text("ALTER TABLE activities ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER REFERENCES users(id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_activities_teacher_id ON activities(teacher_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_activities_room_id ON activities(room_id);"))
                conn.execute(text("ALTER TABLE activities ALTER COLUMN student_id DROP NOT NULL;"))

                # Users
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS guru_id VARCHAR(50);"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100);"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS skills TEXT;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guru_eligible BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_guru_id ON users(guru_id);"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users(username);"))

                # Rooms
                conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id);"))
                conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS access_type VARCHAR(50) DEFAULT 'PUBLIC_FREE';"))
                conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS price FLOAT DEFAULT 0.0;"))
                conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'INR';"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rooms_owner_id ON rooms(owner_id);"))

                # Room Memberships
                conn.execute(text("ALTER TABLE room_memberships ADD COLUMN IF NOT EXISTS access_source VARCHAR(50) DEFAULT 'FREE_JOIN';"))

                # Resources
                conn.execute(text("ALTER TABLE resources ADD COLUMN IF NOT EXISTS is_preview_allowed BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("ALTER TABLE resources ADD COLUMN IF NOT EXISTS external_url VARCHAR(1000);"))

                conn.commit()
            elif dialect == "sqlite":
                columns_to_add = [
                    ("activities", "teacher_id", "INTEGER"),
                    ("activities", "room_id", "INTEGER"),
                    ("activities", "created_by_user_id", "INTEGER"),
                    ("users", "guru_id", "VARCHAR(50)"),
                    ("users", "username", "VARCHAR(100)"),
                    ("users", "bio", "TEXT"),
                    ("users", "skills", "TEXT"),
                    ("users", "is_guru_eligible", "BOOLEAN DEFAULT 0"),
                    ("rooms", "owner_id", "INTEGER"),
                    ("rooms", "access_type", "VARCHAR(50) DEFAULT 'PUBLIC_FREE'"),
                    ("rooms", "price", "FLOAT DEFAULT 0.0"),
                    ("rooms", "currency", "VARCHAR(10) DEFAULT 'INR'"),
                    ("room_memberships", "access_source", "VARCHAR(50) DEFAULT 'FREE_JOIN'"),
                    ("resources", "is_preview_allowed", "BOOLEAN DEFAULT 0"),
                    ("resources", "external_url", "VARCHAR(1000)"),
                ]
                for table, col, col_type in columns_to_add:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                        conn.commit()
                    except Exception:
                        pass

        # Backfill existing data with Python models
        from app.models.models import User, Room, Teacher
        from app.core.identity import generate_guru_id, generate_username
        
        db = SessionLocal()
        try:
            users = db.query(User).all()
            for u in users:
                changed = False
                if not u.guru_id:
                    u.guru_id = generate_guru_id(u.full_name, u.id, db)
                    changed = True
                if not u.username:
                    u.username = generate_username(u.full_name, u.email, u.id, db)
                    changed = True
                # Migrate any legacy role classification:
                if u.role in ("LEARNER", "STUDENT"):
                    u.role = "MEMBER"
                    changed = True
                if changed:
                    db.commit()

            rooms = db.query(Room).all()
            for r in rooms:
                changed = False
                if not r.owner_id and r.teacher_id:
                    teacher = db.query(Teacher).filter(Teacher.id == r.teacher_id).first()
                    if teacher:
                        r.owner_id = teacher.user_id
                        changed = True
                if not r.access_type:
                    r.access_type = "PUBLIC_FREE" if r.visibility == "PUBLIC" else "PRIVATE_FREE"
                    changed = True
                if changed:
                    db.commit()
        except Exception as e:
            print(f"Data backfill note: {e}")
        finally:
            db.close()

    except Exception as e:
        print(f"Migration note: {e}")

@app.on_event("startup")
def startup_event():
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    run_production_safe_migrations()
    
    # Check if empty and SEED_DEMO_DATA is explicitly enabled
    if settings.SEED_DEMO_DATA:
        db = SessionLocal()
        try:
            from app.models.models import Student
            count = db.query(Student).count()
            if count == 0:
                print("SEED_DEMO_DATA=true: Auto-seeding initial demo data for Guru Yuktha...")
                seed_db(drop_first=False)
        except Exception as e:
            print(f"Startup DB seed check error: {e}")
        finally:
            db.close()
    else:
        print("SEED_DEMO_DATA is disabled (production mode). Database tables initialized without mock data.")

@app.get("/")
def root():
    return {
        "title": "Guru Yuktha API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "tagline": "Navigate. Monitor. Support."
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

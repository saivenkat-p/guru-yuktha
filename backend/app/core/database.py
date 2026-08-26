from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# For SQLite, set connect_args check_same_thread=False; for PostgreSQL use pool_pre_ping=True
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine_kwargs = {"connect_args": {"check_same_thread": False}} if is_sqlite else {"pool_pre_ping": True}

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

# Cấu hình engine kết nối SQLite (check_same_thread=False cho FastAPI đa luồng)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency cung cấp session kết nối database cho mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

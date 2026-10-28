import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Locally: the SQLite file is saved in the project folder (permanent).
# On Vercel: the project folder is read-only, so only /tmp can be written to.
# Data in /tmp is TEMPORARY and is lost when the server restarts.
if os.environ.get("VERCEL"):
    DATABASE_URL = "sqlite:////tmp/attendance.db"
else:
    DATABASE_URL = "sqlite:///./attendance.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

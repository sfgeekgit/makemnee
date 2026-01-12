"""
Database connection and session management for MakeMNEE Bounty Board API.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - defaults to SQLite in current directory
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./bountyboard.db"
)

# Create SQLAlchemy engine
# check_same_thread=False is needed for SQLite to work with FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

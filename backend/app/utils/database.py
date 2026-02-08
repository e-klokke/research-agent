"""Database utilities for PostgreSQL"""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, Column, String, Text, Float, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()


class ResearchRecord(Base):
    """Database model for research history"""
    __tablename__ = "research_history"

    research_id = Column(String, primary_key=True)
    query = Column(Text, nullable=False)
    domain = Column(String, nullable=False)
    depth = Column(String, nullable=False)
    status = Column(String, nullable=False)
    final_report = Column(Text, nullable=True)
    sources_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.0)
    iteration_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Database:
    """Database connection manager"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/research_agent"
        )
        self.engine = None
        self.SessionLocal = None

    def init_db(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)

            # Create tables
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.warning(f"Could not initialize database: {e}")
            logger.warning("Falling back to in-memory storage")

    def get_session(self):
        """Get database session"""
        if self.SessionLocal:
            return self.SessionLocal()
        return None

    def save_research(self, research_id: str, state: dict):
        """Save research to database"""
        session = self.get_session()
        if not session:
            return

        try:
            record = session.query(ResearchRecord).filter_by(
                research_id=research_id
            ).first()

            if record:
                # Update existing
                record.status = state.get("current_stage", "unknown")
                record.final_report = state.get("final_report")
                record.confidence_score = state.get("confidence_score", 0.0)
                record.iteration_count = state.get("iteration_count", 0)
                if state.get("current_stage") == "completed":
                    record.completed_at = datetime.utcnow()
            else:
                # Create new
                record = ResearchRecord(
                    research_id=research_id,
                    query=state.get("query", ""),
                    domain=state.get("domain", "tech"),
                    depth=state.get("depth", "standard"),
                    status=state.get("current_stage", "planning"),
                    final_report=state.get("final_report"),
                    confidence_score=state.get("confidence_score", 0.0),
                    iteration_count=state.get("iteration_count", 0)
                )
                session.add(record)

            session.commit()
            logger.debug(f"Saved research {research_id} to database")

        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            session.rollback()
        finally:
            session.close()

    def get_research_history(self, limit: int = 10):
        """Get research history from database"""
        session = self.get_session()
        if not session:
            return []

        try:
            records = session.query(ResearchRecord).order_by(
                ResearchRecord.created_at.desc()
            ).limit(limit).all()

            return [
                {
                    "research_id": r.research_id,
                    "query": r.query,
                    "domain": r.domain,
                    "depth": r.depth,
                    "completed": r.status == "completed",
                    "confidence_score": r.confidence_score,
                    "created_at": r.created_at.isoformat()
                }
                for r in records
            ]

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []
        finally:
            session.close()


# Global instance
_database: Optional[Database] = None


def get_database() -> Database:
    """Get or create database instance"""
    global _database
    if _database is None:
        _database = Database()
        try:
            _database.init_db()
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
    return _database

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./strategic_engine.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Document(Base):
    """Document model for storing uploaded documents"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(String(50), nullable=False)  # financial, market_research, internal, general
    upload_date = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(JSON, nullable=True)  # Additional metadata as JSON
    embedding_status = Column(String(20), default="pending")  # pending, completed, failed
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"


class QueryHistory(Base):
    """Query history model for storing user queries and responses"""
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Source documents as JSON
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(String(10), nullable=True)  # Average similarity score
    
    def __repr__(self):
        return f"<QueryHistory(id={self.id}, timestamp='{self.timestamp}')>"


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()
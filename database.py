from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite URL format
DATABASE_URL = "sqlite:///./research_history.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

# History table


class User(Base):
    __tablename__ = "user_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(80), nullable=False)


class ResearchHistory(Base):
    __tablename__ = "research_history"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    summary = Column(Text)
    sources = Column(Text)  # store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


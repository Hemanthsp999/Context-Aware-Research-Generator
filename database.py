from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# database connection URL (SQLite here for example)
DATABASE_URL = "sqlite:///./test.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class User(Base):
    __tablename__ = "user_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(80), nullable=False)

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), index=True)  # maps to your old file-based ID
    user_id = Column(Integer, ForeignKey("user_table.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    history = relationship("ResearchHistory", back_populates="conversation", cascade="all, delete")


class ResearchHistory(Base):
    __tablename__ = "research_history"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    summary = Column(Text)
    sources = Column(Text)  # store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="history")


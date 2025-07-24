"""
Database models for Gergy MCP shared infrastructure.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, Float, Boolean, Text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

Base = declarative_base()

class KnowledgeItem(Base):
    """Stores knowledge across all MCP domains with JSONB for flexible schema."""
    __tablename__ = 'knowledge_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(50), nullable=False, index=True)  # financial, family, lifestyle, etc.
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=False, default=dict)  # flexible schema
    keywords = Column(JSONB, nullable=False, default=list)  # relevance keywords
    usage_frequency = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(Base):
    """Tracks user conversations and context accumulation."""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime)
    context_data = Column(JSONB, nullable=False, default=dict)
    conversation_history = Column(JSONB, nullable=False, default=list)
    active_domains = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, default=True)

class TemporalCache(Base):
    """Manages temporal caching with expiration and cross-module relevance."""
    __tablename__ = 'temporal_cache'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    cache_value = Column(JSONB, nullable=False)
    domain = Column(String(50), nullable=False, index=True)
    cross_domain_relevance = Column(JSONB, nullable=False, default=list)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)

class CrossDomainPattern(Base):
    """Stores patterns that span multiple domains for intelligent suggestions."""
    __tablename__ = 'cross_domain_patterns'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_name = Column(String(200), nullable=False)
    pattern_data = Column(JSONB, nullable=False)
    involved_domains = Column(JSONB, nullable=False, default=list)
    confidence_score = Column(Float, nullable=False, default=0.0)
    usage_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class APIUsageAnalytics(Base):
    """Tracks API usage and costs across all MCP servers."""
    __tablename__ = 'api_usage_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_name = Column(String(100), nullable=False, index=True)
    api_provider = Column(String(100), nullable=False)
    endpoint = Column(String(200), nullable=False)
    request_count = Column(Integer, default=0)
    token_usage = Column(JSONB, nullable=False, default=dict)  # {input: 0, output: 0}
    estimated_cost = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSONB, nullable=False, default=dict)

class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
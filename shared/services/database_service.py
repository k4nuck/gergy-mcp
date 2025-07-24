"""
DatabaseService for unified knowledge access across all MCP servers.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from contextlib import contextmanager
import logging

from ..models.database import (
    DatabaseConfig, KnowledgeItem, UserSession, TemporalCache, 
    CrossDomainPattern, APIUsageAnalytics
)

logger = logging.getLogger(__name__)

class DatabaseService:
    """Unified database service for all MCP servers."""
    
    def __init__(self, database_url: str):
        self.config = DatabaseConfig(database_url)
        self.config.create_tables()
        
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.config.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    async def store_knowledge(
        self, 
        domain: str, 
        title: str, 
        content: str, 
        metadata: Dict[str, Any], 
        keywords: List[str]
    ) -> str:
        """Store knowledge item with domain tagging."""
        with self.get_session() as session:
            knowledge_item = KnowledgeItem(
                domain=domain,
                title=title,
                content=content,
                metadata=metadata,
                keywords=keywords
            )
            session.add(knowledge_item)
            session.flush()
            return str(knowledge_item.id)
    
    async def search_knowledge(
        self, 
        domains: List[str] = None, 
        keywords: List[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search knowledge across domains with keyword matching."""
        with self.get_session() as session:
            query = session.query(KnowledgeItem)
            
            if domains:
                query = query.filter(KnowledgeItem.domain.in_(domains))
            
            if keywords:
                keyword_filters = []
                for keyword in keywords:
                    keyword_filters.append(
                        KnowledgeItem.keywords.op('?')(keyword)
                    )
                query = query.filter(or_(*keyword_filters))
            
            results = query.order_by(desc(KnowledgeItem.usage_frequency)).limit(limit).all()
            
            return [
                {
                    'id': str(item.id),
                    'domain': item.domain,
                    'title': item.title,
                    'content': item.content,
                    'metadata': item.metadata,
                    'keywords': item.keywords,
                    'usage_frequency': item.usage_frequency,
                    'last_accessed': item.last_accessed
                }
                for item in results
            ]
    
    async def update_usage_frequency(self, knowledge_id: str):
        """Increment usage frequency and update last accessed time."""
        with self.get_session() as session:
            item = session.query(KnowledgeItem).filter(
                KnowledgeItem.id == knowledge_id
            ).first()
            if item:
                item.usage_frequency += 1
                item.last_accessed = datetime.utcnow()
    
    async def start_user_session(self, user_id: str, initial_context: Dict[str, Any]) -> str:
        """Start a new user session."""
        with self.get_session() as session:
            user_session = UserSession(
                user_id=user_id,
                context_data=initial_context,
                conversation_history=[],
                active_domains=[]
            )
            session.add(user_session)
            session.flush()
            return str(user_session.id)
    
    async def update_session_context(
        self, 
        session_id: str, 
        context_update: Dict[str, Any],
        conversation_entry: Dict[str, Any] = None
    ):
        """Update session context and add conversation entry."""
        with self.get_session() as session:
            user_session = session.query(UserSession).filter(
                UserSession.id == session_id
            ).first()
            
            if user_session:
                user_session.context_data.update(context_update)
                
                if conversation_entry:
                    user_session.conversation_history.append({
                        **conversation_entry,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                session.add(user_session)
    
    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session context."""
        with self.get_session() as session:
            user_session = session.query(UserSession).filter(
                UserSession.id == session_id
            ).first()
            
            if user_session:
                return {
                    'context_data': user_session.context_data,
                    'conversation_history': user_session.conversation_history,
                    'active_domains': user_session.active_domains,
                    'session_start': user_session.session_start
                }
            return None
    
    async def end_user_session(self, session_id: str):
        """End a user session."""
        with self.get_session() as session:
            user_session = session.query(UserSession).filter(
                UserSession.id == session_id
            ).first()
            
            if user_session:
                user_session.is_active = False
                user_session.session_end = datetime.utcnow()
    
    async def store_cross_domain_pattern(
        self, 
        pattern_name: str, 
        pattern_data: Dict[str, Any],
        involved_domains: List[str],
        confidence_score: float
    ) -> str:
        """Store a cross-domain pattern for intelligent suggestions."""
        with self.get_session() as session:
            pattern = CrossDomainPattern(
                pattern_name=pattern_name,
                pattern_data=pattern_data,
                involved_domains=involved_domains,
                confidence_score=confidence_score
            )
            session.add(pattern)
            session.flush()
            return str(pattern.id)
    
    async def get_relevant_patterns(
        self, 
        domains: List[str], 
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get patterns relevant to specified domains."""
        with self.get_session() as session:
            patterns = session.query(CrossDomainPattern).filter(
                and_(
                    CrossDomainPattern.confidence_score >= min_confidence,
                    CrossDomainPattern.involved_domains.op('&&')(domains)
                )
            ).order_by(desc(CrossDomainPattern.confidence_score)).all()
            
            return [
                {
                    'id': str(pattern.id),
                    'pattern_name': pattern.pattern_name,
                    'pattern_data': pattern.pattern_data,
                    'involved_domains': pattern.involved_domains,
                    'confidence_score': pattern.confidence_score,
                    'usage_count': pattern.usage_count
                }
                for pattern in patterns
            ]
    
    async def cleanup_expired_cache(self):
        """Remove expired cache entries."""
        with self.get_session() as session:
            expired_count = session.query(TemporalCache).filter(
                TemporalCache.expires_at < datetime.utcnow()
            ).delete()
            logger.info(f"Cleaned up {expired_count} expired cache entries")
    
    async def get_api_usage_summary(
        self, 
        server_name: str = None, 
        days: int = 7
    ) -> Dict[str, Any]:
        """Get API usage summary for cost tracking."""
        with self.get_session() as session:
            query = session.query(APIUsageAnalytics).filter(
                APIUsageAnalytics.date >= datetime.utcnow() - timedelta(days=days)
            )
            
            if server_name:
                query = query.filter(APIUsageAnalytics.server_name == server_name)
            
            usage_data = query.all()
            
            total_cost = sum(item.estimated_cost for item in usage_data)
            total_requests = sum(item.request_count for item in usage_data)
            
            return {
                'total_cost': total_cost,
                'total_requests': total_requests,
                'daily_breakdown': self._group_usage_by_day(usage_data),
                'server_breakdown': self._group_usage_by_server(usage_data)
            }
    
    def _group_usage_by_day(self, usage_data: List[APIUsageAnalytics]) -> Dict[str, Dict[str, float]]:
        """Group usage data by day."""
        daily_data = {}
        for item in usage_data:
            date_key = item.date.strftime('%Y-%m-%d')
            if date_key not in daily_data:
                daily_data[date_key] = {'cost': 0.0, 'requests': 0}
            daily_data[date_key]['cost'] += item.estimated_cost
            daily_data[date_key]['requests'] += item.request_count
        return daily_data
    
    def _group_usage_by_server(self, usage_data: List[APIUsageAnalytics]) -> Dict[str, Dict[str, float]]:
        """Group usage data by server."""
        server_data = {}
        for item in usage_data:
            if item.server_name not in server_data:
                server_data[item.server_name] = {'cost': 0.0, 'requests': 0}
            server_data[item.server_name]['cost'] += item.estimated_cost
            server_data[item.server_name]['requests'] += item.request_count
        return server_data
"""
CacheService with Redis integration for performance optimization across MCP servers.
"""
import asyncio
import logging
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass
import hashlib
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    value: Any
    expires_at: datetime
    domain: str
    access_count: int
    created_at: datetime
    last_accessed: datetime

class CacheService:
    """High-performance caching service with Redis backend."""
    
    def __init__(
        self, 
        database_service,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600  # 1 hour default
    ):
        self.db = database_service
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self.local_cache = {}  # Fallback for when Redis is unavailable
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using local cache fallback.")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_cache_key(self, domain: str, key: str) -> str:
        """Generate a namespaced cache key."""
        return f"gergy:{domain}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """Generate hash for complex data structures."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def get(
        self, 
        key: str, 
        domain: str = "default"
    ) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._generate_cache_key(domain, key)
        
        try:
            if self.redis_client:
                # Try Redis first
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    # Update access count in temporal cache
                    await self._update_access_count(cache_key)
                    return pickle.loads(cached_data)
            else:
                # Fallback to local cache
                if cache_key in self.local_cache:
                    entry = self.local_cache[cache_key]
                    if entry.expires_at > datetime.utcnow():
                        self.cache_stats['hits'] += 1
                        entry.access_count += 1
                        entry.last_accessed = datetime.utcnow()
                        return entry.value
                    else:
                        # Expired entry
                        del self.local_cache[cache_key]
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        domain: str = "default",
        ttl: Optional[int] = None,
        cross_domain_relevance: List[str] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        cache_key = self._generate_cache_key(domain, key)
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        try:
            if self.redis_client:
                # Store in Redis
                serialized_value = pickle.dumps(value)
                await self.redis_client.setex(cache_key, ttl, serialized_value)
            else:
                # Store in local cache
                self.local_cache[cache_key] = CacheEntry(
                    key=cache_key,
                    value=value,
                    expires_at=expires_at,
                    domain=domain,
                    access_count=0,
                    created_at=datetime.utcnow(),
                    last_accessed=datetime.utcnow()
                )
            
            # Store metadata in database for cross-domain relevance
            await self._store_cache_metadata(
                cache_key, domain, expires_at, cross_domain_relevance or []
            )
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {cache_key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    async def delete(self, key: str, domain: str = "default") -> bool:
        """Delete value from cache."""
        cache_key = self._generate_cache_key(domain, key)
        
        try:
            if self.redis_client:
                await self.redis_client.delete(cache_key)
            else:
                if cache_key in self.local_cache:
                    del self.local_cache[cache_key]
            
            self.cache_stats['deletes'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for {cache_key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    async def invalidate_domain(self, domain: str) -> int:
        """Invalidate all cache entries for a domain."""
        pattern = self._generate_cache_key(domain, "*")
        deleted_count = 0
        
        try:
            if self.redis_client:
                # Get all keys matching pattern
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
            else:
                # Local cache cleanup
                keys_to_delete = [
                    key for key in self.local_cache.keys() 
                    if key.startswith(f"gergy:{domain}:")
                ]
                for key in keys_to_delete:
                    del self.local_cache[key]
                deleted_count = len(keys_to_delete)
            
            logger.info(f"Invalidated {deleted_count} cache entries for domain {domain}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache invalidation error for domain {domain}: {e}")
            return 0
    
    async def get_or_set(
        self,
        key: str,
        value_func,
        domain: str = "default",
        ttl: Optional[int] = None,
        cross_domain_relevance: List[str] = None
    ) -> Any:
        """Get value from cache or set it using provided function."""
        cached_value = await self.get(key, domain)
        
        if cached_value is not None:
            return cached_value
        
        # Generate value and cache it
        try:
            if asyncio.iscoroutinefunction(value_func):
                new_value = await value_func()
            else:
                new_value = value_func()
            
            await self.set(key, new_value, domain, ttl, cross_domain_relevance)
            return new_value
            
        except Exception as e:
            logger.error(f"Error generating value for cache key {key}: {e}")
            raise
    
    async def get_cross_domain_suggestions(self, current_domain: str) -> List[Dict[str, Any]]:
        """Get cached data relevant to current domain from other domains."""
        suggestions = []
        
        try:
            with self.db.get_session() as session:
                from ..models.database import TemporalCache
                
                # Query cache entries with cross-domain relevance
                relevant_cache = session.query(TemporalCache).filter(
                    TemporalCache.cross_domain_relevance.op('?')(current_domain)
                ).filter(
                    TemporalCache.expires_at > datetime.utcnow()
                ).order_by(TemporalCache.access_count.desc()).limit(10).all()
                
                for cache_entry in relevant_cache:
                    # Get the actual cached value
                    cached_value = await self.get(
                        cache_entry.cache_key.split(':')[-1], 
                        cache_entry.domain
                    )
                    
                    if cached_value:
                        suggestions.append({
                            'domain': cache_entry.domain,
                            'key': cache_entry.cache_key,
                            'value': cached_value,
                            'access_count': cache_entry.access_count,
                            'relevance_score': self._calculate_relevance_score(
                                cache_entry, current_domain
                            )
                        })
            
            # Sort by relevance score
            suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting cross-domain suggestions: {e}")
            return []
    
    def _calculate_relevance_score(self, cache_entry, current_domain: str) -> float:
        """Calculate relevance score for cross-domain suggestion."""
        base_score = 0.5
        
        # Higher score for more frequently accessed items
        access_score = min(cache_entry.access_count / 10.0, 0.3)
        
        # Higher score for more recent items
        age_hours = (datetime.utcnow() - cache_entry.created_at).total_seconds() / 3600
        recency_score = max(0, 0.2 - (age_hours / 24.0) * 0.2)
        
        return base_score + access_score + recency_score
    
    async def _store_cache_metadata(
        self, 
        cache_key: str, 
        domain: str, 
        expires_at: datetime,
        cross_domain_relevance: List[str]
    ):
        """Store cache metadata in database for cross-domain queries."""
        try:
            with self.db.get_session() as session:
                from ..models.database import TemporalCache
                
                # Check if entry already exists
                existing = session.query(TemporalCache).filter(
                    TemporalCache.cache_key == cache_key
                ).first()
                
                if existing:
                    existing.expires_at = expires_at
                    existing.cross_domain_relevance = cross_domain_relevance
                else:
                    cache_metadata = TemporalCache(
                        cache_key=cache_key,
                        cache_value={},  # We don't store the actual value here
                        domain=domain,
                        cross_domain_relevance=cross_domain_relevance,
                        expires_at=expires_at
                    )
                    session.add(cache_metadata)
                    
        except Exception as e:
            logger.error(f"Error storing cache metadata: {e}")
    
    async def _update_access_count(self, cache_key: str):
        """Update access count for cache entry."""
        try:
            with self.db.get_session() as session:
                from ..models.database import TemporalCache
                
                cache_entry = session.query(TemporalCache).filter(
                    TemporalCache.cache_key == cache_key
                ).first()
                
                if cache_entry:
                    cache_entry.access_count += 1
                    
        except Exception as e:
            logger.error(f"Error updating access count: {e}")
    
    async def cleanup_expired_entries(self):
        """Clean up expired cache entries."""
        try:
            # Clean up database metadata
            await self.db.cleanup_expired_cache()
            
            # Clean up local cache
            if not self.redis_client:
                expired_keys = [
                    key for key, entry in self.local_cache.items()
                    if entry.expires_at <= datetime.utcnow()
                ]
                for key in expired_keys:
                    del self.local_cache[key]
                
                logger.info(f"Cleaned up {len(expired_keys)} expired local cache entries")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_operations = sum(self.cache_stats.values())
        hit_rate = self.cache_stats['hits'] / max(
            self.cache_stats['hits'] + self.cache_stats['misses'], 1
        )
        
        stats = {
            **self.cache_stats,
            'total_operations': total_operations,
            'hit_rate': round(hit_rate * 100, 2),
            'redis_connected': self.redis_client is not None,
            'local_cache_size': len(self.local_cache) if not self.redis_client else 0
        }
        
        # Get Redis info if available
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info('memory')
                stats['redis_memory_usage'] = redis_info.get('used_memory_human', 'Unknown')
                stats['redis_memory_peak'] = redis_info.get('used_memory_peak_human', 'Unknown')
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
        
        return stats
    
    async def warm_cache_for_domain(self, domain: str, data_generator):
        """Pre-populate cache for a domain using a data generator."""
        try:
            logger.info(f"Warming cache for domain: {domain}")
            
            if asyncio.iscoroutinefunction(data_generator):
                cache_data = await data_generator()
            else:
                cache_data = data_generator()
            
            warmed_count = 0
            for key, value in cache_data.items():
                success = await self.set(
                    key, value, domain, 
                    ttl=self.default_ttl * 2  # Longer TTL for pre-warmed data
                )
                if success:
                    warmed_count += 1
            
            logger.info(f"Warmed {warmed_count} cache entries for domain {domain}")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Error warming cache for domain {domain}: {e}")
            return 0
"""
Cache Manager for Mental Health Chatbot
Implements in-memory caching with TTL for LLM responses and database queries
"""

import time
import hashlib
from typing import Any, Optional, Dict
from functools import wraps
import json


class CacheManager:
    """Simple in-memory cache with time-to-live (TTL)"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires_at']:
                self.hits += 1
                return entry['value']
            else:
                # Expired, remove it
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries, return count of removed items"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time >= entry['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'total_requests': total_requests
        }


# Global cache instance
cache = CacheManager(default_ttl=1800)  # 30 minutes default


def cached_response(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function responses
    
    Usage:
        @cached_response('llm', ttl=3600)
        def get_llm_response(query):
            # expensive operation
            return response
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key_data = {'args': args, 'kwargs': kwargs}
            cache_key = cache._generate_key(prefix, cache_key_data)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Not in cache, call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_llm_response(query: str, response: str, ttl: int = 1800) -> None:
    """Cache LLM response for a query"""
    key = cache._generate_key('llm', query)
    cache.set(key, response, ttl)


def get_cached_llm_response(query: str) -> Optional[str]:
    """Get cached LLM response for a query"""
    key = cache._generate_key('llm', query)
    return cache.get(key)


def cache_assessment_result(user_id: int, assessment_type: str, result: Dict, ttl: int = 3600) -> None:
    """Cache assessment result"""
    key = cache._generate_key('assessment', {'user_id': user_id, 'type': assessment_type})
    cache.set(key, result, ttl)


def get_cached_assessment(user_id: int, assessment_type: str) -> Optional[Dict]:
    """Get cached assessment result"""
    key = cache._generate_key('assessment', {'user_id': user_id, 'type': assessment_type})
    return cache.get(key)


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cache entries for a user"""
    # This is a simple implementation - in production, use key prefixes
    keys_to_delete = [
        key for key in cache.cache.keys()
        if f"user_id': {user_id}" in str(cache.cache[key])
    ]
    for key in keys_to_delete:
        cache.delete(key)

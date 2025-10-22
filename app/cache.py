import redis.asyncio as redis
import json
import hashlib
from typing import Optional
import os

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION", 600))  # 10 minutes default

# Initialize Redis client
redis_client = None


async def get_redis_client():
    """Get or create Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
    return redis_client


def generate_cache_key(query: str) -> str:
    """Generate a unique cache key from the query using hash"""
    # Normalize the query (lowercase, strip whitespace)
    normalized_query = query.lower().strip()
    # Create hash for consistent key generation
    query_hash = hashlib.md5(normalized_query.encode()).hexdigest()
    return f"chatbot:query:{query_hash}"


async def get_cached_response(query: str) -> Optional[str]:
    """
    Retrieve cached response from Redis
    Returns None if not found
    """
    try:
        client = await get_redis_client()
        cache_key = generate_cache_key(query)
        cached_data = await client.get(cache_key)
        
        if cached_data:
            # Parse JSON data
            data = json.loads(cached_data)
            return data.get("response")
        
        return None
    except Exception as e:
        print(f"Error retrieving from cache: {e}")
        return None


async def set_cached_response(query: str, response: str) -> bool:
    """
    Store response in Redis cache with expiration
    Returns True if successful
    """
    try:
        client = await get_redis_client()
        cache_key = generate_cache_key(query)
        
        # Store as JSON
        cache_data = json.dumps({
            "query": query,
            "response": response
        })
        
        # Set with expiration
        await client.setex(cache_key, CACHE_EXPIRATION, cache_data)
        return True
    except Exception as e:
        print(f"Error setting cache: {e}")
        return False


async def clear_cache():
    """Clear all chatbot cache entries"""
    try:
        client = await get_redis_client()
        keys = await client.keys("chatbot:query:*")
        if keys:
            await client.delete(*keys)
        return len(keys)
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return 0


async def close_redis_connection():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
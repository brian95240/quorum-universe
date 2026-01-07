#!/usr/bin/env python3
"""
Redis State Manager - Production Implementation
Persistent state management for ambient intelligence system

Key Features:
- Session persistence (conversation history, context)
- Embedding cache (10x speedup on repeated queries)
- Warm circuit predictions (model co-activation patterns)
- Archetype performance tracking
- Query result caching (instant repeat responses)
- Graph traversal cache (semantic relationships)
- Rate limiting state (per-user quotas)

Cache Strategy:
1. Embeddings: TTL 7 days (rarely change)
2. Warm predictions: TTL 1 day (update nightly)
3. Query results: TTL 1 hour (fresh but cached)
4. Session data: TTL 24 hours (active conversations)
5. Graph cache: TTL 2 days (semantic stability)

Performance Target:
- Cache hit rate: >75%
- Latency reduction: 5-10x on cached paths
- Memory efficiency: <2GB Redis RAM
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio

# Redis
try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    print("WARNING: redis not available. Install: pip install redis")
    REDIS_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class CacheType(Enum):
    """Types of cached data"""
    EMBEDDING = "emb"          # Vector embeddings
    QUERY_RESULT = "qry"       # Full query responses
    WARM_PREDICTION = "wrm"    # Warm circuit predictions
    SESSION = "ses"            # User sessions
    GRAPH = "grp"              # Graph traversal results
    ARCHETYPE_STATE = "arc"    # Archetype load states
    QUALITY_SCORE = "qal"      # Quality assessment cache
    RATE_LIMIT = "rlt"         # Rate limiting counters


@dataclass
class CacheEntry:
    """Generic cache entry"""
    key: str
    value: Any
    cache_type: CacheType
    created_at: float
    ttl_seconds: int
    hits: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'value': self.value,
            'cache_type': self.cache_type.value,
            'created_at': self.created_at,
            'ttl_seconds': self.ttl_seconds,
            'hits': self.hits
        }


@dataclass
class SessionState:
    """User conversation session"""
    session_id: str
    user_id: str
    conversation_history: List[Dict]  # [{role, content, timestamp}]
    context: Dict                      # Persistent context
    active_archetypes: List[str]       # Currently loaded
    query_count: int = 0
    created_at: float = 0.0
    last_active: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    
    # By cache type
    hits_by_type: Dict[str, int] = None
    misses_by_type: Dict[str, int] = None
    
    # Performance
    avg_get_latency_ms: float = 0.0
    avg_set_latency_ms: float = 0.0
    
    # Memory
    memory_usage_mb: float = 0.0
    total_keys: int = 0
    
    def __post_init__(self):
        if self.hits_by_type is None:
            self.hits_by_type = {}
        if self.misses_by_type is None:
            self.misses_by_type = {}


# ============================================================================
# REDIS STATE MANAGER
# ============================================================================

class RedisStateManager:
    """
    Production-ready state management with Redis.
    
    Provides caching, session persistence, and state tracking
    for the ambient intelligence system.
    """
    
    # TTL configurations (seconds)
    TTL_CONFIG = {
        CacheType.EMBEDDING: 7 * 24 * 3600,      # 7 days
        CacheType.QUERY_RESULT: 3600,            # 1 hour
        CacheType.WARM_PREDICTION: 24 * 3600,    # 1 day
        CacheType.SESSION: 24 * 3600,            # 1 day
        CacheType.GRAPH: 2 * 24 * 3600,          # 2 days
        CacheType.ARCHETYPE_STATE: 3600,         # 1 hour
        CacheType.QUALITY_SCORE: 3600,           # 1 hour
        CacheType.RATE_LIMIT: 3600               # 1 hour
    }
    
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 key_prefix: str = 'ambient:'):
        """
        Initialize Redis state manager.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if auth enabled)
            key_prefix: Prefix for all keys
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        
        # Redis client (async)
        self.redis: Optional[Redis] = None
        self.connected = False
        
        # Statistics
        self.stats = CacheStats()
        
        # Local cache (fallback if Redis unavailable)
        self._local_cache: Dict[str, Tuple[Any, float]] = {}
        self._use_local_fallback = not REDIS_AVAILABLE
        
        print(f"RedisStateManager initialized")
        print(f"  Host: {host}:{port}")
        print(f"  DB: {db}")
        print(f"  Key prefix: {key_prefix}")
        print(f"  Redis available: {REDIS_AVAILABLE}")
    
    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            print("WARNING: Redis not available, using local fallback")
            self._use_local_fallback = True
            self.connected = False
            return
        
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            print("✓ Connected to Redis")
            
        except Exception as e:
            print(f"WARNING: Redis connection failed: {e}")
            print("  Falling back to local cache")
            self._use_local_fallback = True
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            print("✓ Disconnected from Redis")
    
    def _make_key(self, cache_type: CacheType, identifier: str) -> str:
        """Create Redis key with prefix and type"""
        return f"{self.key_prefix}{cache_type.value}:{identifier}"
    
    def _hash_query(self, query: str) -> str:
        """Hash query for cache key"""
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    # ========================================================================
    # GENERIC CACHE OPERATIONS
    # ========================================================================
    
    async def get(self,
                  cache_type: CacheType,
                  key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            cache_type: Type of cached data
            key: Cache key (will be prefixed)
        
        Returns:
            Cached value or None if not found
        """
        start = time.time()
        self.stats.total_requests += 1
        
        redis_key = self._make_key(cache_type, key)
        
        try:
            # Redis path
            if not self._use_local_fallback and self.redis:
                value_str = await self.redis.get(redis_key)
                
                if value_str:
                    # Hit
                    self.stats.cache_hits += 1
                    self.stats.hits_by_type[cache_type.value] = \
                        self.stats.hits_by_type.get(cache_type.value, 0) + 1
                    
                    # Update hit counter
                    await self.redis.incr(f"{redis_key}:hits")
                    
                    # Deserialize
                    value = json.loads(value_str)
                    
                    # Update stats
                    latency = (time.time() - start) * 1000
                    self._update_latency('get', latency)
                    
                    return value
            
            # Local fallback path
            elif key in self._local_cache:
                value, expiry = self._local_cache[key]
                
                # Check expiry
                if time.time() < expiry:
                    self.stats.cache_hits += 1
                    return value
                else:
                    # Expired
                    del self._local_cache[key]
            
            # Miss
            self.stats.cache_misses += 1
            self.stats.misses_by_type[cache_type.value] = \
                self.stats.misses_by_type.get(cache_type.value, 0) + 1
            
            return None
        
        except Exception as e:
            print(f"Cache get error: {e}")
            self.stats.cache_misses += 1
            return None
    
    async def set(self,
                  cache_type: CacheType,
                  key: str,
                  value: Any,
                  ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            cache_type: Type of cached data
            key: Cache key (will be prefixed)
            value: Value to cache
            ttl: Time-to-live in seconds (or use default for type)
        
        Returns:
            True if successful
        """
        start = time.time()
        
        redis_key = self._make_key(cache_type, key)
        
        # Get TTL
        if ttl is None:
            ttl = self.TTL_CONFIG.get(cache_type, 3600)
        
        try:
            # Serialize
            value_str = json.dumps(value)
            
            # Redis path
            if not self._use_local_fallback and self.redis:
                await self.redis.setex(redis_key, ttl, value_str)
                
                # Initialize hit counter
                await self.redis.setex(f"{redis_key}:hits", ttl, "0")
                
                # Update stats
                latency = (time.time() - start) * 1000
                self._update_latency('set', latency)
                
                return True
            
            # Local fallback path
            else:
                expiry = time.time() + ttl
                self._local_cache[key] = (value, expiry)
                return True
        
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, cache_type: CacheType, key: str) -> bool:
        """Delete value from cache"""
        redis_key = self._make_key(cache_type, key)
        
        try:
            if not self._use_local_fallback and self.redis:
                await self.redis.delete(redis_key)
                await self.redis.delete(f"{redis_key}:hits")
                return True
            else:
                if key in self._local_cache:
                    del self._local_cache[key]
                return True
        
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def exists(self, cache_type: CacheType, key: str) -> bool:
        """Check if key exists in cache"""
        redis_key = self._make_key(cache_type, key)
        
        try:
            if not self._use_local_fallback and self.redis:
                return await self.redis.exists(redis_key) > 0
            else:
                if key in self._local_cache:
                    _, expiry = self._local_cache[key]
                    return time.time() < expiry
                return False
        
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    # ========================================================================
    # SPECIALIZED CACHE OPERATIONS
    # ========================================================================
    
    async def cache_embedding(self,
                             text: str,
                             embedding: List[float]) -> bool:
        """
        Cache text embedding.
        
        Args:
            text: Original text
            embedding: Vector embedding
        
        Returns:
            True if cached successfully
        """
        key = self._hash_query(text)
        return await self.set(CacheType.EMBEDDING, key, embedding)
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        key = self._hash_query(text)
        return await self.get(CacheType.EMBEDDING, key)
    
    async def cache_query_result(self,
                                query: str,
                                response: str,
                                metadata: Dict) -> bool:
        """
        Cache query response.
        
        Args:
            query: User query
            response: System response
            metadata: Response metadata (archetypes, quality, etc.)
        
        Returns:
            True if cached successfully
        """
        key = self._hash_query(query)
        value = {
            'response': response,
            'metadata': metadata,
            'timestamp': time.time()
        }
        return await self.set(CacheType.QUERY_RESULT, key, value)
    
    async def get_query_result(self, query: str) -> Optional[Dict]:
        """Get cached query result"""
        key = self._hash_query(query)
        return await self.get(CacheType.QUERY_RESULT, key)
    
    async def cache_warm_prediction(self,
                                   current_archetype: str,
                                   predictions: List[Tuple[str, float]]) -> bool:
        """
        Cache warm circuit prediction.
        
        Args:
            current_archetype: Currently active archetype
            predictions: List of (archetype, probability) tuples
        
        Returns:
            True if cached successfully
        """
        return await self.set(
            CacheType.WARM_PREDICTION,
            current_archetype,
            predictions
        )
    
    async def get_warm_prediction(self,
                                 current_archetype: str) -> Optional[List[Tuple[str, float]]]:
        """Get cached warm circuit prediction"""
        return await self.get(CacheType.WARM_PREDICTION, current_archetype)
    
    async def cache_graph_result(self,
                                query: str,
                                results: List[Dict]) -> bool:
        """
        Cache graph traversal results.
        
        Args:
            query: Graph query
            results: Retrieved documents/chunks
        
        Returns:
            True if cached successfully
        """
        key = self._hash_query(query)
        return await self.set(CacheType.GRAPH, key, results)
    
    async def get_graph_result(self, query: str) -> Optional[List[Dict]]:
        """Get cached graph traversal result"""
        key = self._hash_query(query)
        return await self.get(CacheType.GRAPH, key)
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    async def create_session(self,
                           session_id: str,
                           user_id: str,
                           context: Optional[Dict] = None) -> SessionState:
        """
        Create new user session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            context: Initial context
        
        Returns:
            Session state
        """
        now = time.time()
        
        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            conversation_history=[],
            context=context or {},
            active_archetypes=[],
            query_count=0,
            created_at=now,
            last_active=now
        )
        
        await self.set(CacheType.SESSION, session_id, session.to_dict())
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session state"""
        data = await self.get(CacheType.SESSION, session_id)
        
        if data:
            return SessionState(**data)
        return None
    
    async def update_session(self, session: SessionState) -> bool:
        """Update session state"""
        session.last_active = time.time()
        return await self.set(CacheType.SESSION, session.session_id, session.to_dict())
    
    async def add_to_conversation(self,
                                 session_id: str,
                                 role: str,
                                 content: str) -> bool:
        """
        Add message to conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        
        Returns:
            True if successful
        """
        session = await self.get_session(session_id)
        
        if not session:
            return False
        
        session.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
        
        return await self.update_session(session)
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    
    async def check_rate_limit(self,
                              user_id: str,
                              limit: int,
                              window_seconds: int) -> Tuple[bool, int]:
        """
        Check rate limit for user.
        
        Args:
            user_id: User identifier
            limit: Maximum requests in window
            window_seconds: Time window in seconds
        
        Returns:
            (allowed, remaining_requests)
        """
        key = f"ratelimit:{user_id}"
        
        try:
            if not self._use_local_fallback and self.redis:
                # Increment counter
                count = await self.redis.incr(self._make_key(CacheType.RATE_LIMIT, key))
                
                # Set expiry on first request
                if count == 1:
                    await self.redis.expire(
                        self._make_key(CacheType.RATE_LIMIT, key),
                        window_seconds
                    )
                
                remaining = max(0, limit - count)
                allowed = count <= limit
                
                return (allowed, remaining)
            
            else:
                # Local fallback (simplified)
                return (True, limit)
        
        except Exception as e:
            print(f"Rate limit check error: {e}")
            return (True, limit)
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    def _update_latency(self, operation: str, latency_ms: float):
        """Update latency statistics"""
        if operation == 'get':
            if self.stats.avg_get_latency_ms == 0:
                self.stats.avg_get_latency_ms = latency_ms
            else:
                self.stats.avg_get_latency_ms = (
                    self.stats.avg_get_latency_ms * 0.9 + latency_ms * 0.1
                )
        
        elif operation == 'set':
            if self.stats.avg_set_latency_ms == 0:
                self.stats.avg_set_latency_ms = latency_ms
            else:
                self.stats.avg_set_latency_ms = (
                    self.stats.avg_set_latency_ms * 0.9 + latency_ms * 0.1
                )
    
    async def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        # Update hit rate
        if self.stats.total_requests > 0:
            self.stats.hit_rate = (
                self.stats.cache_hits / self.stats.total_requests
            )
        
        # Get memory usage (if Redis available)
        if not self._use_local_fallback and self.redis:
            try:
                info = await self.redis.info('memory')
                self.stats.memory_usage_mb = info.get('used_memory', 0) / (1024 * 1024)
                
                # Get key count
                self.stats.total_keys = await self.redis.dbsize()
            
            except Exception as e:
                print(f"Stats error: {e}")
        
        return self.stats
    
    def visualize_stats(self) -> str:
        """Create ASCII visualization of cache statistics"""
        stats = self.stats
        
        lines = []
        lines.append("=" * 80)
        lines.append("REDIS STATE MANAGER - STATISTICS")
        lines.append("=" * 80)
        lines.append(f"\nTotal requests: {stats.total_requests}")
        lines.append(f"Cache hits: {stats.cache_hits}")
        lines.append(f"Cache misses: {stats.cache_misses}")
        lines.append(f"Hit rate: {stats.hit_rate:.2%}")
        
        lines.append(f"\nHits by type:")
        for cache_type, hits in stats.hits_by_type.items():
            lines.append(f"  {cache_type}: {hits}")
        
        lines.append(f"\nPerformance:")
        lines.append(f"  Avg GET latency: {stats.avg_get_latency_ms:.2f}ms")
        lines.append(f"  Avg SET latency: {stats.avg_set_latency_ms:.2f}ms")
        
        lines.append(f"\nMemory:")
        lines.append(f"  Usage: {stats.memory_usage_mb:.1f} MB")
        lines.append(f"  Total keys: {stats.total_keys}")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)
    
    async def clear_cache(self, cache_type: Optional[CacheType] = None):
        """
        Clear cache.
        
        Args:
            cache_type: Specific cache type to clear (or None for all)
        """
        if not self._use_local_fallback and self.redis:
            if cache_type:
                # Clear specific type
                pattern = self._make_key(cache_type, "*")
                cursor = 0
                
                while True:
                    cursor, keys = await self.redis.scan(
                        cursor,
                        match=pattern,
                        count=100
                    )
                    
                    if keys:
                        await self.redis.delete(*keys)
                    
                    if cursor == 0:
                        break
                
                print(f"✓ Cleared cache type: {cache_type.value}")
            
            else:
                # Clear all
                await self.redis.flushdb()
                print("✓ Cleared all cache")
        
        else:
            # Clear local cache
            if cache_type:
                self._local_cache = {
                    k: v for k, v in self._local_cache.items()
                    if not k.startswith(cache_type.value)
                }
            else:
                self._local_cache.clear()


# ============================================================================
# TESTING
# ============================================================================

async def test_state_manager():
    """Test Redis state manager"""
    
    # Initialize
    manager = RedisStateManager()
    await manager.connect()
    
    print("\nTesting Redis State Manager")
    print("=" * 80)
    
    # Test 1: Embedding cache
    print("\n--- Test 1: Embedding Cache ---")
    text = "What is quantum entanglement?"
    embedding = [0.1] * 768
    
    await manager.cache_embedding(text, embedding)
    cached = await manager.get_embedding(text)
    
    print(f"Cached embedding: {cached is not None}")
    print(f"Match: {cached == embedding}")
    
    # Test 2: Query result cache
    print("\n--- Test 2: Query Result Cache ---")
    query = "Explain photosynthesis"
    response = "Photosynthesis is the process..."
    metadata = {'quality': 0.87, 'archetypes': ['mit_biology']}
    
    await manager.cache_query_result(query, response, metadata)
    cached_result = await manager.get_query_result(query)
    
    print(f"Cached result: {cached_result is not None}")
    if cached_result:
        print(f"  Response length: {len(cached_result['response'])}")
        print(f"  Metadata: {cached_result['metadata']}")
    
    # Test 3: Session management
    print("\n--- Test 3: Session Management ---")
    session_id = "test_session_1"
    user_id = "user_123"
    
    session = await manager.create_session(session_id, user_id)
    print(f"Created session: {session.session_id}")
    
    await manager.add_to_conversation(session_id, 'user', 'Hello')
    await manager.add_to_conversation(session_id, 'assistant', 'Hi!')
    
    retrieved = await manager.get_session(session_id)
    print(f"Conversation length: {len(retrieved.conversation_history)}")
    
    # Test 4: Warm prediction cache
    print("\n--- Test 4: Warm Prediction Cache ---")
    archetype = "mit_engineering"
    predictions = [("caltech_physics", 0.67), ("princeton_math", 0.42)]
    
    await manager.cache_warm_prediction(archetype, predictions)
    cached_pred = await manager.get_warm_prediction(archetype)
    
    print(f"Cached predictions: {cached_pred}")
    
    # Test 5: Rate limiting
    print("\n--- Test 5: Rate Limiting ---")
    for i in range(5):
        allowed, remaining = await manager.check_rate_limit("user_123", 3, 60)
        print(f"Request {i+1}: allowed={allowed}, remaining={remaining}")
    
    # Show statistics
    print("\n" + manager.visualize_stats())
    
    # Cleanup
    await manager.disconnect()


if __name__ == "__main__":
    asyncio.run(test_state_manager())

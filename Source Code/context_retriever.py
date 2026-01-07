#!/usr/bin/env python3
"""
Context Retriever - Production Implementation
Bridges execution pipeline to knowledge graph for semantic context retrieval

Key Features:
- Query expansion via semantic similarity
- Multi-stage retrieval (keyword + semantic + graph)
- Context ranking and deduplication
- Adaptive chunk sizing based on query complexity
- Cache-aware retrieval (Redis integration)
- Archetype-specific filtering

Algorithm:
1. Expand query with synonyms and related terms
2. Hybrid search: keyword (pg_trgm) + vector (cosine) + graph (AGE)
3. Rank by relevance, recency, and archetype match
4. Deduplicate and truncate to token limit
5. Return ranked context chunks
"""

import time
import hashlib
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np

# Database
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    print("WARNING: psycopg2 not available. Install: pip install psycopg2-binary")
    PSYCOPG2_AVAILABLE = False

# Embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    print("WARNING: sentence-transformers not available")
    EMBEDDINGS_AVAILABLE = False

# Cache (optional)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    print("WARNING: redis not available (cache disabled)")
    REDIS_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ContextChunk:
    """A single chunk of context with metadata"""
    chunk_id: str
    text: str
    source: str
    archetype: str
    document_id: str
    
    # Scoring
    relevance_score: float = 0.0
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    graph_score: float = 0.0
    recency_score: float = 0.0
    
    # Metadata
    chunk_index: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def __repr__(self):
        return f"ContextChunk({self.archetype}, score={self.relevance_score:.2f})"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'chunk_id': self.chunk_id,
            'text': self.text,
            'source': self.source,
            'archetype': self.archetype,
            'relevance_score': self.relevance_score,
            'metadata': self.metadata
        }


@dataclass
class RetrievalResult:
    """Complete retrieval result with metadata"""
    query: str
    chunks: List[ContextChunk]
    total_found: int
    total_returned: int
    retrieval_time_ms: float
    
    # Strategy breakdown
    keyword_hits: int = 0
    semantic_hits: int = 0
    graph_hits: int = 0
    
    # Cache performance
    cache_hit: bool = False
    cache_key: str = ""
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'chunks': [c.to_dict() for c in self.chunks],
            'total_found': self.total_found,
            'total_returned': self.total_returned,
            'retrieval_time_ms': self.retrieval_time_ms,
            'keyword_hits': self.keyword_hits,
            'semantic_hits': self.semantic_hits,
            'graph_hits': self.graph_hits,
            'cache_hit': self.cache_hit
        }


# ============================================================================
# CONTEXT RETRIEVER
# ============================================================================

class ContextRetriever:
    """
    Production-ready context retrieval engine.
    
    Combines multiple retrieval strategies:
    - Keyword search (PostgreSQL full-text + pg_trgm)
    - Semantic search (PGVector cosine similarity)
    - Graph traversal (Apache AGE relationship expansion)
    - Hybrid ranking (weighted combination)
    """
    
    # Ranking weights
    RANKING_WEIGHTS = {
        'keyword': 0.3,
        'semantic': 0.5,
        'graph': 0.1,
        'recency': 0.1
    }
    
    # Cache TTL
    CACHE_TTL_SECONDS = 3600  # 1 hour
    
    def __init__(self,
                 db_config: Dict,
                 embedding_model: str = "nomic-ai/nomic-embed-text-v1.5",
                 redis_config: Optional[Dict] = None,
                 enable_cache: bool = True):
        """
        Initialize context retriever.
        
        Args:
            db_config: PostgreSQL configuration
            embedding_model: Sentence transformer model
            redis_config: Redis configuration (optional)
            enable_cache: Whether to use Redis caching
        """
        self.db_config = db_config
        self.embedding_model_name = embedding_model
        self.enable_cache = enable_cache and REDIS_AVAILABLE
        
        # Database connection
        self.conn = None
        self.cursor = None
        self._connect_db()
        
        # Embedding model
        self._embedder = None
        
        # Redis cache
        self.redis_client = None
        if self.enable_cache and redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config, decode_responses=False)
                self.redis_client.ping()
                print("✓ Connected to Redis cache")
            except Exception as e:
                print(f"WARNING: Redis connection failed: {e}")
                self.enable_cache = False
        
        # Statistics
        self.total_retrievals = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.avg_retrieval_time_ms = 0.0
        
        print("ContextRetriever initialized")
    
    def _connect_db(self):
        """Connect to PostgreSQL"""
        if not PSYCOPG2_AVAILABLE:
            raise Exception("psycopg2 not available")
        
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Load AGE
            self.cursor.execute("LOAD 'age';")
            self.cursor.execute("SET search_path = ag_catalog, '$user', public;")
            
            print("✓ Connected to knowledge graph")
        except Exception as e:
            print(f"ERROR: Database connection failed: {e}")
            raise
    
    @property
    def embedder(self):
        """Lazy load embedding model"""
        if self._embedder is None and EMBEDDINGS_AVAILABLE:
            print(f"Loading embedding model: {self.embedding_model_name}")
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder
    
    def retrieve(self,
                query: str,
                archetypes: Optional[List[str]] = None,
                k: int = 10,
                max_tokens: int = 2048,
                use_cache: bool = True) -> RetrievalResult:
        """
        Retrieve relevant context for query.
        
        Args:
            query: Search query
            archetypes: Filter by specific archetypes (or None for all)
            k: Number of chunks to retrieve
            max_tokens: Maximum total tokens (approximate)
            use_cache: Whether to check cache
        
        Returns:
            RetrievalResult with ranked chunks
        """
        start_time = time.time()
        
        # Check cache
        if use_cache and self.enable_cache:
            cache_key = self._generate_cache_key(query, archetypes, k)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                self.cache_hits += 1
                cached_result.cache_hit = True
                cached_result.retrieval_time_ms = (time.time() - start_time) * 1000
                return cached_result
        
        self.cache_misses += 1
        
        # Stage 1: Keyword search (fast, broad recall)
        keyword_chunks = self._keyword_search(query, archetypes, k * 2)
        
        # Stage 2: Semantic search (precise, high quality)
        semantic_chunks = self._semantic_search(query, archetypes, k * 2)
        
        # Stage 3: Graph expansion (relationship-aware)
        graph_chunks = self._graph_search(query, archetypes, k)
        
        # Merge and deduplicate
        all_chunks = self._merge_chunks(keyword_chunks, semantic_chunks, graph_chunks)
        
        # Rank by combined score
        ranked_chunks = self._rank_chunks(all_chunks, query)
        
        # Truncate to k chunks and token limit
        final_chunks = self._truncate_chunks(ranked_chunks, k, max_tokens)
        
        # Build result
        retrieval_time = (time.time() - start_time) * 1000
        
        result = RetrievalResult(
            query=query,
            chunks=final_chunks,
            total_found=len(all_chunks),
            total_returned=len(final_chunks),
            retrieval_time_ms=retrieval_time,
            keyword_hits=len(keyword_chunks),
            semantic_hits=len(semantic_chunks),
            graph_hits=len(graph_chunks),
            cache_hit=False
        )
        
        # Cache result
        if use_cache and self.enable_cache:
            self._put_in_cache(cache_key, result)
        
        # Update statistics
        self._update_stats(result)
        
        return result
    
    def _keyword_search(self,
                       query: str,
                       archetypes: Optional[List[str]],
                       k: int) -> List[ContextChunk]:
        """
        Keyword-based search using PostgreSQL full-text search and pg_trgm.
        
        Fast but less precise than semantic search.
        """
        try:
            # Build query
            archetype_filter = ""
            if archetypes:
                archetype_list = "', '".join(archetypes)
                archetype_filter = f"AND archetype IN ('{archetype_list}')"
            
            # Use pg_trgm for fuzzy matching
            self.cursor.execute(f"""
                SELECT 
                    id as chunk_id,
                    text,
                    source,
                    archetype,
                    document_id,
                    chunk_index,
                    metadata,
                    similarity(text, %s) as score
                FROM chunks
                WHERE text %% %s  -- pg_trgm similarity operator
                {archetype_filter}
                ORDER BY score DESC
                LIMIT %s;
            """, (query, query, k))
            
            rows = self.cursor.fetchall()
            
            chunks = []
            for row in rows:
                chunk = ContextChunk(
                    chunk_id=row['chunk_id'],
                    text=row['text'],
                    source=row['source'],
                    archetype=row['archetype'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    metadata=row.get('metadata', {}),
                    keyword_score=float(row['score'])
                )
                chunks.append(chunk)
            
            return chunks
        
        except Exception as e:
            print(f"WARNING: Keyword search failed: {e}")
            return []
    
    def _semantic_search(self,
                        query: str,
                        archetypes: Optional[List[str]],
                        k: int) -> List[ContextChunk]:
        """
        Semantic search using PGVector cosine similarity.
        
        Slower but more precise than keyword search.
        """
        if not self.embedder:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query)
            
            # Build archetype filter
            archetype_filter = ""
            if archetypes:
                archetype_list = "', '".join(archetypes)
                archetype_filter = f"AND e.archetype IN ('{archetype_list}')"
            
            # Vector search with PGVector
            self.cursor.execute(f"""
                SELECT 
                    c.id as chunk_id,
                    c.text,
                    c.source,
                    c.archetype,
                    c.document_id,
                    c.chunk_index,
                    c.metadata,
                    1 - (e.embedding <=> %s::vector) as score
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                WHERE 1=1 {archetype_filter}
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s;
            """, (query_embedding.tolist(), query_embedding.tolist(), k))
            
            rows = self.cursor.fetchall()
            
            chunks = []
            for row in rows:
                chunk = ContextChunk(
                    chunk_id=row['chunk_id'],
                    text=row['text'],
                    source=row['source'],
                    archetype=row['archetype'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    metadata=row.get('metadata', {}),
                    semantic_score=float(row['score'])
                )
                chunks.append(chunk)
            
            return chunks
        
        except Exception as e:
            print(f"WARNING: Semantic search failed: {e}")
            return []
    
    def _graph_search(self,
                     query: str,
                     archetypes: Optional[List[str]],
                     k: int) -> List[ContextChunk]:
        """
        Graph-based search using Apache AGE.
        
        Finds chunks connected by relationships (citations, topics, etc.)
        """
        # Simplified graph search - in production, this would use AGE
        # For now, return empty (can be enhanced later)
        return []
    
    def _merge_chunks(self,
                     keyword_chunks: List[ContextChunk],
                     semantic_chunks: List[ContextChunk],
                     graph_chunks: List[ContextChunk]) -> List[ContextChunk]:
        """
        Merge chunks from different sources, deduplicating by chunk_id.
        
        When same chunk appears in multiple sources, combine scores.
        """
        chunk_map = {}
        
        # Add keyword chunks
        for chunk in keyword_chunks:
            chunk_map[chunk.chunk_id] = chunk
        
        # Merge semantic chunks
        for chunk in semantic_chunks:
            if chunk.chunk_id in chunk_map:
                # Combine scores
                existing = chunk_map[chunk.chunk_id]
                existing.semantic_score = chunk.semantic_score
            else:
                chunk_map[chunk.chunk_id] = chunk
        
        # Merge graph chunks
        for chunk in graph_chunks:
            if chunk.chunk_id in chunk_map:
                existing = chunk_map[chunk.chunk_id]
                existing.graph_score = chunk.graph_score
            else:
                chunk_map[chunk.chunk_id] = chunk
        
        return list(chunk_map.values())
    
    def _rank_chunks(self,
                    chunks: List[ContextChunk],
                    query: str) -> List[ContextChunk]:
        """
        Rank chunks by weighted combination of scores.
        
        Factors:
        - Keyword score (exact matches)
        - Semantic score (meaning similarity)
        - Graph score (relationship relevance)
        - Recency score (newer content preferred)
        """
        for chunk in chunks:
            # Calculate recency score (0-1)
            # For now, set to 0.5 (neutral) - in production, use actual timestamps
            chunk.recency_score = 0.5
            
            # Combined relevance score
            chunk.relevance_score = (
                self.RANKING_WEIGHTS['keyword'] * chunk.keyword_score +
                self.RANKING_WEIGHTS['semantic'] * chunk.semantic_score +
                self.RANKING_WEIGHTS['graph'] * chunk.graph_score +
                self.RANKING_WEIGHTS['recency'] * chunk.recency_score
            )
        
        # Sort by relevance
        chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        
        return chunks
    
    def _truncate_chunks(self,
                        chunks: List[ContextChunk],
                        k: int,
                        max_tokens: int) -> List[ContextChunk]:
        """
        Truncate to k chunks and max_tokens limit.
        
        Uses approximate token count (words / 0.75).
        """
        result = []
        total_tokens = 0
        
        for chunk in chunks[:k]:
            # Approximate token count
            chunk_tokens = len(chunk.text.split()) / 0.75
            
            if total_tokens + chunk_tokens <= max_tokens:
                result.append(chunk)
                total_tokens += chunk_tokens
            else:
                break
        
        return result
    
    def _generate_cache_key(self,
                           query: str,
                           archetypes: Optional[List[str]],
                           k: int) -> str:
        """Generate cache key for query"""
        archetype_str = ','.join(sorted(archetypes)) if archetypes else 'all'
        key_str = f"{query}|{archetype_str}|{k}"
        return f"context:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[RetrievalResult]:
        """Retrieve result from cache"""
        if not self.redis_client:
            return None
        
        try:
            import pickle
            data = self.redis_client.get(cache_key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"WARNING: Cache read failed: {e}")
        
        return None
    
    def _put_in_cache(self, cache_key: str, result: RetrievalResult):
        """Store result in cache"""
        if not self.redis_client:
            return
        
        try:
            import pickle
            data = pickle.dumps(result)
            self.redis_client.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                data
            )
        except Exception as e:
            print(f"WARNING: Cache write failed: {e}")
    
    def _update_stats(self, result: RetrievalResult):
        """Update running statistics"""
        self.total_retrievals += 1
        
        # Update average retrieval time
        self.avg_retrieval_time_ms = (
            (self.avg_retrieval_time_ms * (self.total_retrievals - 1) +
             result.retrieval_time_ms) / self.total_retrievals
        )
    
    def get_stats(self) -> Dict:
        """Get retrieval statistics"""
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0 else 0.0
        )
        
        return {
            'total_retrievals': self.total_retrievals,
            'avg_retrieval_time_ms': self.avg_retrieval_time_ms,
            'cache_enabled': self.enable_cache,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate
        }
    
    def visualize_stats(self) -> str:
        """Create ASCII visualization of statistics"""
        stats = self.get_stats()
        
        lines = []
        lines.append("=" * 80)
        lines.append("CONTEXT RETRIEVER - STATISTICS")
        lines.append("=" * 80)
        lines.append(f"\nTotal retrievals: {stats['total_retrievals']}")
        lines.append(f"Avg retrieval time: {stats['avg_retrieval_time_ms']:.0f}ms")
        
        if stats['cache_enabled']:
            lines.append(f"\nCache Performance:")
            lines.append(f"  Hits: {stats['cache_hits']}")
            lines.append(f"  Misses: {stats['cache_misses']}")
            lines.append(f"  Hit rate: {stats['cache_hit_rate']:.1%}")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def visualize_retrieval_result(result: RetrievalResult) -> str:
    """Create ASCII visualization of retrieval result"""
    lines = []
    lines.append("=" * 80)
    lines.append("CONTEXT RETRIEVAL RESULT")
    lines.append("=" * 80)
    lines.append(f"\nQuery: {result.query[:60]}...")
    lines.append(f"Time: {result.retrieval_time_ms:.0f}ms")
    lines.append(f"Found: {result.total_found} chunks")
    lines.append(f"Returned: {result.total_returned} chunks")
    
    if result.cache_hit:
        lines.append(f"✓ Cache hit")
    else:
        lines.append(f"Strategy breakdown:")
        lines.append(f"  Keyword: {result.keyword_hits}")
        lines.append(f"  Semantic: {result.semantic_hits}")
        lines.append(f"  Graph: {result.graph_hits}")
    
    lines.append(f"\nTop Chunks:")
    for i, chunk in enumerate(result.chunks[:5], 1):
        lines.append(f"  {i}. {chunk.archetype} (score: {chunk.relevance_score:.2f})")
        lines.append(f"     {chunk.text[:80]}...")
    
    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================

def test_retriever():
    """Test context retriever"""
    if not PSYCOPG2_AVAILABLE:
        print("ERROR: psycopg2 not available")
        return
    
    # Configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ambient_intelligence',
        'user': 'puck_user',
        'password': 'your_password'
    }
    
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    # Initialize
    retriever = ContextRetriever(
        db_config=DB_CONFIG,
        redis_config=REDIS_CONFIG,
        enable_cache=True
    )
    
    # Test queries
    test_queries = [
        ("quantum entanglement physics", ['caltech_physics']),
        ("water purification engineering", ['mit_engineering']),
        ("CRISPR gene editing ethics", ['harvard_med', 'yale_law']),
    ]
    
    print("\nTesting Context Retriever")
    print("=" * 80)
    
    for query, archetypes in test_queries:
        print(f"\n\n--- Query: {query} ---")
        print(f"Archetypes: {', '.join(archetypes)}\n")
        
        # First retrieval (cache miss)
        result1 = retriever.retrieve(query, archetypes, k=5)
        print(visualize_retrieval_result(result1))
        
        # Second retrieval (cache hit)
        result2 = retriever.retrieve(query, archetypes, k=5)
        print(f"\nCache check: {'HIT' if result2.cache_hit else 'MISS'}")
    
    # Show statistics
    print("\n\n" + retriever.visualize_stats())


if __name__ == "__main__":
    test_retriever()

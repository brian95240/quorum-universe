#!/usr/bin/env python3
"""
Knowledge Graph - Universal Storage for 20 Institutional Archetypes
Stores ALL 620 GB of knowledge as graph + embeddings
Apache AGE (graph) + PGVector (embeddings) + PostgreSQL
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    print("ERROR: Install psycopg2-binary: pip install psycopg2-binary")
    exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("WARNING: sentence-transformers not found. Using fallback embeddings.")
    SentenceTransformer = None


# ============================================================================
# ARCHETYPE DEFINITIONS (ALL 20)
# ============================================================================

ARCHETYPES = {
    # Tier 1: Original 8
    'mit_engineering': {
        'cluster': 'stem_core',
        'sources': ['MIT OCW', 'MIT CSAIL', 'MIT Media Lab'],
        'corpus_size_gb': 160,
        'domains': ['engineering', 'robotics', 'systems', 'design'],
        'style': 'Applied, constraint-driven, diagram-first',
        'temperature': 0.7
    },
    'caltech_physics': {
        'cluster': 'stem_core',
        'sources': ['Feynman Lectures', 'Caltech Seminars', 'arXiv Physics'],
        'corpus_size_gb': 86,
        'domains': ['physics', 'cosmology', 'quantum', 'relativity'],
        'style': 'First-principles, reductionist, intuitive clarity',
        'temperature': 0.6
    },
    'princeton_math': {
        'cluster': 'stem_core',
        'sources': ['Terry Tao Blog', 'Princeton Math Dept', 'Annals of Math'],
        'corpus_size_gb': 22,
        'domains': ['mathematics', 'proof', 'analysis', 'topology'],
        'style': 'Pure abstraction, proof-based, elegant',
        'temperature': 0.65
    },
    'stanford_cs': {
        'cluster': 'applied_tech',
        'sources': ['CS229', 'CS231n', 'CS224n', 'Stanford AI Lab'],
        'corpus_size_gb': 18,
        'domains': ['computer_science', 'machine_learning', 'algorithms'],
        'style': 'Scalable, code-first, ship-focused',
        'temperature': 0.7
    },
    'harvard_med': {
        'cluster': 'life_systems',
        'sources': ['Harvard Med Open', 'NEJM Open', 'HMS Lectures'],
        'corpus_size_gb': 65,
        'domains': ['medicine', 'clinical', 'diagnostics', 'physiology'],
        'style': 'Clinical reasoning, probabilistic, evidence-based',
        'temperature': 0.65
    },
    'yale_law': {
        'cluster': 'human_systems',
        'sources': ['Yale Law Readers', 'SCOTUS Opinions', 'Intl Law'],
        'corpus_size_gb': 42,
        'domains': ['law', 'policy', 'rights', 'precedent'],
        'style': 'Adversarial, precedent-heavy, distinguish-or-concede',
        'temperature': 0.65
    },
    'oxford_classics': {
        'cluster': 'human_systems',
        'sources': ['Perseus Project', 'Oxford Papers', 'Plato/Aristotle', 'Cambridge History'],
        'corpus_size_gb': 35,
        'domains': ['classics', 'philosophy', 'history', 'literature'],
        'style': 'Dialectical, narrative, historiographic',
        'temperature': 0.75
    },
    'mensa_orthogonal': {
        'cluster': 'meta_cognitive',
        'sources': ['Mensa Bulletin 1960-2025', 'World Puzzle Federation', 'Lateral Thinking'],
        'corpus_size_gb': 4,
        'domains': ['puzzles', 'patterns', 'lateral_thinking'],
        'style': 'Non-linear, pattern-seeking, assume-nothing',
        'temperature': 0.9
    },
    
    # Tier 2: Non-Western
    'beijing_classical': {
        'cluster': 'non_western',
        'sources': ['Art of War', 'Analects', 'Daodejing', 'I Ching', 'TCM', '36 Stratagems'],
        'corpus_size_gb': 8,
        'domains': ['strategy', 'eastern_philosophy', 'traditional_medicine'],
        'style': 'Strategic, paradoxical, harmony-seeking',
        'temperature': 0.75
    },
    'baghdad_golden': {
        'cluster': 'non_western',
        'sources': ['Al-Khwarizmi', 'Ibn Sina', 'Al-Haytham', 'Islamic Astronomy', 'Sufi Texts'],
        'corpus_size_gb': 12,
        'domains': ['islamic_science', 'mathematics', 'optics', 'medicine'],
        'style': 'Empirical, geometric, spiritual-rational synthesis',
        'temperature': 0.7
    },
    'nalanda_vedic': {
        'cluster': 'non_western',
        'sources': ['Aryabhata', 'Ramanujan', 'Sushruta Samhita', 'Buddhist Logic', 'Vedic Math'],
        'corpus_size_gb': 6,
        'domains': ['indian_mathematics', 'ayurveda', 'logic', 'consciousness'],
        'style': 'Intuitive-deductive, infinity-aware, holistic',
        'temperature': 0.72
    },
    
    # Tier 3: Life Sciences
    'broad_genomics': {
        'cluster': 'life_systems',
        'sources': ['Broad Institute', 'bioRxiv', 'PubMed Central Genetics'],
        'corpus_size_gb': 120,
        'domains': ['genomics', 'evolution', 'molecular_biology', 'genetics'],
        'style': 'Data-driven, evolutionary, systems biology',
        'temperature': 0.7
    },
    'berkeley_psychedelics': {
        'cluster': 'creative_synthesis',
        'sources': ['MAPS Research', 'Hopkins Studies', 'Huxley', 'Shulgin', 'Consciousness Papers'],
        'corpus_size_gb': 8,
        'domains': ['consciousness', 'psychedelics', 'phenomenology'],
        'style': 'Experiential, non-ordinary states, phenomenological',
        'temperature': 0.85
    },
    
    # Tier 4: Social Systems
    'chicago_economics': {
        'cluster': 'human_systems',
        'sources': ['NBER', 'Friedman', 'Hayek', 'Becker', 'Coase', 'Thaler'],
        'corpus_size_gb': 28,
        'domains': ['economics', 'incentives', 'markets', 'behavior'],
        'style': 'Incentive-focused, market-based, rational-choice',
        'temperature': 0.7
    },
    
    # Tier 5: Creative & Applied
    'bauhaus_design': {
        'cluster': 'creative_synthesis',
        'sources': ['Bauhaus Manifestos', 'Moholy-Nagy', 'RISD', 'Dieter Rams', 'Pattern Language'],
        'corpus_size_gb': 5,
        'domains': ['design', 'architecture', 'aesthetics', 'systems_thinking'],
        'style': 'Form-follows-function, gestalt, minimalist',
        'temperature': 0.8
    },
    'hacker_insurgent': {
        'cluster': 'applied_tech',
        'sources': ['GNU Manifesto', 'Phrack', '2600', 'Jargon File', 'Cypherpunk', 'Swartz'],
        'corpus_size_gb': 3,
        'domains': ['hacking', 'security', 'foss', 'freedom'],
        'style': 'Lateral, exploit-seeking, anti-authoritarian',
        'temperature': 0.8
    },
    
    # Tier 6: Edge Knowledge
    'indigenous_ecology': {
        'cluster': 'creative_synthesis',
        'sources': ['TEK Databases', 'Ethnobotany', 'Permaculture', 'Biomimicry'],
        'corpus_size_gb': 4,
        'domains': ['ecology', 'traditional_knowledge', 'sustainability'],
        'style': 'Holistic, multi-generational, reciprocal',
        'temperature': 0.75
    },
    'complexity_science': {
        'cluster': 'stem_core',
        'sources': ['Santa Fe Institute', 'Emergence Papers', 'Network Science'],
        'corpus_size_gb': 15,
        'domains': ['complexity', 'emergence', 'networks', 'chaos'],
        'style': 'Systems-level, non-linear, emergent properties',
        'temperature': 0.75
    },
    'ai_safety': {
        'cluster': 'applied_tech',
        'sources': ['Anthropic', 'OpenAI Safety', 'MIRI', 'AI Alignment Forum', 'Bostrom'],
        'corpus_size_gb': 8,
        'domains': ['ai_safety', 'alignment', 'x-risk', 'ethics'],
        'style': 'Cautious, long-term, adversarial-robust',
        'temperature': 0.65
    },
    'longevity_research': {
        'cluster': 'life_systems',
        'sources': ['SENS Research', 'Aubrey de Grey', 'Longevity Journals', 'Horvath', 'Sinclair'],
        'corpus_size_gb': 12,
        'domains': ['longevity', 'aging', 'regeneration', 'biomarkers'],
        'style': 'Interventionist, damage-repair, optimistic',
        'temperature': 0.7
    }
}

# Calculate totals
TOTAL_CORPUS_GB = sum(a['corpus_size_gb'] for a in ARCHETYPES.values())
TOTAL_ARCHETYPES = len(ARCHETYPES)

print(f"✓ Loaded {TOTAL_ARCHETYPES} archetypes, total corpus: {TOTAL_CORPUS_GB} GB")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Chunk:
    """Represents a 512-token chunk of knowledge"""
    id: str
    text: str
    source: str
    archetype: str
    document_id: str
    chunk_index: int
    embedding: Optional[np.ndarray] = None
    metadata: Optional[Dict] = None


@dataclass
class Document:
    """Represents a source document"""
    id: str
    title: str
    source: str
    archetype: str
    file_path: str
    size_bytes: int
    chunk_count: int
    metadata: Optional[Dict] = None


# ============================================================================
# EMBEDDING ENGINE
# ============================================================================

class EmbeddingEngine:
    """Generate embeddings using Nomic-Embed or fallback"""
    
    def __init__(self, model_name: str = 'nomic-ai/nomic-embed-text-v1.5'):
        if SentenceTransformer:
            print(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.dimension = 768
        else:
            print("WARNING: Using fallback random embeddings")
            self.model = None
            self.dimension = 768
    
    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for list of texts"""
        if self.model:
            return self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100
            )
        else:
            # Fallback: deterministic random based on text hash
            embeddings = []
            for text in texts:
                seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
                np.random.seed(seed % (2**32))
                embeddings.append(np.random.randn(self.dimension))
            return np.array(embeddings)
    
    def encode_single(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        return self.encode([text])[0]


# ============================================================================
# KNOWLEDGE GRAPH (Apache AGE + PGVector)
# ============================================================================

class KnowledgeGraph:
    """
    Universal knowledge storage for all 20 archetypes.
    - Graph: Apache AGE (relationships, structure)
    - Vectors: PGVector (semantic search)
    - Metadata: PostgreSQL (indexing, filtering)
    """
    
    def __init__(self, db_config: Dict):
        self.config = db_config
        self.conn = None
        self.cursor = None
        self.embedder = EmbeddingEngine()
        
        self._connect()
        self._init_schema()
    
    def _connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✓ Connected to PostgreSQL")
        except Exception as e:
            print(f"ERROR: Database connection failed: {e}")
            raise
    
    def _init_schema(self):
        """Initialize AGE graph + PGVector + metadata tables"""
        try:
            # Create extensions
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS age;")
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            
            # Load AGE
            self.cursor.execute("LOAD 'age';")
            self.cursor.execute("SET search_path = ag_catalog, '$user', public;")
            
            # Create graph
            graph_name = 'knowledge_graph'
            self.cursor.execute(f"""
                SELECT create_graph('{graph_name}')
                WHERE NOT EXISTS (
                    SELECT 1 FROM ag_catalog.ag_graph WHERE name = '{graph_name}'
                );
            """)
            
            # Create metadata tables
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    archetype TEXT,
                    file_path TEXT,
                    size_bytes BIGINT,
                    chunk_count INTEGER,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT REFERENCES documents(id),
                    text TEXT,
                    chunk_index INTEGER,
                    archetype TEXT,
                    source TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create vector table (PGVector)
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY REFERENCES chunks(id),
                    embedding vector({self.embedder.dimension}),
                    archetype TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create indexes
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_archetype 
                ON chunks(archetype);
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_document 
                ON chunks(document_id);
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_text_search 
                ON chunks USING gin(text gin_trgm_ops);
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_archetype 
                ON embeddings(archetype);
            """)
            
            # Vector similarity index (IVFFlat for speed)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
                ON embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            
            self.conn.commit()
            print("✓ Schema initialized (AGE + PGVector + metadata)")
            
        except Exception as e:
            print(f"ERROR: Schema initialization failed: {e}")
            self.conn.rollback()
            raise
    
    def ingest_document(self, doc: Document, chunks: List[Chunk]) -> bool:
        """
        Ingest a document and its chunks into the knowledge graph.
        Returns True on success.
        """
        try:
            # Insert document metadata
            self.cursor.execute("""
                INSERT INTO documents 
                (id, title, source, archetype, file_path, size_bytes, chunk_count, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, (
                doc.id, doc.title, doc.source, doc.archetype,
                doc.file_path, doc.size_bytes, doc.chunk_count,
                json.dumps(doc.metadata) if doc.metadata else None
            ))
            
            # Batch insert chunks
            chunk_data = [
                (c.id, c.document_id, c.text, c.chunk_index, 
                 c.archetype, c.source, json.dumps(c.metadata) if c.metadata else None)
                for c in chunks
            ]
            
            execute_values(
                self.cursor,
                """
                INSERT INTO chunks 
                (id, document_id, text, chunk_index, archetype, source, metadata)
                VALUES %s
                ON CONFLICT (id) DO NOTHING;
                """,
                chunk_data
            )
            
            # Generate and insert embeddings
            texts = [c.text for c in chunks]
            embeddings = self.embedder.encode(texts)
            
            embedding_data = [
                (chunks[i].id, embeddings[i].tolist(), chunks[i].archetype)
                for i in range(len(chunks))
            ]
            
            execute_values(
                self.cursor,
                """
                INSERT INTO embeddings (chunk_id, embedding, archetype)
                VALUES %s
                ON CONFLICT (chunk_id) DO NOTHING;
                """,
                embedding_data
            )
            
            # Create graph nodes (AGE)
            for chunk in chunks:
                self.cursor.execute(f"""
                    SELECT * FROM cypher('knowledge_graph', $$
                        CREATE (c:Chunk {{
                            id: '{chunk.id}',
                            archetype: '{chunk.archetype}',
                            source: '{chunk.source}',
                            text_preview: '{chunk.text[:100].replace("'", "")}'
                        }})
                    $$) as (result agtype);
                """)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"ERROR: Document ingestion failed: {e}")
            self.conn.rollback()
            return False
    
    def semantic_search(
        self,
        query_text: str,
        top_k: int = 20,
        archetype_filter: Optional[str] = None,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Semantic search across knowledge graph.
        Returns relevant chunks with metadata.
        """
        # Generate query embedding
        query_embedding = self.embedder.encode_single(query_text)
        
        # Build query
        archetype_clause = ""
        if archetype_filter:
            archetype_clause = f"AND e.archetype = '{archetype_filter}'"
        
        query = f"""
            SELECT 
                c.id,
                c.text,
                c.archetype,
                c.source,
                c.chunk_index,
                c.metadata,
                d.title as document_title,
                1 - (e.embedding <=> %s::vector) as similarity
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE 1 - (e.embedding <=> %s::vector) > %s
            {archetype_clause}
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s;
        """
        
        self.cursor.execute(
            query,
            (query_embedding.tolist(), query_embedding.tolist(), 
             min_similarity, query_embedding.tolist(), top_k)
        )
        
        results = self.cursor.fetchall()
        
        return [dict(r) for r in results]
    
    def get_archetype_stats(self) -> Dict:
        """Get statistics for each archetype"""
        self.cursor.execute("""
            SELECT 
                archetype,
                COUNT(DISTINCT document_id) as doc_count,
                COUNT(*) as chunk_count,
                AVG(LENGTH(text)) as avg_chunk_length
            FROM chunks
            GROUP BY archetype
            ORDER BY chunk_count DESC;
        """)
        
        stats = {}
        for row in self.cursor.fetchall():
            stats[row['archetype']] = {
                'documents': row['doc_count'],
                'chunks': row['chunk_count'],
                'avg_chunk_length': float(row['avg_chunk_length']) if row['avg_chunk_length'] else 0
            }
        
        return stats
    
    def get_coactivation_matrix(self) -> np.ndarray:
        """
        Build co-activation matrix from query logs.
        Shows which archetypes tend to be used together.
        """
        # This would be populated by the router
        # For now, return zeros
        n = len(ARCHETYPES)
        return np.zeros((n, n))
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")


# ============================================================================
# INGESTION HELPERS
# ============================================================================

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """
    Split text into overlapping chunks.
    chunk_size: tokens (approximated as ~4 chars)
    """
    chars_per_chunk = chunk_size * 4
    overlap_chars = overlap * 4
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chars_per_chunk
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk)
        
        start = end - overlap_chars
    
    return chunks


def create_document_from_file(
    file_path: str,
    archetype: str,
    source: str,
    title: Optional[str] = None
) -> Tuple[Document, List[Chunk]]:
    """
    Load a file and create document + chunks.
    """
    import os
    
    # Read file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    # Generate IDs
    doc_id = hashlib.sha256(file_path.encode()).hexdigest()[:16]
    
    # Create chunks
    chunk_texts = chunk_text(text)
    chunks = []
    
    for i, chunk_text in enumerate(chunk_texts):
        chunk_id = f"{doc_id}_{i:04d}"
        chunks.append(Chunk(
            id=chunk_id,
            text=chunk_text,
            source=source,
            archetype=archetype,
            document_id=doc_id,
            chunk_index=i,
            metadata={'file_path': file_path}
        ))
    
    # Create document
    doc = Document(
        id=doc_id,
        title=title or os.path.basename(file_path),
        source=source,
        archetype=archetype,
        file_path=file_path,
        size_bytes=len(text),
        chunk_count=len(chunks),
        metadata={'char_count': len(text)}
    )
    
    return doc, chunks


# ============================================================================
# MAIN (FOR TESTING)
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Graph Management')
    parser.add_argument('--init', action='store_true', help='Initialize schema')
    parser.add_argument('--ingest', type=str, help='Ingest file (format: archetype:source:path)')
    parser.add_argument('--search', type=str, help='Semantic search query')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--archetype', type=str, help='Filter by archetype')
    
    args = parser.parse_args()
    
    # Database config
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ambient_intelligence',
        'user': 'puck_user',
        'password': 'change_me_in_production'
    }
    
    kg = KnowledgeGraph(DB_CONFIG)
    
    try:
        if args.init:
            print("Schema already initialized during connection")
        
        elif args.ingest:
            parts = args.ingest.split(':')
            if len(parts) != 3:
                print("ERROR: Format: archetype:source:path")
                exit(1)
            
            archetype, source, path = parts
            
            if archetype not in ARCHETYPES:
                print(f"ERROR: Unknown archetype: {archetype}")
                print(f"Available: {', '.join(ARCHETYPES.keys())}")
                exit(1)
            
            print(f"Ingesting {path}...")
            doc, chunks = create_document_from_file(path, archetype, source)
            
            if kg.ingest_document(doc, chunks):
                print(f"✓ Ingested {len(chunks)} chunks")
            else:
                print("✗ Ingestion failed")
        
        elif args.search:
            print(f"Searching for: {args.search}")
            results = kg.semantic_search(
                args.search,
                top_k=10,
                archetype_filter=args.archetype
            )
            
            print(f"\nFound {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. [{result['archetype']}] {result['document_title']}")
                print(f"   Similarity: {result['similarity']:.3f}")
                print(f"   {result['text'][:200]}...")
                print()
        
        elif args.stats:
            stats = kg.get_archetype_stats()
            
            print("\nArchetype Statistics:")
            print("=" * 80)
            for archetype, data in stats.items():
                print(f"{archetype:20s} | Docs: {data['documents']:4d} | "
                      f"Chunks: {data['chunks']:6d} | "
                      f"Avg Length: {data['avg_chunk_length']:.0f}")
        
        else:
            print("Use --init, --ingest, --search, or --stats")
    
    finally:
        kg.close()

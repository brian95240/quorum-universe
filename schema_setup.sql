-- Quorum Universe Database Schema
-- PostgreSQL with pgvector for Apache AGE-style graph operations

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Schema
CREATE SCHEMA IF NOT EXISTS quorum;

-- Archetypes table
CREATE TABLE IF NOT EXISTS quorum.archetypes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    cluster VARCHAR(50) NOT NULL,
    corpus_size_gb DECIMAL(10,2),
    temperature DECIMAL(3,2),
    style TEXT,
    domains TEXT[],
    sources TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge chunks with vector embeddings
CREATE TABLE IF NOT EXISTS quorum.chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    source VARCHAR(500),
    archetype_id INTEGER REFERENCES quorum.archetypes(id),
    document_id UUID,
    chunk_index INTEGER,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    compressed_data BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS quorum.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    source VARCHAR(500),
    archetype_id INTEGER REFERENCES quorum.archetypes(id),
    file_path VARCHAR(1000),
    size_bytes BIGINT,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query cache
CREATE TABLE IF NOT EXISTS quorum.query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    response TEXT,
    compressed_response BYTEA,
    quality_score DECIMAL(5,4),
    archetypes_used TEXT[],
    latency_ms INTEGER,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions
CREATE TABLE IF NOT EXISTS quorum.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_key VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    state JSONB DEFAULT '{}',
    compressed_state BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Metrics
CREATE TABLE IF NOT EXISTS quorum.metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,6),
    labels JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Graph edges (Apache AGE compatible)
CREATE TABLE IF NOT EXISTS quorum.graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    edge_type VARCHAR(100) NOT NULL,
    weight DECIMAL(10,6) DEFAULT 1.0,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Graph nodes
CREATE TABLE IF NOT EXISTS quorum.graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(100) NOT NULL,
    label VARCHAR(500),
    properties JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tribunal verdicts
CREATE TABLE IF NOT EXISTS quorum.tribunal_verdicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_text TEXT NOT NULL,
    philosopher_votes JSONB NOT NULL,
    final_verdict VARCHAR(50),
    confidence_score DECIMAL(5,4),
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compression stats
CREATE TABLE IF NOT EXISTS quorum.compression_stats (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL,
    original_size_bytes BIGINT,
    compressed_size_bytes BIGINT,
    compression_ratio DECIMAL(5,4),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Synergy clusters table for graph analysis
CREATE TABLE IF NOT EXISTS quorum.synergy_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name VARCHAR(200) NOT NULL,
    node_ids UUID[] NOT NULL,
    synergy_score DECIMAL(10,6),
    burst_potential DECIMAL(10,6),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Code analysis results
CREATE TABLE IF NOT EXISTS quorum.code_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path VARCHAR(500) NOT NULL,
    module_name VARCHAR(200),
    functions TEXT[],
    classes TEXT[],
    imports TEXT[],
    complexity_score DECIMAL(10,4),
    synergy_connections JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

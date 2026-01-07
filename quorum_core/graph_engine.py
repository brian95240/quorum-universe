#!/usr/bin/env python3
"""
Quorum Universe - Hyper-Optimized Graph Engine
NetworkX + PostgreSQL/pgvector for Apache AGE-style graph operations
Maximum async parallelism with cascading workflows
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
import numpy as np

import networkx as nx
import asyncpg

from config import NEON_CONNECTION_STRING, ARCHETYPES, TOTAL_ARCHETYPES

# =============================================================================
# GRAPH NODE AND EDGE TYPES
# =============================================================================
class NodeType(Enum):
    ARCHETYPE = "archetype"
    CONCEPT = "concept"
    DOCUMENT = "document"
    CHUNK = "chunk"
    QUERY = "query"
    SYNERGY = "synergy"
    CLUSTER = "cluster"

class EdgeType(Enum):
    BELONGS_TO = "belongs_to"
    REFERENCES = "references"
    SIMILAR_TO = "similar_to"
    SYNERGY = "synergy"
    DERIVED_FROM = "derived_from"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"

@dataclass
class GraphNode:
    """Node in the knowledge graph"""
    id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'node_type': self.node_type.value,
            'label': self.label,
            'properties': self.properties,
        }

@dataclass
class GraphEdge:
    """Edge in the knowledge graph"""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'edge_type': self.edge_type.value,
            'weight': self.weight,
            'properties': self.properties,
        }

# =============================================================================
# SYNERGY DETECTION RESULTS
# =============================================================================
@dataclass
class SynergyCluster:
    """Represents a discovered synergy cluster"""
    id: str
    name: str
    nodes: List[str]
    synergy_score: float
    burst_potential: float
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'nodes': self.nodes,
            'synergy_score': self.synergy_score,
            'burst_potential': self.burst_potential,
            'properties': self.properties,
        }

@dataclass
class SynergyAnalysisResult:
    """Complete synergy analysis result"""
    clusters: List[SynergyCluster]
    hidden_connections: List[Dict]
    optimization_opportunities: List[Dict]
    total_synergy_score: float
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)

# =============================================================================
# HYPER-OPTIMIZED GRAPH ENGINE
# =============================================================================
class QuorumGraphEngine:
    """
    Hyper-optimized graph engine combining NetworkX with PostgreSQL/pgvector
    Implements Apache AGE-style graph operations with maximum async parallelism
    """
    
    def __init__(self):
        self.nx_graph = nx.DiGraph()
        self.db_pool: Optional[asyncpg.Pool] = None
        self._node_cache: Dict[str, GraphNode] = {}
        self._edge_cache: Dict[str, GraphEdge] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._synergy_cache: Dict[str, SynergyCluster] = {}
        
        # Initialize archetype nodes
        self._init_archetype_nodes()
    
    def _init_archetype_nodes(self):
        """Initialize nodes for all 26 archetypes"""
        for archetype_name, archetype_config in ARCHETYPES.items():
            node_id = f"archetype:{archetype_name}"
            node = GraphNode(
                id=node_id,
                node_type=NodeType.ARCHETYPE,
                label=archetype_name,
                properties={
                    'cluster': archetype_config['cluster'],
                    'corpus_size_gb': archetype_config['corpus_size_gb'],
                    'temperature': archetype_config['temperature'],
                    'domains': archetype_config['domains'],
                }
            )
            self._node_cache[node_id] = node
            self.nx_graph.add_node(node_id, **node.to_dict())
        
        # Add cluster edges between archetypes in same cluster
        clusters = defaultdict(list)
        for name, config in ARCHETYPES.items():
            clusters[config['cluster']].append(f"archetype:{name}")
        
        for cluster_name, archetype_ids in clusters.items():
            for i, src in enumerate(archetype_ids):
                for tgt in archetype_ids[i+1:]:
                    self.nx_graph.add_edge(
                        src, tgt,
                        edge_type=EdgeType.SIMILAR_TO.value,
                        weight=0.8,
                        properties={'cluster': cluster_name}
                    )
    
    async def connect(self) -> asyncpg.Pool:
        """Establish database connection pool"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                NEON_CONNECTION_STRING,
                min_size=2,
                max_size=20,
                command_timeout=60,
            )
        return self.db_pool
    
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
    
    # =========================================================================
    # NODE OPERATIONS (Async Parallel)
    # =========================================================================
    async def add_node(self, node: GraphNode) -> str:
        """Add a node to the graph (both NetworkX and PostgreSQL)"""
        # Add to NetworkX
        self.nx_graph.add_node(node.id, **node.to_dict())
        self._node_cache[node.id] = node
        
        # Add to PostgreSQL
        pool = await self.connect()
        async with pool.acquire() as conn:
            embedding_list = node.embedding.tolist() if node.embedding is not None else None
            await conn.execute("""
                INSERT INTO quorum.graph_nodes (id, node_type, label, properties, embedding)
                VALUES ($1::uuid, $2, $3, $4, $5::vector)
                ON CONFLICT (id) DO UPDATE SET
                    properties = $4,
                    embedding = $5::vector
            """, node.id if '-' in node.id else None, 
                node.node_type.value, 
                node.label,
                json.dumps(node.properties),
                str(embedding_list) if embedding_list else None)
        
        return node.id
    
    async def add_nodes_batch(self, nodes: List[GraphNode]) -> List[str]:
        """Add multiple nodes in parallel batch"""
        # Add to NetworkX
        for node in nodes:
            self.nx_graph.add_node(node.id, **node.to_dict())
            self._node_cache[node.id] = node
        
        # Batch insert to PostgreSQL
        pool = await self.connect()
        async with pool.acquire() as conn:
            # Prepare batch data
            records = []
            for node in nodes:
                embedding_list = node.embedding.tolist() if node.embedding is not None else None
                records.append((
                    node.node_type.value,
                    node.label,
                    json.dumps(node.properties),
                    str(embedding_list) if embedding_list else None
                ))
            
            await conn.executemany("""
                INSERT INTO quorum.graph_nodes (node_type, label, properties, embedding)
                VALUES ($1, $2, $3, $4::vector)
            """, records)
        
        return [n.id for n in nodes]
    
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        if node_id in self._node_cache:
            return self._node_cache[node_id]
        
        pool = await self.connect()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, node_type, label, properties, embedding
                FROM quorum.graph_nodes
                WHERE id = $1::uuid OR label = $1
            """, node_id)
            
            if row:
                node = GraphNode(
                    id=str(row['id']),
                    node_type=NodeType(row['node_type']),
                    label=row['label'],
                    properties=json.loads(row['properties']) if row['properties'] else {},
                )
                self._node_cache[node.id] = node
                return node
        
        return None
    
    # =========================================================================
    # EDGE OPERATIONS (Async Parallel)
    # =========================================================================
    async def add_edge(self, edge: GraphEdge) -> str:
        """Add an edge to the graph"""
        edge_id = f"{edge.source_id}->{edge.target_id}:{edge.edge_type.value}"
        
        # Add to NetworkX
        self.nx_graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type.value,
            weight=edge.weight,
            properties=edge.properties
        )
        self._edge_cache[edge_id] = edge
        
        # Add to PostgreSQL
        pool = await self.connect()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO quorum.graph_edges (source_id, target_id, edge_type, weight, properties)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5)
            """, edge.source_id if '-' in edge.source_id else None,
                edge.target_id if '-' in edge.target_id else None,
                edge.edge_type.value,
                edge.weight,
                json.dumps(edge.properties))
        
        return edge_id
    
    async def add_edges_batch(self, edges: List[GraphEdge]) -> List[str]:
        """Add multiple edges in parallel batch"""
        edge_ids = []
        
        for edge in edges:
            edge_id = f"{edge.source_id}->{edge.target_id}:{edge.edge_type.value}"
            edge_ids.append(edge_id)
            
            self.nx_graph.add_edge(
                edge.source_id,
                edge.target_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight,
                properties=edge.properties
            )
            self._edge_cache[edge_id] = edge
        
        # Batch insert to PostgreSQL
        pool = await self.connect()
        async with pool.acquire() as conn:
            records = [
                (edge.edge_type.value, edge.weight, json.dumps(edge.properties))
                for edge in edges
            ]
            await conn.executemany("""
                INSERT INTO quorum.graph_edges (edge_type, weight, properties)
                VALUES ($1, $2, $3)
            """, records)
        
        return edge_ids
    
    # =========================================================================
    # SYNERGY DETECTION (Hidden Connection Discovery)
    # =========================================================================
    async def detect_synergies(self, min_synergy_score: float = 0.5) -> SynergyAnalysisResult:
        """
        Detect hidden synergies and burst clusters in the graph
        Uses multiple algorithms for comprehensive analysis
        """
        start_time = time.time()
        
        # Run synergy detection algorithms in parallel
        results = await asyncio.gather(
            self._detect_community_synergies(),
            self._detect_bridge_synergies(),
            self._detect_embedding_synergies(),
            self._detect_cross_cluster_synergies(),
        )
        
        community_clusters, bridge_connections, embedding_clusters, cross_cluster = results
        
        # Merge and deduplicate clusters
        all_clusters = []
        seen_node_sets = set()
        
        for cluster in community_clusters + embedding_clusters:
            node_set = frozenset(cluster.nodes)
            if node_set not in seen_node_sets and cluster.synergy_score >= min_synergy_score:
                seen_node_sets.add(node_set)
                all_clusters.append(cluster)
        
        # Calculate burst potential for each cluster
        for cluster in all_clusters:
            cluster.burst_potential = self._calculate_burst_potential(cluster)
        
        # Sort by synergy score
        all_clusters.sort(key=lambda c: c.synergy_score, reverse=True)
        
        # Identify optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(
            all_clusters, bridge_connections, cross_cluster
        )
        
        total_synergy = sum(c.synergy_score for c in all_clusters) / max(len(all_clusters), 1)
        
        analysis_time = time.time() - start_time
        
        return SynergyAnalysisResult(
            clusters=all_clusters,
            hidden_connections=bridge_connections + cross_cluster,
            optimization_opportunities=optimization_opportunities,
            total_synergy_score=total_synergy,
        )
    
    async def _detect_community_synergies(self) -> List[SynergyCluster]:
        """Detect synergies using community detection algorithms"""
        clusters = []
        
        # Use Louvain community detection
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(self.nx_graph.to_undirected())
            
            for i, community in enumerate(communities):
                if len(community) >= 2:
                    # Calculate internal density
                    subgraph = self.nx_graph.subgraph(community)
                    density = nx.density(subgraph)
                    
                    cluster = SynergyCluster(
                        id=f"community_{i}",
                        name=f"Community Cluster {i}",
                        nodes=list(community),
                        synergy_score=density,
                        burst_potential=0.0,
                        properties={
                            'detection_method': 'louvain',
                            'size': len(community),
                        }
                    )
                    clusters.append(cluster)
        except Exception as e:
            print(f"Community detection error: {e}")
        
        return clusters
    
    async def _detect_bridge_synergies(self) -> List[Dict]:
        """Detect bridge nodes that connect disparate clusters"""
        bridges = []
        
        try:
            # Find articulation points (bridge nodes)
            undirected = self.nx_graph.to_undirected()
            articulation_points = list(nx.articulation_points(undirected))
            
            for node in articulation_points:
                neighbors = list(self.nx_graph.neighbors(node))
                
                bridges.append({
                    'type': 'bridge_node',
                    'node': node,
                    'connections': len(neighbors),
                    'neighbors': neighbors[:10],  # Limit for performance
                    'synergy_potential': len(neighbors) / max(self.nx_graph.number_of_nodes(), 1),
                })
        except Exception as e:
            print(f"Bridge detection error: {e}")
        
        return bridges
    
    async def _detect_embedding_synergies(self) -> List[SynergyCluster]:
        """Detect synergies based on embedding similarity"""
        clusters = []
        
        # Get nodes with embeddings
        nodes_with_embeddings = [
            (node_id, node.embedding)
            for node_id, node in self._node_cache.items()
            if node.embedding is not None
        ]
        
        if len(nodes_with_embeddings) < 2:
            return clusters
        
        # Calculate pairwise similarities
        node_ids = [n[0] for n in nodes_with_embeddings]
        embeddings = np.array([n[1] for n in nodes_with_embeddings])
        
        # Cosine similarity matrix
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-10)
        similarity_matrix = np.dot(normalized, normalized.T)
        
        # Find high-similarity clusters
        threshold = 0.8
        for i in range(len(node_ids)):
            similar_indices = np.where(similarity_matrix[i] > threshold)[0]
            if len(similar_indices) >= 2:
                similar_nodes = [node_ids[j] for j in similar_indices]
                avg_similarity = np.mean(similarity_matrix[i][similar_indices])
                
                cluster = SynergyCluster(
                    id=f"embedding_{i}",
                    name=f"Embedding Cluster {i}",
                    nodes=similar_nodes,
                    synergy_score=float(avg_similarity),
                    burst_potential=0.0,
                    properties={
                        'detection_method': 'embedding_similarity',
                        'threshold': threshold,
                    }
                )
                clusters.append(cluster)
        
        return clusters
    
    async def _detect_cross_cluster_synergies(self) -> List[Dict]:
        """Detect synergies across archetype clusters"""
        cross_synergies = []
        
        # Group archetypes by cluster
        cluster_archetypes = defaultdict(list)
        for name, config in ARCHETYPES.items():
            cluster_archetypes[config['cluster']].append(name)
        
        # Find cross-cluster connections
        cluster_names = list(cluster_archetypes.keys())
        for i, cluster1 in enumerate(cluster_names):
            for cluster2 in cluster_names[i+1:]:
                # Check for edges between clusters
                edges_between = 0
                for arch1 in cluster_archetypes[cluster1]:
                    for arch2 in cluster_archetypes[cluster2]:
                        node1 = f"archetype:{arch1}"
                        node2 = f"archetype:{arch2}"
                        if self.nx_graph.has_edge(node1, node2) or self.nx_graph.has_edge(node2, node1):
                            edges_between += 1
                
                if edges_between > 0:
                    cross_synergies.append({
                        'type': 'cross_cluster',
                        'cluster1': cluster1,
                        'cluster2': cluster2,
                        'connection_strength': edges_between,
                        'archetypes1': cluster_archetypes[cluster1],
                        'archetypes2': cluster_archetypes[cluster2],
                    })
        
        return cross_synergies
    
    def _calculate_burst_potential(self, cluster: SynergyCluster) -> float:
        """Calculate the burst potential of a synergy cluster"""
        if len(cluster.nodes) < 2:
            return 0.0
        
        # Factors for burst potential:
        # 1. Cluster density
        # 2. External connections
        # 3. Node importance (PageRank)
        
        subgraph = self.nx_graph.subgraph(cluster.nodes)
        density = nx.density(subgraph)
        
        # External connections
        external_edges = 0
        for node in cluster.nodes:
            for neighbor in self.nx_graph.neighbors(node):
                if neighbor not in cluster.nodes:
                    external_edges += 1
        
        external_ratio = external_edges / max(len(cluster.nodes), 1)
        
        # PageRank of cluster nodes
        try:
            pagerank = nx.pagerank(self.nx_graph)
            cluster_pagerank = sum(pagerank.get(n, 0) for n in cluster.nodes)
        except:
            cluster_pagerank = 0.1
        
        burst_potential = (density * 0.4 + external_ratio * 0.3 + cluster_pagerank * 0.3)
        return min(burst_potential, 1.0)
    
    def _identify_optimization_opportunities(
        self,
        clusters: List[SynergyCluster],
        bridges: List[Dict],
        cross_cluster: List[Dict]
    ) -> List[Dict]:
        """Identify optimization opportunities from synergy analysis"""
        opportunities = []
        
        # High-synergy clusters that could be merged
        for i, cluster1 in enumerate(clusters):
            for cluster2 in clusters[i+1:]:
                overlap = set(cluster1.nodes) & set(cluster2.nodes)
                if len(overlap) > 0:
                    opportunities.append({
                        'type': 'cluster_merge',
                        'clusters': [cluster1.id, cluster2.id],
                        'overlap_nodes': list(overlap),
                        'potential_gain': (cluster1.synergy_score + cluster2.synergy_score) / 2,
                    })
        
        # Bridge nodes that could be strengthened
        for bridge in bridges:
            if bridge['synergy_potential'] > 0.3:
                opportunities.append({
                    'type': 'bridge_strengthening',
                    'node': bridge['node'],
                    'current_connections': bridge['connections'],
                    'potential_gain': bridge['synergy_potential'],
                })
        
        # Cross-cluster connections that could be enhanced
        for cross in cross_cluster:
            if cross['connection_strength'] < 3:
                opportunities.append({
                    'type': 'cross_cluster_enhancement',
                    'clusters': [cross['cluster1'], cross['cluster2']],
                    'current_strength': cross['connection_strength'],
                    'potential_gain': 0.5,
                })
        
        return opportunities
    
    # =========================================================================
    # GRAPH QUERIES (Async)
    # =========================================================================
    async def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two nodes"""
        try:
            return nx.shortest_path(self.nx_graph, source, target)
        except nx.NetworkXNoPath:
            return None
    
    async def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]:
        """Get neighbors up to specified depth"""
        if depth == 1:
            return list(self.nx_graph.neighbors(node_id))
        
        neighbors = set()
        current_level = {node_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.nx_graph.neighbors(node))
            neighbors.update(next_level)
            current_level = next_level
        
        neighbors.discard(node_id)
        return list(neighbors)
    
    async def semantic_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        node_type: Optional[NodeType] = None
    ) -> List[Tuple[str, float]]:
        """Search for similar nodes by embedding"""
        pool = await self.connect()
        
        async with pool.acquire() as conn:
            embedding_str = str(query_embedding.tolist())
            
            if node_type:
                rows = await conn.fetch("""
                    SELECT id, label, 1 - (embedding <=> $1::vector) as similarity
                    FROM quorum.graph_nodes
                    WHERE node_type = $2 AND embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                """, embedding_str, node_type.value, top_k)
            else:
                rows = await conn.fetch("""
                    SELECT id, label, 1 - (embedding <=> $1::vector) as similarity
                    FROM quorum.graph_nodes
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                """, embedding_str, top_k)
            
            return [(str(row['id']), float(row['similarity'])) for row in rows]
    
    async def get_graph_stats(self) -> Dict:
        """Get comprehensive graph statistics"""
        stats = {
            'nodes': self.nx_graph.number_of_nodes(),
            'edges': self.nx_graph.number_of_edges(),
            'density': nx.density(self.nx_graph),
            'is_connected': nx.is_weakly_connected(self.nx_graph),
        }
        
        # Node type distribution
        node_types = defaultdict(int)
        for node_id, data in self.nx_graph.nodes(data=True):
            node_types[data.get('node_type', 'unknown')] += 1
        stats['node_types'] = dict(node_types)
        
        # Edge type distribution
        edge_types = defaultdict(int)
        for _, _, data in self.nx_graph.edges(data=True):
            edge_types[data.get('edge_type', 'unknown')] += 1
        stats['edge_types'] = dict(edge_types)
        
        # Centrality metrics (sample for performance)
        if self.nx_graph.number_of_nodes() <= 1000:
            try:
                pagerank = nx.pagerank(self.nx_graph)
                top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
                stats['top_pagerank_nodes'] = top_nodes
            except:
                pass
        
        return stats
    
    async def export_to_json(self) -> Dict:
        """Export graph to JSON format"""
        return {
            'nodes': [
                {**data, 'id': node_id}
                for node_id, data in self.nx_graph.nodes(data=True)
            ],
            'edges': [
                {**data, 'source': src, 'target': tgt}
                for src, tgt, data in self.nx_graph.edges(data=True)
            ],
            'stats': await self.get_graph_stats(),
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
async def create_graph_engine() -> QuorumGraphEngine:
    """Create and initialize graph engine"""
    engine = QuorumGraphEngine()
    await engine.connect()
    return engine


if __name__ == "__main__":
    async def test():
        engine = QuorumGraphEngine()
        print(f"Graph initialized with {engine.nx_graph.number_of_nodes()} archetype nodes")
        
        stats = await engine.get_graph_stats()
        print(f"\nGraph Stats:")
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Edges: {stats['edges']}")
        print(f"  Density: {stats['density']:.4f}")
        
        # Test synergy detection
        print("\nRunning synergy detection...")
        synergies = await engine.detect_synergies(min_synergy_score=0.3)
        print(f"  Found {len(synergies.clusters)} synergy clusters")
        print(f"  Hidden connections: {len(synergies.hidden_connections)}")
        print(f"  Optimization opportunities: {len(synergies.optimization_opportunities)}")
        
        await engine.close()
    
    asyncio.run(test())

#!/usr/bin/env python3
"""
Quorum Universe - Synergy Analyzer
Discovers hidden synergies, burst clusters, and optimization opportunities
Uses graph analysis to extract maximum technical potential
"""

import asyncio
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import sys
sys.path.insert(0, '/home/ubuntu/quorum_universe/quorum_core')

import networkx as nx
import numpy as np

from config import ARCHETYPES, NEON_CONNECTION_STRING, TOTAL_ARCHETYPES
from graph_engine import QuorumGraphEngine, NodeType, EdgeType, SynergyCluster

# =============================================================================
# SYNERGY ANALYSIS RESULTS
# =============================================================================
@dataclass
class OptimizationOpportunity:
    """Represents an optimization opportunity"""
    id: str
    category: str
    description: str
    impact_score: float
    effort_score: float
    roi_score: float
    affected_components: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'category': self.category,
            'description': self.description,
            'impact_score': self.impact_score,
            'effort_score': self.effort_score,
            'roi_score': self.roi_score,
            'affected_components': self.affected_components,
            'recommendations': self.recommendations,
        }

@dataclass
class SynergyBurst:
    """Represents a synergy burst cluster"""
    id: str
    name: str
    nodes: List[str]
    burst_score: float
    activation_threshold: float
    cascade_potential: float
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'nodes': self.nodes,
            'burst_score': self.burst_score,
            'activation_threshold': self.activation_threshold,
            'cascade_potential': self.cascade_potential,
            'properties': self.properties,
        }

@dataclass
class ComprehensiveSynergyReport:
    """Complete synergy analysis report"""
    # Clusters
    synergy_clusters: List[SynergyCluster]
    burst_clusters: List[SynergyBurst]
    
    # Connections
    hidden_connections: List[Dict]
    cross_domain_bridges: List[Dict]
    
    # Optimization
    optimization_opportunities: List[OptimizationOpportunity]
    
    # Metrics
    total_synergy_score: float
    network_efficiency: float
    cascade_potential: float
    
    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    analysis_duration_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'synergy_clusters': [c.to_dict() for c in self.synergy_clusters],
            'burst_clusters': [b.to_dict() for b in self.burst_clusters],
            'hidden_connections': self.hidden_connections,
            'cross_domain_bridges': self.cross_domain_bridges,
            'optimization_opportunities': [o.to_dict() for o in self.optimization_opportunities],
            'metrics': {
                'total_synergy_score': self.total_synergy_score,
                'network_efficiency': self.network_efficiency,
                'cascade_potential': self.cascade_potential,
            },
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'analysis_duration_ms': self.analysis_duration_ms,
        }

# =============================================================================
# SYNERGY ANALYZER
# =============================================================================
class SynergyAnalyzer:
    """
    Comprehensive synergy analyzer for Quorum Universe
    Discovers hidden connections, burst clusters, and optimization opportunities
    """
    
    def __init__(self, graph_engine: QuorumGraphEngine = None):
        self.graph_engine = graph_engine or QuorumGraphEngine()
        self.code_graph = nx.DiGraph()  # For code analysis
        self._build_code_graph()
    
    async def build_graph(self):
        """Build the knowledge graph from archetypes"""
        # Initialize graph engine if it has initialize method
        if hasattr(self.graph_engine, 'initialize'):
            await self.graph_engine.initialize()
        return True
    
    async def find_synergy_clusters(self) -> List[Dict]:
        """Find synergy clusters in the graph"""
        clusters = await self._analyze_archetype_synergies()
        return [c.to_dict() for c in clusters]
    
    async def find_burst_clusters(self) -> List[Dict]:
        """Find burst clusters in the graph"""
        bursts = await self._analyze_burst_clusters()
        return [b.to_dict() for b in bursts]
    
    async def find_hidden_connections(self) -> List[Dict]:
        """Find hidden connections in the graph"""
        return await self._analyze_hidden_connections()
    
    def _build_code_graph(self):
        """Build graph from code structure"""
        # Add module nodes
        modules = [
            ('config', {'type': 'module', 'lines': 400, 'functions': 5}),
            ('symbiotic_connector', {'type': 'module', 'lines': 450, 'functions': 15}),
            ('graph_engine', {'type': 'module', 'lines': 500, 'functions': 20}),
            ('api_server', {'type': 'module', 'lines': 400, 'functions': 25}),
            ('closed_loop_test', {'type': 'module', 'lines': 350, 'functions': 15}),
        ]
        
        for module_name, attrs in modules:
            self.code_graph.add_node(f"module:{module_name}", **attrs)
        
        # Add dependencies
        dependencies = [
            ('api_server', 'config'),
            ('api_server', 'symbiotic_connector'),
            ('api_server', 'graph_engine'),
            ('symbiotic_connector', 'config'),
            ('graph_engine', 'config'),
            ('closed_loop_test', 'config'),
            ('closed_loop_test', 'graph_engine'),
            ('closed_loop_test', 'symbiotic_connector'),
        ]
        
        for src, tgt in dependencies:
            self.code_graph.add_edge(f"module:{src}", f"module:{tgt}", type='imports')
    
    async def analyze_comprehensive(self) -> ComprehensiveSynergyReport:
        """Run comprehensive synergy analysis"""
        start_time = time.time()
        
        # Run all analyses in parallel
        results = await asyncio.gather(
            self._analyze_archetype_synergies(),
            self._analyze_burst_clusters(),
            self._analyze_hidden_connections(),
            self._analyze_cross_domain_bridges(),
            self._analyze_optimization_opportunities(),
            self._calculate_network_metrics(),
        )
        
        (
            synergy_clusters,
            burst_clusters,
            hidden_connections,
            cross_domain_bridges,
            optimization_opportunities,
            network_metrics,
        ) = results
        
        duration_ms = (time.time() - start_time) * 1000
        
        return ComprehensiveSynergyReport(
            synergy_clusters=synergy_clusters,
            burst_clusters=burst_clusters,
            hidden_connections=hidden_connections,
            cross_domain_bridges=cross_domain_bridges,
            optimization_opportunities=optimization_opportunities,
            total_synergy_score=network_metrics['total_synergy'],
            network_efficiency=network_metrics['efficiency'],
            cascade_potential=network_metrics['cascade_potential'],
            analysis_duration_ms=duration_ms,
        )
    
    async def _analyze_archetype_synergies(self) -> List[SynergyCluster]:
        """Analyze synergies between archetypes"""
        clusters = []
        
        # Group archetypes by cluster
        cluster_groups = defaultdict(list)
        for name, config in ARCHETYPES.items():
            cluster_groups[config['cluster']].append(name)
        
        # Create synergy clusters for each group
        for cluster_name, archetypes in cluster_groups.items():
            if len(archetypes) >= 2:
                # Calculate synergy score based on domain overlap
                domain_sets = [set(ARCHETYPES[a]['domains']) for a in archetypes]
                
                # Calculate pairwise overlaps
                total_overlap = 0
                pairs = 0
                for i, d1 in enumerate(domain_sets):
                    for d2 in domain_sets[i+1:]:
                        overlap = len(d1 & d2) / max(len(d1 | d2), 1)
                        total_overlap += overlap
                        pairs += 1
                
                avg_overlap = total_overlap / max(pairs, 1)
                synergy_score = 0.5 + (avg_overlap * 0.5)  # Base 0.5 + overlap bonus
                
                cluster = SynergyCluster(
                    id=f"archetype_cluster_{cluster_name}",
                    name=f"{cluster_name.replace('_', ' ').title()} Cluster",
                    nodes=[f"archetype:{a}" for a in archetypes],
                    synergy_score=synergy_score,
                    burst_potential=self._calculate_burst_potential_for_archetypes(archetypes),
                    properties={
                        'cluster_type': cluster_name,
                        'archetype_count': len(archetypes),
                        'domain_overlap': avg_overlap,
                    }
                )
                clusters.append(cluster)
        
        # Find cross-cluster synergies
        cross_cluster_synergies = await self._find_cross_cluster_synergies()
        clusters.extend(cross_cluster_synergies)
        
        # Sort by synergy score
        clusters.sort(key=lambda c: c.synergy_score, reverse=True)
        
        return clusters
    
    def _calculate_burst_potential_for_archetypes(self, archetypes: List[str]) -> float:
        """Calculate burst potential for a group of archetypes"""
        # Factors: corpus size, temperature variance, domain diversity
        corpus_sizes = [ARCHETYPES[a]['corpus_size_gb'] for a in archetypes]
        temperatures = [ARCHETYPES[a]['temperature'] for a in archetypes]
        
        all_domains = set()
        for a in archetypes:
            all_domains.update(ARCHETYPES[a]['domains'])
        
        # Normalize factors
        corpus_factor = min(sum(corpus_sizes) / 500, 1.0)  # Cap at 500GB
        temp_variance = np.std(temperatures) if len(temperatures) > 1 else 0
        domain_diversity = len(all_domains) / 20  # Normalize by max expected domains
        
        burst_potential = (corpus_factor * 0.4 + temp_variance * 0.2 + domain_diversity * 0.4)
        return min(burst_potential, 1.0)
    
    async def _find_cross_cluster_synergies(self) -> List[SynergyCluster]:
        """Find synergies across different archetype clusters"""
        cross_synergies = []
        
        # Define known cross-cluster synergy patterns
        synergy_patterns = [
            {
                'name': 'AI-Neuroscience Bridge',
                'archetypes': ['stanford_cs', 'neuroscience_cognitive', 'ai_safety'],
                'synergy_type': 'technical_convergence',
            },
            {
                'name': 'Quantum-Physics Nexus',
                'archetypes': ['caltech_physics', 'quantum_computing', 'princeton_math'],
                'synergy_type': 'theoretical_foundation',
            },
            {
                'name': 'Systems Biology Hub',
                'archetypes': ['broad_genomics', 'systems_biology', 'longevity_research', 'harvard_med'],
                'synergy_type': 'life_sciences_integration',
            },
            {
                'name': 'Complexity-Climate Network',
                'archetypes': ['complexity_science', 'climate_earth_systems', 'indigenous_ecology'],
                'synergy_type': 'systems_thinking',
            },
            {
                'name': 'Philosophy-AI Ethics Tribunal',
                'archetypes': ['philosophy_tribunal', 'ai_safety', 'oxford_classics'],
                'synergy_type': 'ethical_reasoning',
            },
            {
                'name': 'Eastern-Western Wisdom Bridge',
                'archetypes': ['beijing_classical', 'nalanda_vedic', 'baghdad_golden', 'oxford_classics'],
                'synergy_type': 'cross_cultural_synthesis',
            },
            {
                'name': 'Robotics-Engineering Fusion',
                'archetypes': ['robotics_embodied_ai', 'mit_engineering', 'stanford_cs'],
                'synergy_type': 'applied_technology',
            },
            {
                'name': 'Creative-Design Synthesis',
                'archetypes': ['bauhaus_design', 'hacker_insurgent', 'mensa_orthogonal'],
                'synergy_type': 'creative_innovation',
            },
        ]
        
        for pattern in synergy_patterns:
            # Calculate synergy score
            domains = set()
            corpus_total = 0
            for arch in pattern['archetypes']:
                if arch in ARCHETYPES:
                    domains.update(ARCHETYPES[arch]['domains'])
                    corpus_total += ARCHETYPES[arch]['corpus_size_gb']
            
            synergy_score = min(len(domains) / 15, 1.0) * 0.6 + min(corpus_total / 200, 1.0) * 0.4
            
            cluster = SynergyCluster(
                id=f"cross_cluster_{pattern['synergy_type']}",
                name=pattern['name'],
                nodes=[f"archetype:{a}" for a in pattern['archetypes'] if a in ARCHETYPES],
                synergy_score=synergy_score,
                burst_potential=self._calculate_burst_potential_for_archetypes(
                    [a for a in pattern['archetypes'] if a in ARCHETYPES]
                ),
                properties={
                    'synergy_type': pattern['synergy_type'],
                    'domain_count': len(domains),
                    'corpus_total_gb': corpus_total,
                }
            )
            cross_synergies.append(cluster)
        
        return cross_synergies
    
    async def _analyze_burst_clusters(self) -> List[SynergyBurst]:
        """Identify burst clusters with high cascade potential"""
        bursts = []
        
        # Analyze code module dependencies for burst potential
        for node in self.code_graph.nodes():
            if self.code_graph.out_degree(node) >= 2:
                dependents = list(self.code_graph.successors(node))
                
                # Calculate burst score
                burst_score = self.code_graph.out_degree(node) / max(self.code_graph.number_of_nodes(), 1)
                
                # Calculate cascade potential
                cascade_depth = self._calculate_cascade_depth(node)
                cascade_potential = cascade_depth / 5  # Normalize by max expected depth
                
                burst = SynergyBurst(
                    id=f"burst_{node.replace(':', '_')}",
                    name=f"{node.split(':')[1].replace('_', ' ').title()} Burst Point",
                    nodes=[node] + dependents,
                    burst_score=burst_score,
                    activation_threshold=0.5,
                    cascade_potential=cascade_potential,
                    properties={
                        'type': 'code_module',
                        'dependents': len(dependents),
                        'cascade_depth': cascade_depth,
                    }
                )
                bursts.append(burst)
        
        # Analyze archetype clusters for burst potential
        cluster_groups = defaultdict(list)
        for name, config in ARCHETYPES.items():
            cluster_groups[config['cluster']].append(name)
        
        for cluster_name, archetypes in cluster_groups.items():
            if len(archetypes) >= 3:
                burst_score = len(archetypes) / TOTAL_ARCHETYPES
                cascade_potential = sum(ARCHETYPES[a]['corpus_size_gb'] for a in archetypes) / 500
                
                burst = SynergyBurst(
                    id=f"burst_cluster_{cluster_name}",
                    name=f"{cluster_name.replace('_', ' ').title()} Burst Cluster",
                    nodes=[f"archetype:{a}" for a in archetypes],
                    burst_score=burst_score,
                    activation_threshold=0.6,
                    cascade_potential=min(cascade_potential, 1.0),
                    properties={
                        'type': 'archetype_cluster',
                        'archetype_count': len(archetypes),
                    }
                )
                bursts.append(burst)
        
        # Sort by burst score
        bursts.sort(key=lambda b: b.burst_score, reverse=True)
        
        return bursts
    
    def _calculate_cascade_depth(self, node: str) -> int:
        """Calculate cascade depth from a node"""
        visited = set()
        depth = 0
        current_level = {node}
        
        while current_level:
            visited.update(current_level)
            next_level = set()
            for n in current_level:
                for successor in self.code_graph.successors(n):
                    if successor not in visited:
                        next_level.add(successor)
            if next_level:
                depth += 1
            current_level = next_level
        
        return depth
    
    async def _analyze_hidden_connections(self) -> List[Dict]:
        """Discover hidden connections in the system"""
        hidden = []
        
        # Find archetypes with overlapping domains but different clusters
        for name1, config1 in ARCHETYPES.items():
            for name2, config2 in ARCHETYPES.items():
                if name1 >= name2:  # Avoid duplicates
                    continue
                
                if config1['cluster'] != config2['cluster']:
                    domain_overlap = set(config1['domains']) & set(config2['domains'])
                    if domain_overlap:
                        hidden.append({
                            'type': 'domain_overlap',
                            'source': name1,
                            'target': name2,
                            'overlapping_domains': list(domain_overlap),
                            'strength': len(domain_overlap) / max(len(config1['domains']), len(config2['domains'])),
                            'clusters': [config1['cluster'], config2['cluster']],
                        })
        
        # Find temperature-based connections (similar reasoning styles)
        temp_groups = defaultdict(list)
        for name, config in ARCHETYPES.items():
            temp_bucket = round(config['temperature'] * 10) / 10
            temp_groups[temp_bucket].append(name)
        
        for temp, archetypes in temp_groups.items():
            if len(archetypes) >= 2:
                hidden.append({
                    'type': 'temperature_affinity',
                    'temperature': temp,
                    'archetypes': archetypes,
                    'strength': 0.5 + (len(archetypes) / TOTAL_ARCHETYPES),
                    'description': f"Archetypes with similar reasoning temperature ({temp})",
                })
        
        # Sort by strength
        hidden.sort(key=lambda h: h.get('strength', 0), reverse=True)
        
        return hidden[:20]  # Top 20 hidden connections
    
    async def _analyze_cross_domain_bridges(self) -> List[Dict]:
        """Find cross-domain bridge archetypes"""
        bridges = []
        
        # Find archetypes that span multiple domain categories
        domain_categories = {
            'technical': ['engineering', 'computer_science', 'algorithms', 'robotics'],
            'scientific': ['physics', 'chemistry', 'biology', 'mathematics'],
            'life_sciences': ['medicine', 'genomics', 'neuroscience', 'longevity'],
            'humanities': ['philosophy', 'history', 'literature', 'classics'],
            'social': ['economics', 'law', 'policy', 'ethics'],
            'creative': ['design', 'art', 'architecture', 'aesthetics'],
        }
        
        for name, config in ARCHETYPES.items():
            categories_spanned = set()
            for category, domains in domain_categories.items():
                if any(d in config['domains'] for d in domains):
                    categories_spanned.add(category)
            
            if len(categories_spanned) >= 2:
                bridges.append({
                    'archetype': name,
                    'categories_spanned': list(categories_spanned),
                    'bridge_strength': len(categories_spanned) / len(domain_categories),
                    'domains': config['domains'],
                    'cluster': config['cluster'],
                })
        
        # Sort by bridge strength
        bridges.sort(key=lambda b: b['bridge_strength'], reverse=True)
        
        return bridges
    
    async def _analyze_optimization_opportunities(self) -> List[OptimizationOpportunity]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # 1. Cache optimization opportunities
        opportunities.append(OptimizationOpportunity(
            id='opt_cache_hierarchy',
            category='performance',
            description='Implement multi-tier cache hierarchy (L1/L2/L3) for archetype responses',
            impact_score=0.85,
            effort_score=0.6,
            roi_score=0.85 / 0.6,
            affected_components=['api_server', 'graph_engine', 'symbiotic_connector'],
            recommendations=[
                'Implement Redis L1 cache with 5-minute TTL for hot queries',
                'Add L2 warm cache with 1-hour TTL for frequent patterns',
                'Use L3 cold cache with 24-hour TTL for archetype embeddings',
            ]
        ))
        
        # 2. Async parallelism optimization
        opportunities.append(OptimizationOpportunity(
            id='opt_async_parallel',
            category='performance',
            description='Maximize async parallelism in archetype routing',
            impact_score=0.9,
            effort_score=0.5,
            roi_score=0.9 / 0.5,
            affected_components=['api_server', 'graph_engine'],
            recommendations=[
                'Use asyncio.gather() for parallel archetype queries',
                'Implement connection pooling for database access',
                'Add batch processing for bulk operations',
            ]
        ))
        
        # 3. Graph compression optimization
        opportunities.append(OptimizationOpportunity(
            id='opt_graph_compression',
            category='storage',
            description='Compress graph data using Zstandard for 70% size reduction',
            impact_score=0.7,
            effort_score=0.4,
            roi_score=0.7 / 0.4,
            affected_components=['graph_engine', 'symbiotic_connector'],
            recommendations=[
                'Apply Zstandard compression to graph serialization',
                'Use dictionary-based compression for repeated patterns',
                'Implement lazy loading for large graph segments',
            ]
        ))
        
        # 4. Synergy cascade optimization
        opportunities.append(OptimizationOpportunity(
            id='opt_synergy_cascade',
            category='intelligence',
            description='Leverage synergy clusters for cascading knowledge activation',
            impact_score=0.95,
            effort_score=0.7,
            roi_score=0.95 / 0.7,
            affected_components=['graph_engine', 'api_server'],
            recommendations=[
                'Pre-compute synergy clusters on startup',
                'Implement cascade activation for related archetypes',
                'Use burst detection for optimal query routing',
            ]
        ))
        
        # 5. Cross-platform sync optimization
        opportunities.append(OptimizationOpportunity(
            id='opt_cross_platform_sync',
            category='connectivity',
            description='Optimize cross-platform sync for PC/Mac/Raspberry Pi/mobile',
            impact_score=0.8,
            effort_score=0.65,
            roi_score=0.8 / 0.65,
            affected_components=['symbiotic_connector', 'api_server'],
            recommendations=[
                'Implement differential sync for large datasets',
                'Use WebSocket for real-time updates',
                'Add platform-specific optimizations',
            ]
        ))
        
        # 6. Embedding optimization
        opportunities.append(OptimizationOpportunity(
            id='opt_embeddings',
            category='intelligence',
            description='Optimize embedding storage and retrieval with pgvector',
            impact_score=0.85,
            effort_score=0.55,
            roi_score=0.85 / 0.55,
            affected_components=['graph_engine'],
            recommendations=[
                'Use HNSW index for fast similarity search',
                'Implement embedding quantization for storage efficiency',
                'Cache frequently accessed embeddings in Redis',
            ]
        ))
        
        # Sort by ROI score
        opportunities.sort(key=lambda o: o.roi_score, reverse=True)
        
        return opportunities
    
    async def _calculate_network_metrics(self) -> Dict[str, float]:
        """Calculate overall network metrics"""
        # Graph metrics
        nx_graph = self.graph_engine.nx_graph
        
        # Efficiency: ratio of actual to potential connections
        n = nx_graph.number_of_nodes()
        e = nx_graph.number_of_edges()
        max_edges = n * (n - 1)  # Directed graph
        efficiency = e / max(max_edges, 1)
        
        # Total synergy: based on cluster density
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(nx_graph.to_undirected())
            
            total_synergy = 0
            for community in communities:
                if len(community) >= 2:
                    subgraph = nx_graph.subgraph(community)
                    density = nx.density(subgraph)
                    total_synergy += density * len(community)
            
            total_synergy /= max(n, 1)
        except:
            total_synergy = efficiency
        
        # Cascade potential: based on average path length
        try:
            if nx.is_weakly_connected(nx_graph):
                avg_path = nx.average_shortest_path_length(nx_graph)
                cascade_potential = 1 / max(avg_path, 1)
            else:
                cascade_potential = 0.5
        except:
            cascade_potential = 0.5
        
        return {
            'efficiency': efficiency,
            'total_synergy': total_synergy,
            'cascade_potential': cascade_potential,
        }


# =============================================================================
# MAIN
# =============================================================================
async def run_synergy_analysis() -> ComprehensiveSynergyReport:
    """Run comprehensive synergy analysis"""
    print("=" * 60)
    print("QUORUM UNIVERSE - SYNERGY ANALYSIS")
    print("=" * 60)
    print(f"Started: {datetime.utcnow().isoformat()}")
    print()
    
    graph_engine = QuorumGraphEngine()
    await graph_engine.connect()
    
    analyzer = SynergyAnalyzer(graph_engine)
    report = await analyzer.analyze_comprehensive()
    
    await graph_engine.close()
    
    # Print summary
    print(f"\n{'='*60}")
    print("SYNERGY ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Synergy Clusters: {len(report.synergy_clusters)}")
    print(f"Burst Clusters: {len(report.burst_clusters)}")
    print(f"Hidden Connections: {len(report.hidden_connections)}")
    print(f"Cross-Domain Bridges: {len(report.cross_domain_bridges)}")
    print(f"Optimization Opportunities: {len(report.optimization_opportunities)}")
    print()
    print(f"Total Synergy Score: {report.total_synergy_score:.4f}")
    print(f"Network Efficiency: {report.network_efficiency:.4f}")
    print(f"Cascade Potential: {report.cascade_potential:.4f}")
    print()
    print(f"Analysis Duration: {report.analysis_duration_ms:.2f} ms")
    print(f"{'='*60}")
    
    return report


if __name__ == "__main__":
    report = asyncio.run(run_synergy_analysis())
    
    # Save report to file
    output_path = "/home/ubuntu/quorum_universe/synergy_report.json"
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nReport saved to: {output_path}")

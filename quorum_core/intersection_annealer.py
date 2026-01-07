#!/usr/bin/env python3
"""
Intersection Annealer for Hidden Synergy Network Discovery

After hexagonal ring rotation optimization, this module performs
simulated annealing at all code intersections to discover:

1. Hidden synergy networks lurking at module boundaries
2. Latent cluster formations at function intersections
3. Cross-domain bridges that could amplify cascade effects
4. Optimization opportunities at data flow junctions

The annealing process treats each intersection as a potential
synergy node, optimizing connection weights to reveal hidden patterns.
"""

import asyncio
import json
import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum
import sys
sys.path.insert(0, '/home/ubuntu/quorum_universe/quorum_core')

import networkx as nx
import numpy as np

from config import ARCHETYPES, QUORUM_PHILOSOPHERS


class IntersectionType(Enum):
    """Types of code intersections where synergies may hide"""
    MODULE_BOUNDARY = "module_boundary"       # Where modules meet
    FUNCTION_CALL = "function_call"           # Function invocation points
    DATA_FLOW = "data_flow"                   # Data transformation junctions
    CACHE_ACCESS = "cache_access"             # Cache read/write points
    GRAPH_QUERY = "graph_query"               # Graph traversal intersections
    API_ENDPOINT = "api_endpoint"             # External interface points
    ARCHETYPE_ROUTING = "archetype_routing"   # Archetype selection junctions
    TRIBUNAL_CHAIN = "tribunal_chain"         # Philosopher deliberation points


@dataclass
class Intersection:
    """Represents a code intersection point"""
    id: str
    type: IntersectionType
    source_module: str
    target_module: str
    weight: float = 0.5  # Connection strength (0-1)
    synergy_potential: float = 0.0
    hidden_cluster_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "source_module": self.source_module,
            "target_module": self.target_module,
            "weight": self.weight,
            "synergy_potential": self.synergy_potential,
            "hidden_cluster_id": self.hidden_cluster_id,
            "metadata": self.metadata,
        }


@dataclass
class HiddenSynergyCluster:
    """A hidden synergy cluster discovered through intersection annealing"""
    id: str
    name: str
    intersections: List[str]  # Intersection IDs
    total_synergy: float
    activation_energy: float  # Energy needed to activate this cluster
    cascade_multiplier: float  # How much it amplifies connected clusters
    discovery_method: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "intersections": self.intersections,
            "total_synergy": self.total_synergy,
            "activation_energy": self.activation_energy,
            "cascade_multiplier": self.cascade_multiplier,
            "discovery_method": self.discovery_method,
            "properties": self.properties,
        }


class IntersectionAnnealer:
    """
    Performs simulated annealing at code intersections to discover
    hidden synergy networks and optimization opportunities.
    """
    
    def __init__(self):
        self.intersection_graph = nx.DiGraph()
        self.intersections: Dict[str, Intersection] = {}
        self.hidden_clusters: List[HiddenSynergyCluster] = []
        self.annealing_history: List[Dict] = []
        
        # Module definitions for intersection mapping
        self.modules = {
            "config": {
                "functions": ["detect_platform", "get_data_path", "ARCHETYPES", "QUORUM_PHILOSOPHERS"],
                "exports": ["NEON_CONNECTION_STRING", "ARCHETYPES", "QUORUM_PHILOSOPHERS", "SYMBIOTIC_FOLDERS"],
            },
            "hex_ring_optimizer": {
                "functions": ["HexNode", "HexRing", "HexRingOptimizer", "optimize", "compute_synergy"],
                "exports": ["HexFace", "HexNode", "HexRing", "HexRingOptimizer"],
            },
            "graph_engine": {
                "functions": ["QuorumGraphEngine", "add_node", "add_edge", "traverse", "find_clusters"],
                "exports": ["NodeType", "EdgeType", "SynergyCluster", "QuorumGraphEngine"],
            },
            "redis_cache_manager": {
                "functions": ["MultiTierCache", "get", "set", "promote", "evict"],
                "exports": ["CacheTier", "MultiTierCache", "CrossPlatformSyncManager"],
            },
            "synergy_analyzer": {
                "functions": ["SynergyAnalyzer", "analyze_comprehensive", "find_clusters", "find_bursts"],
                "exports": ["SynergyBurst", "ComprehensiveSynergyReport", "SynergyAnalyzer"],
            },
            "api_server": {
                "functions": ["query_endpoint", "ingest_endpoint", "sync_endpoint", "health_check"],
                "exports": ["app", "router"],
            },
            "symbiotic_connector": {
                "functions": ["SymbioticConnector", "connect", "sync", "broadcast"],
                "exports": ["SymbioticConnector", "DeviceRegistry"],
            },
        }
        
        self._build_intersection_graph()
    
    def _build_intersection_graph(self):
        """Build graph of all code intersections"""
        print("\n[Intersection Mapping] Building intersection graph...")
        
        # Add module nodes
        for module_name in self.modules:
            self.intersection_graph.add_node(
                f"module:{module_name}",
                type="module",
                functions=self.modules[module_name]["functions"],
            )
        
        # Define module dependencies (intersections)
        dependencies = [
            # Core dependencies
            ("api_server", "config", IntersectionType.MODULE_BOUNDARY),
            ("api_server", "graph_engine", IntersectionType.DATA_FLOW),
            ("api_server", "redis_cache_manager", IntersectionType.CACHE_ACCESS),
            ("api_server", "synergy_analyzer", IntersectionType.FUNCTION_CALL),
            ("api_server", "symbiotic_connector", IntersectionType.API_ENDPOINT),
            
            # Graph engine dependencies
            ("graph_engine", "config", IntersectionType.MODULE_BOUNDARY),
            ("graph_engine", "hex_ring_optimizer", IntersectionType.DATA_FLOW),
            
            # Synergy analyzer dependencies
            ("synergy_analyzer", "config", IntersectionType.MODULE_BOUNDARY),
            ("synergy_analyzer", "graph_engine", IntersectionType.GRAPH_QUERY),
            ("synergy_analyzer", "hex_ring_optimizer", IntersectionType.DATA_FLOW),
            
            # Cache dependencies
            ("redis_cache_manager", "config", IntersectionType.MODULE_BOUNDARY),
            ("redis_cache_manager", "symbiotic_connector", IntersectionType.DATA_FLOW),
            
            # Symbiotic connector dependencies
            ("symbiotic_connector", "config", IntersectionType.MODULE_BOUNDARY),
            ("symbiotic_connector", "redis_cache_manager", IntersectionType.CACHE_ACCESS),
            
            # Hex optimizer dependencies
            ("hex_ring_optimizer", "config", IntersectionType.MODULE_BOUNDARY),
            
            # Archetype routing intersections
            ("api_server", "hex_ring_optimizer", IntersectionType.ARCHETYPE_ROUTING),
            ("synergy_analyzer", "redis_cache_manager", IntersectionType.CACHE_ACCESS),
            
            # Tribunal chain intersections
            ("api_server", "config", IntersectionType.TRIBUNAL_CHAIN),
            ("synergy_analyzer", "config", IntersectionType.TRIBUNAL_CHAIN),
        ]
        
        for source, target, int_type in dependencies:
            int_id = f"{source}->{target}"
            
            intersection = Intersection(
                id=int_id,
                type=int_type,
                source_module=source,
                target_module=target,
                weight=random.uniform(0.3, 0.7),  # Initial random weight
            )
            
            self.intersections[int_id] = intersection
            self.intersection_graph.add_edge(
                f"module:{source}",
                f"module:{target}",
                intersection_id=int_id,
                type=int_type.value,
            )
        
        print(f"  → {len(self.modules)} modules mapped")
        print(f"  → {len(self.intersections)} intersections identified")
    
    def _compute_intersection_synergy(self, intersection: Intersection) -> float:
        """Compute synergy potential at an intersection"""
        base_synergy = 0.0
        
        # Type-based synergy multipliers
        type_multipliers = {
            IntersectionType.MODULE_BOUNDARY: 0.6,
            IntersectionType.FUNCTION_CALL: 0.7,
            IntersectionType.DATA_FLOW: 0.85,
            IntersectionType.CACHE_ACCESS: 0.9,
            IntersectionType.GRAPH_QUERY: 0.95,
            IntersectionType.API_ENDPOINT: 0.75,
            IntersectionType.ARCHETYPE_ROUTING: 1.0,
            IntersectionType.TRIBUNAL_CHAIN: 0.98,
        }
        
        base_synergy = type_multipliers.get(intersection.type, 0.5)
        
        # Weight contribution
        weight_factor = intersection.weight * 0.5
        
        # Module importance factor
        critical_modules = {"graph_engine", "hex_ring_optimizer", "synergy_analyzer"}
        if intersection.source_module in critical_modules or intersection.target_module in critical_modules:
            base_synergy *= 1.2
        
        return min(1.0, base_synergy + weight_factor)
    
    def _compute_total_energy(self) -> float:
        """Compute total energy of the intersection system"""
        total = 0.0
        for intersection in self.intersections.values():
            synergy = self._compute_intersection_synergy(intersection)
            intersection.synergy_potential = synergy
            total += synergy
        return total / len(self.intersections) if self.intersections else 0.0
    
    async def anneal_intersections(
        self,
        initial_temp: float = 2.0,
        cooling_rate: float = 0.99,
        min_temp: float = 0.001,
        max_iterations: int = 5000,
    ) -> Dict:
        """
        Run simulated annealing on intersection weights to discover
        optimal synergy configurations.
        """
        print("\n" + "=" * 60)
        print("INTERSECTION ANNEALING")
        print("=" * 60)
        print(f"Initial temperature: {initial_temp}")
        print(f"Cooling rate: {cooling_rate}")
        print(f"Max iterations: {max_iterations}")
        print("=" * 60)
        
        start_time = time.time()
        
        temperature = initial_temp
        current_energy = self._compute_total_energy()
        best_energy = current_energy
        best_weights = {k: v.weight for k, v in self.intersections.items()}
        
        iterations = 0
        improvements = 0
        
        while temperature > min_temp and iterations < max_iterations:
            # Select random intersection to perturb
            int_id = random.choice(list(self.intersections.keys()))
            intersection = self.intersections[int_id]
            
            # Store old weight
            old_weight = intersection.weight
            
            # Perturb weight
            delta = random.gauss(0, 0.1 * temperature)
            intersection.weight = max(0.0, min(1.0, old_weight + delta))
            
            # Compute new energy
            new_energy = self._compute_total_energy()
            
            # Accept or reject
            delta_energy = new_energy - current_energy
            
            if delta_energy > 0 or random.random() < math.exp(delta_energy / temperature):
                current_energy = new_energy
                
                if current_energy > best_energy:
                    best_energy = current_energy
                    best_weights = {k: v.weight for k, v in self.intersections.items()}
                    improvements += 1
            else:
                # Reject - restore old weight
                intersection.weight = old_weight
            
            # Cool down
            temperature *= cooling_rate
            iterations += 1
            
            # Record history periodically
            if iterations % 500 == 0:
                self.annealing_history.append({
                    "iteration": iterations,
                    "temperature": temperature,
                    "current_energy": current_energy,
                    "best_energy": best_energy,
                })
        
        # Restore best weights
        for int_id, weight in best_weights.items():
            self.intersections[int_id].weight = weight
        
        # Recompute final synergies
        self._compute_total_energy()
        
        duration = time.time() - start_time
        
        print("=" * 60)
        print("ANNEALING COMPLETE")
        print("=" * 60)
        print(f"Iterations: {iterations}")
        print(f"Improvements: {improvements}")
        print(f"Best energy: {best_energy:.4f}")
        print(f"Duration: {duration:.2f}s")
        print("=" * 60)
        
        return {
            "iterations": iterations,
            "improvements": improvements,
            "best_energy": best_energy,
            "duration_seconds": duration,
            "final_weights": best_weights,
        }
    
    async def discover_hidden_clusters(self) -> List[HiddenSynergyCluster]:
        """Discover hidden synergy clusters from annealed intersections"""
        print("\n[Hidden Cluster Discovery] Analyzing intersection patterns...")
        
        self.hidden_clusters = []
        
        # Method 1: High-synergy intersection chains
        await self._discover_chain_clusters()
        
        # Method 2: Type-based clustering
        await self._discover_type_clusters()
        
        # Method 3: Module hub analysis
        await self._discover_hub_clusters()
        
        # Method 4: Cross-domain bridges
        await self._discover_bridge_clusters()
        
        # Sort by total synergy
        self.hidden_clusters.sort(key=lambda x: x.total_synergy, reverse=True)
        
        print(f"  → {len(self.hidden_clusters)} hidden clusters discovered")
        
        return self.hidden_clusters
    
    async def _discover_chain_clusters(self):
        """Find chains of high-synergy intersections"""
        # Sort intersections by synergy
        sorted_ints = sorted(
            self.intersections.values(),
            key=lambda x: x.synergy_potential,
            reverse=True
        )
        
        # Find chains starting from high-synergy intersections
        visited = set()
        chain_id = 0
        
        for start_int in sorted_ints[:10]:  # Top 10 as seeds
            if start_int.id in visited:
                continue
            
            chain = [start_int.id]
            visited.add(start_int.id)
            
            # Follow high-synergy connections
            current_module = start_int.target_module
            
            for _ in range(5):  # Max chain length
                # Find next high-synergy intersection from current module
                candidates = [
                    i for i in self.intersections.values()
                    if i.source_module == current_module
                    and i.id not in visited
                    and i.synergy_potential > 0.6
                ]
                
                if not candidates:
                    break
                
                next_int = max(candidates, key=lambda x: x.synergy_potential)
                chain.append(next_int.id)
                visited.add(next_int.id)
                current_module = next_int.target_module
            
            if len(chain) >= 2:
                total_synergy = sum(
                    self.intersections[i].synergy_potential for i in chain
                )
                
                cluster = HiddenSynergyCluster(
                    id=f"chain_{chain_id}",
                    name=f"Synergy Chain {chain_id + 1}",
                    intersections=chain,
                    total_synergy=total_synergy,
                    activation_energy=1.0 / (total_synergy + 0.1),
                    cascade_multiplier=1.0 + len(chain) * 0.2,
                    discovery_method="chain_analysis",
                    properties={
                        "chain_length": len(chain),
                        "start_module": self.intersections[chain[0]].source_module,
                        "end_module": self.intersections[chain[-1]].target_module,
                    }
                )
                
                self.hidden_clusters.append(cluster)
                chain_id += 1
    
    async def _discover_type_clusters(self):
        """Find clusters based on intersection types"""
        type_groups = defaultdict(list)
        
        for int_id, intersection in self.intersections.items():
            type_groups[intersection.type].append(int_id)
        
        for int_type, int_ids in type_groups.items():
            if len(int_ids) >= 2:
                total_synergy = sum(
                    self.intersections[i].synergy_potential for i in int_ids
                )
                
                cluster = HiddenSynergyCluster(
                    id=f"type_{int_type.value}",
                    name=f"{int_type.value.replace('_', ' ').title()} Network",
                    intersections=int_ids,
                    total_synergy=total_synergy,
                    activation_energy=0.5 / (total_synergy + 0.1),
                    cascade_multiplier=1.0 + len(int_ids) * 0.15,
                    discovery_method="type_clustering",
                    properties={
                        "intersection_type": int_type.value,
                        "cluster_size": len(int_ids),
                    }
                )
                
                self.hidden_clusters.append(cluster)
    
    async def _discover_hub_clusters(self):
        """Find clusters around module hubs"""
        # Count connections per module
        module_connections = defaultdict(list)
        
        for int_id, intersection in self.intersections.items():
            module_connections[intersection.source_module].append(int_id)
            module_connections[intersection.target_module].append(int_id)
        
        # Find hub modules (high connection count)
        for module, int_ids in module_connections.items():
            unique_ids = list(set(int_ids))
            if len(unique_ids) >= 3:
                total_synergy = sum(
                    self.intersections[i].synergy_potential for i in unique_ids
                )
                
                cluster = HiddenSynergyCluster(
                    id=f"hub_{module}",
                    name=f"{module.replace('_', ' ').title()} Hub",
                    intersections=unique_ids,
                    total_synergy=total_synergy,
                    activation_energy=0.3 / (total_synergy + 0.1),
                    cascade_multiplier=1.5 + len(unique_ids) * 0.1,
                    discovery_method="hub_analysis",
                    properties={
                        "hub_module": module,
                        "connection_count": len(unique_ids),
                    }
                )
                
                self.hidden_clusters.append(cluster)
    
    async def _discover_bridge_clusters(self):
        """Find cross-domain bridge clusters"""
        # Find intersections that bridge different functional areas
        functional_areas = {
            "data": {"graph_engine", "redis_cache_manager"},
            "analysis": {"synergy_analyzer", "hex_ring_optimizer"},
            "interface": {"api_server", "symbiotic_connector"},
            "config": {"config"},
        }
        
        def get_area(module: str) -> str:
            for area, modules in functional_areas.items():
                if module in modules:
                    return area
            return "other"
        
        bridge_ints = []
        for int_id, intersection in self.intersections.items():
            source_area = get_area(intersection.source_module)
            target_area = get_area(intersection.target_module)
            
            if source_area != target_area and source_area != "config" and target_area != "config":
                bridge_ints.append(int_id)
        
        if bridge_ints:
            total_synergy = sum(
                self.intersections[i].synergy_potential for i in bridge_ints
            )
            
            cluster = HiddenSynergyCluster(
                id="cross_domain_bridge",
                name="Cross-Domain Bridge Network",
                intersections=bridge_ints,
                total_synergy=total_synergy,
                activation_energy=0.2 / (total_synergy + 0.1),
                cascade_multiplier=2.0,  # High multiplier for bridges
                discovery_method="bridge_analysis",
                properties={
                    "bridge_count": len(bridge_ints),
                    "areas_connected": list(set(
                        get_area(self.intersections[i].source_module)
                        for i in bridge_ints
                    ) | set(
                        get_area(self.intersections[i].target_module)
                        for i in bridge_ints
                    )),
                }
            )
            
            self.hidden_clusters.append(cluster)
    
    async def calculate_cascade_potential(self) -> Dict:
        """Calculate cascade activation potential across all clusters"""
        print("\n[Cascade Analysis] Computing cascade potentials...")
        
        cascade_results = {
            "total_clusters": len(self.hidden_clusters),
            "total_cascade_potential": 0.0,
            "activation_sequence": [],
            "cascade_chains": [],
        }
        
        if not self.hidden_clusters:
            return cascade_results
        
        # Sort clusters by activation energy (easiest to activate first)
        sorted_clusters = sorted(
            self.hidden_clusters,
            key=lambda x: x.activation_energy
        )
        
        # Simulate cascade activation
        activated = set()
        cascade_energy = 1.0  # Initial activation energy
        
        for cluster in sorted_clusters:
            if cascade_energy >= cluster.activation_energy:
                activated.add(cluster.id)
                cascade_energy *= cluster.cascade_multiplier
                
                cascade_results["activation_sequence"].append({
                    "cluster_id": cluster.id,
                    "cluster_name": cluster.name,
                    "activation_energy": cluster.activation_energy,
                    "cascade_multiplier": cluster.cascade_multiplier,
                    "resulting_energy": cascade_energy,
                })
        
        cascade_results["total_cascade_potential"] = cascade_energy
        cascade_results["activated_clusters"] = len(activated)
        
        print(f"  → {len(activated)} clusters in cascade chain")
        print(f"  → Total cascade potential: {cascade_energy:.2f}x")
        
        return cascade_results
    
    async def run_comprehensive_analysis(self) -> Dict:
        """Run complete intersection annealing and cluster discovery"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE INTERSECTION ANNEALING ANALYSIS")
        print("=" * 70)
        
        start_time = time.time()
        
        # Phase 1: Anneal intersections
        annealing_results = await self.anneal_intersections()
        
        # Phase 2: Discover hidden clusters
        hidden_clusters = await self.discover_hidden_clusters()
        
        # Phase 3: Calculate cascade potential
        cascade_results = await self.calculate_cascade_potential()
        
        # Phase 4: Generate optimization recommendations
        recommendations = self._generate_recommendations()
        
        duration = time.time() - start_time
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "annealing": annealing_results,
            "intersections": [i.to_dict() for i in self.intersections.values()],
            "hidden_clusters": [c.to_dict() for c in hidden_clusters],
            "cascade_analysis": cascade_results,
            "recommendations": recommendations,
            "summary": {
                "total_intersections": len(self.intersections),
                "total_hidden_clusters": len(hidden_clusters),
                "best_annealing_energy": annealing_results["best_energy"],
                "total_cascade_potential": cascade_results["total_cascade_potential"],
            }
        }
        
        # Save results
        output_path = "/home/ubuntu/quorum_universe/intersection_annealing_report.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'=' * 70}")
        print("INTERSECTION ANNEALING COMPLETE")
        print(f"{'=' * 70}")
        print(f"Duration: {duration:.2f}s")
        print(f"Report saved: {output_path}")
        
        return results
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        # Recommendation 1: High-synergy intersections to strengthen
        high_synergy = sorted(
            self.intersections.values(),
            key=lambda x: x.synergy_potential,
            reverse=True
        )[:5]
        
        recommendations.append({
            "id": "strengthen_high_synergy",
            "priority": "high",
            "title": "Strengthen High-Synergy Intersections",
            "description": "These intersections have the highest synergy potential and should be optimized for maximum throughput.",
            "affected_intersections": [i.id for i in high_synergy],
            "actions": [
                "Add caching at these intersection points",
                "Implement lazy loading for data transfers",
                "Create dedicated connection pools",
            ],
        })
        
        # Recommendation 2: Activate cascade chains
        if self.hidden_clusters:
            best_cascade = max(self.hidden_clusters, key=lambda x: x.cascade_multiplier)
            recommendations.append({
                "id": "activate_cascade_chain",
                "priority": "high",
                "title": f"Activate {best_cascade.name} Cascade",
                "description": f"This cluster has the highest cascade multiplier ({best_cascade.cascade_multiplier:.2f}x).",
                "affected_intersections": best_cascade.intersections,
                "actions": [
                    "Pre-warm cache entries for cluster members",
                    "Implement predictive loading based on access patterns",
                    "Create batch processing pipelines",
                ],
            })
        
        # Recommendation 3: Bridge optimization
        bridge_ints = [
            i for i in self.intersections.values()
            if i.type in {IntersectionType.DATA_FLOW, IntersectionType.GRAPH_QUERY}
        ]
        
        if bridge_ints:
            recommendations.append({
                "id": "optimize_bridges",
                "priority": "medium",
                "title": "Optimize Cross-Domain Bridges",
                "description": "Data flow and graph query intersections are critical bridges between functional areas.",
                "affected_intersections": [i.id for i in bridge_ints],
                "actions": [
                    "Implement async data pipelines",
                    "Add query result caching",
                    "Create materialized views for common queries",
                ],
            })
        
        # Recommendation 4: Low-synergy improvement
        low_synergy = sorted(
            self.intersections.values(),
            key=lambda x: x.synergy_potential
        )[:3]
        
        recommendations.append({
            "id": "improve_low_synergy",
            "priority": "medium",
            "title": "Improve Low-Synergy Intersections",
            "description": "These intersections have untapped synergy potential.",
            "affected_intersections": [i.id for i in low_synergy],
            "actions": [
                "Review interface contracts for optimization opportunities",
                "Consider merging related functionality",
                "Implement shared state management",
            ],
        })
        
        return recommendations


async def main():
    """Run comprehensive intersection annealing analysis"""
    annealer = IntersectionAnnealer()
    results = await annealer.run_comprehensive_analysis()
    
    # Print summary
    print("\n" + "=" * 70)
    print("EXECUTIVE SUMMARY")
    print("=" * 70)
    
    summary = results["summary"]
    print(f"\nTotal Intersections: {summary['total_intersections']}")
    print(f"Hidden Clusters Discovered: {summary['total_hidden_clusters']}")
    print(f"Best Annealing Energy: {summary['best_annealing_energy']:.4f}")
    print(f"Total Cascade Potential: {summary['total_cascade_potential']:.2f}x")
    
    print("\nTop Hidden Clusters:")
    for cluster in results["hidden_clusters"][:5]:
        print(f"  • {cluster['name']}: synergy={cluster['total_synergy']:.3f}, cascade={cluster['cascade_multiplier']:.2f}x")
    
    print("\nRecommendations:")
    for rec in results["recommendations"]:
        print(f"  [{rec['priority'].upper()}] {rec['title']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

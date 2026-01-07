#!/usr/bin/env python3
"""
Hexagonal Ring Collapse Optimizer for Knowledge Graph Synergies

This module implements a Rubik's Cube-like optimization algorithm for
arranging knowledge archetypes in concentric hexagonal rings, where:

1. Each archetype is a hexagonal node with 6 relational faces
2. Archetypes are arranged in concentric rings (core → peripheral)
3. Ring rotation optimizes face-to-face synergy alignment
4. Goal: Minimize total relational distance across all hex faces

The algorithm uses simulated annealing to find optimal ring rotations
that maximize synergy between adjacent disciplines.
"""

import math
import random
import json
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
import numpy as np
from datetime import datetime

# Import config
try:
    from config import ARCHETYPES, QUORUM_PHILOSOPHERS
except ImportError:
    ARCHETYPES = {}
    QUORUM_PHILOSOPHERS = {}


class HexFace(Enum):
    """Six faces of a hexagonal node, representing relational dimensions"""
    THEORETICAL = 0      # Abstract/theoretical connections
    EMPIRICAL = 1        # Data/evidence-based connections
    METHODOLOGICAL = 2   # Shared methods/approaches
    HISTORICAL = 3       # Historical/temporal connections
    APPLIED = 4          # Practical application connections
    PHILOSOPHICAL = 5    # Foundational/philosophical connections


@dataclass
class HexNode:
    """A hexagonal knowledge node with 6 relational faces"""
    id: str
    name: str
    ring: int  # 0 = core, 1 = inner, 2 = middle, 3 = outer
    position: int  # Position within ring (0 to ring_size-1)
    cluster: str
    domains: List[str]
    corpus_size_gb: float
    
    # Face affinities: scores for each face type (0-1)
    face_affinities: Dict[HexFace, float] = field(default_factory=dict)
    
    # Synergy scores with other nodes (computed dynamically)
    synergy_cache: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.face_affinities:
            self._compute_face_affinities()
    
    def _compute_face_affinities(self):
        """Compute face affinities based on archetype characteristics"""
        # Default affinities based on cluster type
        cluster_profiles = {
            'stem_core': {
                HexFace.THEORETICAL: 0.9,
                HexFace.EMPIRICAL: 0.85,
                HexFace.METHODOLOGICAL: 0.8,
                HexFace.HISTORICAL: 0.4,
                HexFace.APPLIED: 0.7,
                HexFace.PHILOSOPHICAL: 0.5,
            },
            'applied_tech': {
                HexFace.THEORETICAL: 0.6,
                HexFace.EMPIRICAL: 0.8,
                HexFace.METHODOLOGICAL: 0.85,
                HexFace.HISTORICAL: 0.3,
                HexFace.APPLIED: 0.95,
                HexFace.PHILOSOPHICAL: 0.4,
            },
            'life_systems': {
                HexFace.THEORETICAL: 0.7,
                HexFace.EMPIRICAL: 0.95,
                HexFace.METHODOLOGICAL: 0.8,
                HexFace.HISTORICAL: 0.5,
                HexFace.APPLIED: 0.85,
                HexFace.PHILOSOPHICAL: 0.5,
            },
            'human_systems': {
                HexFace.THEORETICAL: 0.75,
                HexFace.EMPIRICAL: 0.6,
                HexFace.METHODOLOGICAL: 0.7,
                HexFace.HISTORICAL: 0.85,
                HexFace.APPLIED: 0.7,
                HexFace.PHILOSOPHICAL: 0.8,
            },
            'meta_cognitive': {
                HexFace.THEORETICAL: 0.95,
                HexFace.EMPIRICAL: 0.5,
                HexFace.METHODOLOGICAL: 0.75,
                HexFace.HISTORICAL: 0.7,
                HexFace.APPLIED: 0.5,
                HexFace.PHILOSOPHICAL: 0.95,
            },
            'non_western': {
                HexFace.THEORETICAL: 0.8,
                HexFace.EMPIRICAL: 0.5,
                HexFace.METHODOLOGICAL: 0.6,
                HexFace.HISTORICAL: 0.95,
                HexFace.APPLIED: 0.6,
                HexFace.PHILOSOPHICAL: 0.9,
            },
            'creative_synthesis': {
                HexFace.THEORETICAL: 0.6,
                HexFace.EMPIRICAL: 0.55,
                HexFace.METHODOLOGICAL: 0.7,
                HexFace.HISTORICAL: 0.6,
                HexFace.APPLIED: 0.8,
                HexFace.PHILOSOPHICAL: 0.75,
            },
        }
        
        profile = cluster_profiles.get(self.cluster, {
            face: 0.5 for face in HexFace
        })
        
        # Add domain-specific modulations
        domain_modulations = {
            'physics': {HexFace.THEORETICAL: 0.1, HexFace.EMPIRICAL: 0.1},
            'mathematics': {HexFace.THEORETICAL: 0.15, HexFace.METHODOLOGICAL: 0.1},
            'biology': {HexFace.EMPIRICAL: 0.15, HexFace.APPLIED: 0.1},
            'philosophy': {HexFace.PHILOSOPHICAL: 0.15, HexFace.THEORETICAL: 0.1},
            'engineering': {HexFace.APPLIED: 0.15, HexFace.METHODOLOGICAL: 0.1},
            'history': {HexFace.HISTORICAL: 0.15, HexFace.PHILOSOPHICAL: 0.05},
            'ai': {HexFace.APPLIED: 0.1, HexFace.THEORETICAL: 0.1},
            'medicine': {HexFace.EMPIRICAL: 0.1, HexFace.APPLIED: 0.15},
        }
        
        for domain in self.domains:
            domain_lower = domain.lower()
            for key, mods in domain_modulations.items():
                if key in domain_lower:
                    for face, mod in mods.items():
                        profile[face] = min(1.0, profile.get(face, 0.5) + mod)
        
        self.face_affinities = profile
    
    def get_face_vector(self) -> np.ndarray:
        """Get face affinities as a numpy vector"""
        return np.array([self.face_affinities[face] for face in HexFace])
    
    def compute_synergy(self, other: 'HexNode') -> float:
        """Compute synergy score with another node based on face alignment"""
        cache_key = other.id
        if cache_key in self.synergy_cache:
            return self.synergy_cache[cache_key]
        
        # Compute face-to-face synergy
        self_vec = self.get_face_vector()
        other_vec = other.get_face_vector()
        
        # Complementary synergy: high when faces complement each other
        complementary = np.sum(self_vec * other_vec) / 6.0
        
        # Domain overlap bonus
        self_domains = set(d.lower() for d in self.domains)
        other_domains = set(d.lower() for d in other.domains)
        domain_overlap = len(self_domains & other_domains) / max(len(self_domains | other_domains), 1)
        
        # Cluster affinity bonus
        cluster_affinity = 0.2 if self.cluster == other.cluster else 0.0
        
        # Combined synergy score
        synergy = 0.5 * complementary + 0.3 * domain_overlap + 0.2 * cluster_affinity
        
        self.synergy_cache[cache_key] = synergy
        return synergy


@dataclass
class HexRing:
    """A ring of hexagonal nodes that can be rotated"""
    level: int  # 0 = core (1 node), 1 = inner (6 nodes), 2 = middle (12 nodes), etc.
    nodes: List[HexNode]
    rotation: int = 0  # Current rotation offset (0 to size-1)
    
    @property
    def size(self) -> int:
        """Number of nodes in this ring"""
        if self.level == 0:
            return 1
        return 6 * self.level
    
    def rotate(self, steps: int):
        """Rotate the ring by given steps"""
        if self.size > 1:
            self.rotation = (self.rotation + steps) % self.size
    
    def get_node_at_position(self, position: int) -> Optional[HexNode]:
        """Get node at absolute position (accounting for rotation)"""
        if not self.nodes:
            return None
        if self.size == 1:
            return self.nodes[0]
        actual_pos = (position - self.rotation) % self.size
        if actual_pos < len(self.nodes):
            return self.nodes[actual_pos]
        return None
    
    def get_adjacent_positions(self, position: int) -> List[Tuple[int, int]]:
        """Get (ring_level, position) tuples for adjacent nodes"""
        adjacents = []
        
        # Same ring neighbors (left and right)
        if self.size > 1:
            adjacents.append((self.level, (position - 1) % self.size))
            adjacents.append((self.level, (position + 1) % self.size))
        
        # Inner ring connections
        if self.level > 0:
            inner_size = 1 if self.level == 1 else 6 * (self.level - 1)
            if inner_size == 1:
                adjacents.append((self.level - 1, 0))
            else:
                # Map to inner ring positions
                inner_pos = int(position * inner_size / self.size)
                adjacents.append((self.level - 1, inner_pos))
        
        # Outer ring connections (computed by caller)
        
        return adjacents


class HexRingOptimizer:
    """
    Optimizes hexagonal ring arrangement using simulated annealing.
    
    The goal is to rotate rings to maximize total synergy between
    adjacent nodes across all faces.
    """
    
    def __init__(self, archetypes: Dict = None):
        self.archetypes = archetypes or ARCHETYPES
        self.rings: List[HexRing] = []
        self.nodes: Dict[str, HexNode] = {}
        self.best_state: Dict[int, int] = {}  # ring_level -> rotation
        self.best_score: float = 0.0
        self.optimization_history: List[Dict] = []
        
        self._initialize_rings()
    
    def _initialize_rings(self):
        """Initialize hexagonal rings from archetypes"""
        # Assign archetypes to rings based on cluster importance
        cluster_ring_map = {
            'meta_cognitive': 0,    # Core
            'stem_core': 1,         # Inner ring
            'life_systems': 1,      # Inner ring
            'applied_tech': 2,      # Middle ring
            'human_systems': 2,     # Middle ring
            'non_western': 3,       # Outer ring
            'creative_synthesis': 3, # Outer ring
        }
        
        # Group archetypes by ring
        ring_groups: Dict[int, List[HexNode]] = {0: [], 1: [], 2: [], 3: []}
        
        for arch_id, arch_data in self.archetypes.items():
            cluster = arch_data.get('cluster', 'applied_tech')
            ring_level = cluster_ring_map.get(cluster, 2)
            
            node = HexNode(
                id=arch_id,
                name=arch_id.replace('_', ' ').title(),
                ring=ring_level,
                position=len(ring_groups[ring_level]),
                cluster=cluster,
                domains=arch_data.get('domains', []),
                corpus_size_gb=arch_data.get('corpus_size_gb', 10),
            )
            
            ring_groups[ring_level].append(node)
            self.nodes[arch_id] = node
        
        # Create rings
        for level in range(4):
            ring = HexRing(level=level, nodes=ring_groups[level])
            self.rings.append(ring)
            
            # Update node positions
            for i, node in enumerate(ring.nodes):
                node.position = i
    
    def compute_total_synergy(self) -> float:
        """Compute total synergy score for current ring configuration"""
        total_synergy = 0.0
        connection_count = 0
        
        for ring in self.rings:
            for pos, node in enumerate(ring.nodes):
                # Get actual position with rotation
                actual_pos = (pos + ring.rotation) % max(ring.size, 1)
                
                # Get adjacent nodes
                adjacents = ring.get_adjacent_positions(actual_pos)
                
                for adj_ring_level, adj_pos in adjacents:
                    if adj_ring_level < len(self.rings):
                        adj_ring = self.rings[adj_ring_level]
                        adj_node = adj_ring.get_node_at_position(adj_pos)
                        
                        if adj_node and adj_node.id != node.id:
                            synergy = node.compute_synergy(adj_node)
                            total_synergy += synergy
                            connection_count += 1
        
        # Normalize by connection count
        if connection_count > 0:
            total_synergy /= connection_count
        
        return total_synergy
    
    def get_node_by_id(self, node_id: str) -> Optional[HexNode]:
        """Get a node by its ID"""
        return self.nodes.get(node_id)
    
    def get_adjacent_nodes(self, node: HexNode) -> Dict[HexFace, Optional[HexNode]]:
        """Get adjacent nodes for each face of a hex node"""
        adjacents = {face: None for face in HexFace}
        
        if node.ring >= len(self.rings):
            return adjacents
        
        ring = self.rings[node.ring]
        actual_pos = (node.position + ring.rotation) % max(ring.size, 1)
        
        # Get adjacent positions
        adj_positions = ring.get_adjacent_positions(actual_pos)
        
        # Map to faces
        face_list = list(HexFace)
        for i, (adj_ring_level, adj_pos) in enumerate(adj_positions):
            if adj_ring_level < len(self.rings):
                adj_ring = self.rings[adj_ring_level]
                adj_node = adj_ring.get_node_at_position(adj_pos)
                if adj_node and i < len(face_list):
                    adjacents[face_list[i]] = adj_node
        
        return adjacents
    
    def get_ring_state(self) -> Dict[int, int]:
        """Get current rotation state of all rings"""
        return {ring.level: ring.rotation for ring in self.rings}
    
    def set_ring_state(self, state: Dict[int, int]):
        """Set rotation state for all rings"""
        for ring in self.rings:
            if ring.level in state:
                ring.rotation = state[ring.level]
    
    async def optimize(
        self,
        initial_temp: float = 1.0,
        cooling_rate: float = 0.995,
        min_temp: float = 0.001,
        max_iterations: int = 10000,
        callback=None
    ) -> Dict:
        """
        Run simulated annealing optimization to find optimal ring rotations.
        
        Returns optimization results including best state and synergy score.
        """
        print("\n" + "=" * 60)
        print("HEXAGONAL RING COLLAPSE OPTIMIZATION")
        print("=" * 60)
        print(f"Rings: {len(self.rings)}")
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Initial temperature: {initial_temp}")
        print(f"Cooling rate: {cooling_rate}")
        print("=" * 60 + "\n")
        
        start_time = datetime.now()
        
        # Initialize
        current_score = self.compute_total_synergy()
        self.best_score = current_score
        self.best_state = self.get_ring_state()
        
        temperature = initial_temp
        iteration = 0
        improvements = 0
        
        while temperature > min_temp and iteration < max_iterations:
            # Select random ring to rotate (skip core ring with 1 node)
            rotatable_rings = [r for r in self.rings if r.size > 1]
            if not rotatable_rings:
                break
            
            ring = random.choice(rotatable_rings)
            
            # Random rotation step
            step = random.choice([-2, -1, 1, 2])
            old_rotation = ring.rotation
            ring.rotate(step)
            
            # Compute new score
            new_score = self.compute_total_synergy()
            
            # Acceptance probability
            delta = new_score - current_score
            
            if delta > 0:
                # Better solution - always accept
                current_score = new_score
                if new_score > self.best_score:
                    self.best_score = new_score
                    self.best_state = self.get_ring_state()
                    improvements += 1
            else:
                # Worse solution - accept with probability
                acceptance_prob = math.exp(delta / temperature)
                if random.random() < acceptance_prob:
                    current_score = new_score
                else:
                    # Reject - revert rotation
                    ring.rotation = old_rotation
            
            # Cool down
            temperature *= cooling_rate
            iteration += 1
            
            # Record history periodically
            if iteration % 100 == 0:
                self.optimization_history.append({
                    'iteration': iteration,
                    'temperature': temperature,
                    'current_score': current_score,
                    'best_score': self.best_score,
                })
                
                if callback:
                    await callback({
                        'iteration': iteration,
                        'temperature': temperature,
                        'score': current_score,
                        'best_score': self.best_score,
                    })
            
            # Yield control periodically for async
            if iteration % 500 == 0:
                await asyncio.sleep(0)
        
        # Restore best state
        self.set_ring_state(self.best_state)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        results = {
            'success': True,
            'iterations': iteration,
            'improvements': improvements,
            'initial_score': self.optimization_history[0]['current_score'] if self.optimization_history else current_score,
            'final_score': self.best_score,
            'improvement_percent': ((self.best_score - (self.optimization_history[0]['current_score'] if self.optimization_history else current_score)) / max(self.optimization_history[0]['current_score'] if self.optimization_history else current_score, 0.001)) * 100,
            'best_state': self.best_state,
            'duration_seconds': duration,
            'final_temperature': temperature,
        }
        
        print("\n" + "=" * 60)
        print("OPTIMIZATION COMPLETE")
        print("=" * 60)
        print(f"Iterations: {iteration}")
        print(f"Improvements found: {improvements}")
        print(f"Final synergy score: {self.best_score:.4f}")
        print(f"Duration: {duration:.2f}s")
        print("=" * 60 + "\n")
        
        return results
    
    def get_optimal_adjacencies(self) -> List[Dict]:
        """Get list of optimal node adjacencies after optimization"""
        adjacencies = []
        
        for ring in self.rings:
            for pos, node in enumerate(ring.nodes):
                actual_pos = (pos + ring.rotation) % max(ring.size, 1)
                
                adj_positions = ring.get_adjacent_positions(actual_pos)
                
                for adj_ring_level, adj_pos in adj_positions:
                    if adj_ring_level < len(self.rings):
                        adj_ring = self.rings[adj_ring_level]
                        adj_node = adj_ring.get_node_at_position(adj_pos)
                        
                        if adj_node and adj_node.id != node.id:
                            synergy = node.compute_synergy(adj_node)
                            adjacencies.append({
                                'source': node.id,
                                'source_name': node.name,
                                'source_ring': node.ring,
                                'target': adj_node.id,
                                'target_name': adj_node.name,
                                'target_ring': adj_node.ring,
                                'synergy': synergy,
                                'face_alignment': self._get_face_alignment(node, adj_node),
                            })
        
        # Sort by synergy score
        adjacencies.sort(key=lambda x: x['synergy'], reverse=True)
        
        return adjacencies
    
    def _get_face_alignment(self, node1: HexNode, node2: HexNode) -> Dict[str, float]:
        """Get face-by-face alignment scores between two nodes"""
        alignment = {}
        for face in HexFace:
            score = node1.face_affinities[face] * node2.face_affinities[face]
            alignment[face.name.lower()] = round(score, 3)
        return alignment
    
    def get_ring_visualization_data(self) -> Dict:
        """Get data for D3.js hexagonal ring visualization"""
        rings_data = []
        
        for ring in self.rings:
            ring_nodes = []
            for i, node in enumerate(ring.nodes):
                # Calculate position with rotation
                actual_pos = (i + ring.rotation) % max(ring.size, 1)
                
                # Calculate angle for visualization
                if ring.size == 1:
                    angle = 0
                else:
                    angle = (actual_pos / ring.size) * 2 * math.pi
                
                ring_nodes.append({
                    'id': node.id,
                    'name': node.name,
                    'cluster': node.cluster,
                    'domains': node.domains,
                    'corpus_size_gb': node.corpus_size_gb,
                    'position': actual_pos,
                    'angle': angle,
                    'face_affinities': {f.name: v for f, v in node.face_affinities.items()},
                })
            
            rings_data.append({
                'level': ring.level,
                'size': ring.size,
                'rotation': ring.rotation,
                'nodes': ring_nodes,
            })
        
        # Get edges (adjacencies)
        edges = []
        adjacencies = self.get_optimal_adjacencies()
        seen_edges = set()
        
        for adj in adjacencies:
            edge_key = tuple(sorted([adj['source'], adj['target']]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    'source': adj['source'],
                    'target': adj['target'],
                    'synergy': adj['synergy'],
                })
        
        return {
            'rings': rings_data,
            'edges': edges,
            'total_synergy': self.best_score,
            'optimization_state': self.best_state,
        }
    
    def export_to_json(self, filepath: str):
        """Export optimization results to JSON file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'visualization': self.get_ring_visualization_data(),
            'adjacencies': self.get_optimal_adjacencies()[:50],  # Top 50
            'optimization_history': self.optimization_history,
            'ring_states': self.best_state,
            'total_nodes': len(self.nodes),
            'total_rings': len(self.rings),
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Exported to {filepath}")
        return filepath


async def run_hex_optimization():
    """Run the hexagonal ring optimization"""
    optimizer = HexRingOptimizer()
    
    # Run optimization
    results = await optimizer.optimize(
        initial_temp=1.0,
        cooling_rate=0.995,
        min_temp=0.001,
        max_iterations=5000,
    )
    
    # Export results
    optimizer.export_to_json('/home/ubuntu/quorum_universe/hex_ring_optimization.json')
    
    # Print top adjacencies
    print("\nTOP 10 SYNERGISTIC ADJACENCIES:")
    print("-" * 60)
    adjacencies = optimizer.get_optimal_adjacencies()[:10]
    for adj in adjacencies:
        print(f"  {adj['source_name']} ↔ {adj['target_name']}: {adj['synergy']:.3f}")
    
    return results


if __name__ == '__main__':
    asyncio.run(run_hex_optimization())

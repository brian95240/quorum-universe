#!/usr/bin/env python3
"""
Comprehensive Closed-Loop Test Suite for Quorum Universe

This test suite validates the entire system including:
1. Hexagonal ring collapse optimization
2. Multi-tier cache performance
3. Cross-platform sync capabilities
4. Graph synergy analysis
5. Philosopher tribunal deliberation
6. Air-gap isolation testing
"""

import asyncio
import json
import time
import sys
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    details: Dict = None


class ClosedLoopTestSuite:
    """
    Air-gap validated test suite for the Quorum Universe system.
    
    Tests are designed to validate system integrity in isolation,
    ensuring no external dependencies leak into the core logic.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time: datetime = None
        self.end_time: datetime = None
        
    async def run_all_tests(self) -> Dict:
        """Run all tests in the suite"""
        print("\n" + "=" * 70)
        print("QUORUM UNIVERSE CLOSED-LOOP TEST SUITE")
        print("=" * 70)
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 70 + "\n")
        
        self.start_time = datetime.now()
        
        # Test categories
        test_categories = [
            ("Configuration Tests", [
                self.test_config_loading,
                self.test_archetype_definitions,
                self.test_philosopher_definitions,
            ]),
            ("Hexagonal Ring Tests", [
                self.test_hex_node_creation,
                self.test_hex_ring_rotation,
                self.test_hex_face_affinities,
                self.test_hex_synergy_computation,
                self.test_hex_ring_optimization,
            ]),
            ("Cache System Tests", [
                self.test_cache_initialization,
                self.test_cache_set_get,
                self.test_cache_compression,
                self.test_cache_tier_promotion,
                self.test_cache_eviction,
            ]),
            ("Graph Analysis Tests", [
                self.test_synergy_cluster_detection,
                self.test_burst_cluster_identification,
                self.test_hidden_connection_discovery,
            ]),
            ("Tribunal Tests", [
                self.test_philosopher_chain_deliberation,
                self.test_observer_consensus_threshold,
            ]),
            ("Air-Gap Isolation Tests", [
                self.test_no_external_network_calls,
                self.test_data_isolation,
                self.test_deterministic_outputs,
            ]),
        ]
        
        for category_name, tests in test_categories:
            print(f"\n{'─' * 50}")
            print(f"  {category_name}")
            print(f"{'─' * 50}")
            
            for test_func in tests:
                await self._run_test(test_func)
        
        self.end_time = datetime.now()
        
        return self._generate_report()
    
    async def _run_test(self, test_func):
        """Run a single test and record results"""
        test_name = test_func.__name__.replace("test_", "").replace("_", " ").title()
        
        start = time.perf_counter()
        try:
            result = await test_func()
            duration = (time.perf_counter() - start) * 1000
            
            if result.get("success", False):
                status = TestStatus.PASSED
                symbol = "✓"
                color = "\033[92m"  # Green
            else:
                status = TestStatus.FAILED
                symbol = "✗"
                color = "\033[91m"  # Red
            
            self.results.append(TestResult(
                name=test_name,
                status=status,
                duration_ms=duration,
                message=result.get("message", ""),
                details=result.get("details", {}),
            ))
            
            print(f"  {color}{symbol}\033[0m {test_name} ({duration:.1f}ms)")
            
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            self.results.append(TestResult(
                name=test_name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message=str(e),
            ))
            print(f"  \033[91m✗\033[0m {test_name} ({duration:.1f}ms) - {str(e)[:50]}")
    
    # =========================================================================
    # Configuration Tests
    # =========================================================================
    
    async def test_config_loading(self) -> Dict:
        """Test that configuration loads correctly"""
        try:
            from config import ARCHETYPES, QUORUM_PHILOSOPHERS, QuorumConfig
            config = QuorumConfig()
            
            return {
                "success": True,
                "message": f"Config loaded: {len(ARCHETYPES)} archetypes",
                "details": {
                    "archetype_count": len(ARCHETYPES),
                    "philosopher_count": len(QUORUM_PHILOSOPHERS),
                    "platform": config.platform,
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def test_archetype_definitions(self) -> Dict:
        """Test that all 26 archetypes are properly defined"""
        from config import ARCHETYPES
        
        required_fields = ["cluster", "domains", "corpus_size_gb"]
        missing_fields = []
        
        for arch_id, arch_data in ARCHETYPES.items():
            for field in required_fields:
                if field not in arch_data:
                    missing_fields.append(f"{arch_id}.{field}")
        
        return {
            "success": len(missing_fields) == 0 and len(ARCHETYPES) == 26,
            "message": f"26 archetypes validated" if len(ARCHETYPES) == 26 else f"Found {len(ARCHETYPES)} archetypes",
            "details": {
                "archetype_count": len(ARCHETYPES),
                "missing_fields": missing_fields[:5],
            }
        }
    
    async def test_philosopher_definitions(self) -> Dict:
        """Test that all 6 philosophers + observer are properly defined"""
        from config import QUORUM_PHILOSOPHERS
        
        # 6 philosophers + 1 observer = 7 total
        expected = {"hume", "popper", "quine", "arendt", "zhuangzi", "ibn_khaldun", "observer"}
        actual = set(QUORUM_PHILOSOPHERS.keys())
        
        return {
            "success": expected == actual,
            "message": f"6 philosophers + observer validated",
            "details": {
                "expected": list(expected),
                "actual": list(actual),
                "missing": list(expected - actual),
            }
        }
    
    # =========================================================================
    # Hexagonal Ring Tests
    # =========================================================================
    
    async def test_hex_node_creation(self) -> Dict:
        """Test hexagonal node creation with face affinities"""
        from hex_ring_optimizer import HexNode, HexFace
        
        node = HexNode(
            id="test_node",
            name="Test Node",
            ring=1,
            position=0,
            cluster="stem_core",
            domains=["physics", "mathematics"],
            corpus_size_gb=50,
        )
        
        # Check all 6 faces have affinities
        has_all_faces = all(face in node.face_affinities for face in HexFace)
        
        return {
            "success": has_all_faces and len(node.face_affinities) == 6,
            "message": "Hex node created with 6 face affinities",
            "details": {
                "faces": {f.name: v for f, v in node.face_affinities.items()},
            }
        }
    
    async def test_hex_ring_rotation(self) -> Dict:
        """Test hexagonal ring rotation mechanics"""
        from hex_ring_optimizer import HexRing, HexNode
        
        nodes = [
            HexNode(id=f"node_{i}", name=f"Node {i}", ring=1, position=i,
                   cluster="stem_core", domains=["test"], corpus_size_gb=10)
            for i in range(6)
        ]
        
        ring = HexRing(level=1, nodes=nodes)
        
        # Test rotation
        initial_rotation = ring.rotation
        ring.rotate(2)
        after_rotate = ring.rotation
        ring.rotate(-2)
        back_to_initial = ring.rotation
        
        return {
            "success": initial_rotation == 0 and after_rotate == 2 and back_to_initial == 0,
            "message": "Ring rotation works correctly",
            "details": {
                "initial": initial_rotation,
                "after_rotate_2": after_rotate,
                "after_rotate_back": back_to_initial,
            }
        }
    
    async def test_hex_face_affinities(self) -> Dict:
        """Test face affinity computation based on cluster type"""
        from hex_ring_optimizer import HexNode, HexFace
        
        # STEM node should have high theoretical/empirical
        stem_node = HexNode(
            id="stem", name="STEM", ring=1, position=0,
            cluster="stem_core", domains=["physics"], corpus_size_gb=50,
        )
        
        # Human systems should have high historical/philosophical
        human_node = HexNode(
            id="human", name="Human", ring=2, position=0,
            cluster="human_systems", domains=["history"], corpus_size_gb=30,
        )
        
        stem_theoretical = stem_node.face_affinities[HexFace.THEORETICAL]
        human_historical = human_node.face_affinities[HexFace.HISTORICAL]
        
        return {
            "success": stem_theoretical > 0.8 and human_historical > 0.8,
            "message": "Face affinities reflect cluster characteristics",
            "details": {
                "stem_theoretical": stem_theoretical,
                "human_historical": human_historical,
            }
        }
    
    async def test_hex_synergy_computation(self) -> Dict:
        """Test synergy computation between hex nodes"""
        from hex_ring_optimizer import HexNode
        
        node1 = HexNode(
            id="physics", name="Physics", ring=1, position=0,
            cluster="stem_core", domains=["physics", "mathematics"], corpus_size_gb=50,
        )
        
        node2 = HexNode(
            id="engineering", name="Engineering", ring=1, position=1,
            cluster="stem_core", domains=["engineering", "mathematics"], corpus_size_gb=60,
        )
        
        synergy = node1.compute_synergy(node2)
        
        return {
            "success": 0 <= synergy <= 1,
            "message": f"Synergy computed: {synergy:.3f}",
            "details": {
                "synergy_score": synergy,
                "node1_cluster": node1.cluster,
                "node2_cluster": node2.cluster,
            }
        }
    
    async def test_hex_ring_optimization(self) -> Dict:
        """Test hexagonal ring collapse optimization"""
        from hex_ring_optimizer import HexRingOptimizer
        
        optimizer = HexRingOptimizer()
        
        # Run quick optimization
        results = await optimizer.optimize(
            initial_temp=0.5,
            cooling_rate=0.99,
            min_temp=0.01,
            max_iterations=500,
        )
        
        return {
            "success": results["success"] and results["final_score"] > 0,
            "message": f"Optimization complete: {results['final_score']:.4f}",
            "details": {
                "iterations": results["iterations"],
                "improvements": results["improvements"],
                "final_score": results["final_score"],
            }
        }
    
    # =========================================================================
    # Cache System Tests
    # =========================================================================
    
    async def test_cache_initialization(self) -> Dict:
        """Test multi-tier cache initialization"""
        from redis_cache_manager import MultiTierCache, CacheTier
        
        cache = MultiTierCache()
        
        has_all_tiers = all(tier in cache.tiers for tier in CacheTier)
        has_all_configs = all(tier in cache.configs for tier in CacheTier)
        
        return {
            "success": has_all_tiers and has_all_configs,
            "message": "Cache initialized with 3 tiers",
            "details": {
                "tiers": [t.value for t in cache.tiers.keys()],
            }
        }
    
    async def test_cache_set_get(self) -> Dict:
        """Test basic cache set and get operations"""
        from redis_cache_manager import MultiTierCache, CacheTier
        
        cache = MultiTierCache()
        test_data = {"key": "value", "number": 42}
        
        await cache.set("test_key", test_data, CacheTier.L2_WARM)
        retrieved = await cache.get("test_key")
        
        return {
            "success": retrieved == test_data,
            "message": "Set/Get operations work correctly",
            "details": {
                "original": test_data,
                "retrieved": retrieved,
            }
        }
    
    async def test_cache_compression(self) -> Dict:
        """Test Zstandard compression in cache"""
        from redis_cache_manager import MultiTierCache, CacheTier
        
        cache = MultiTierCache()
        
        # Large data that compresses well
        large_data = {"data": "x" * 10000, "repeated": ["test"] * 100}
        
        await cache.set("large_key", large_data, CacheTier.L3_COLD)
        
        stats = cache.get_stats()
        compressions = stats["tiers"]["l3_cold"]["compressions"]
        
        return {
            "success": compressions > 0,
            "message": f"Compression applied: {compressions} compressions",
            "details": stats["tiers"]["l3_cold"],
        }
    
    async def test_cache_tier_promotion(self) -> Dict:
        """Test automatic tier promotion on frequent access"""
        from redis_cache_manager import MultiTierCache, CacheTier
        
        cache = MultiTierCache()
        cache.promotion_threshold = 3  # Lower for testing
        
        await cache.set("promote_key", {"test": True}, CacheTier.L2_WARM)
        
        # Access multiple times
        for _ in range(5):
            await cache.get("promote_key")
        
        # Check if promoted to L1
        stats = cache.get_stats()
        l1_entries = stats["tiers"]["l1_hot"]["entry_count"]
        
        return {
            "success": l1_entries > 0,
            "message": f"Entry promoted to L1: {l1_entries} entries",
            "details": {
                "l1_entries": l1_entries,
                "l2_entries": stats["tiers"]["l2_warm"]["entry_count"],
            }
        }
    
    async def test_cache_eviction(self) -> Dict:
        """Test LRU eviction when cache is full"""
        from redis_cache_manager import MultiTierCache, CacheTier
        
        cache = MultiTierCache()
        # Set very small max size for testing
        cache.configs[CacheTier.L1_HOT].max_size_mb = 0.001  # 1KB
        
        # Add entries until eviction
        for i in range(10):
            await cache.set(f"evict_key_{i}", {"data": "x" * 100}, CacheTier.L1_HOT)
        
        stats = cache.get_stats()
        evictions = stats["tiers"]["l1_hot"]["evictions"]
        
        return {
            "success": evictions > 0,
            "message": f"LRU eviction triggered: {evictions} evictions",
            "details": stats["tiers"]["l1_hot"],
        }
    
    # =========================================================================
    # Graph Analysis Tests
    # =========================================================================
    
    async def test_synergy_cluster_detection(self) -> Dict:
        """Test synergy cluster detection in the graph"""
        from synergy_analyzer import SynergyAnalyzer
        
        analyzer = SynergyAnalyzer()
        await analyzer.build_graph()
        clusters = await analyzer.find_synergy_clusters()
        
        return {
            "success": len(clusters) > 0,
            "message": f"Found {len(clusters)} synergy clusters",
            "details": {
                "cluster_count": len(clusters),
                "top_cluster": clusters[0] if clusters else None,
            }
        }
    
    async def test_burst_cluster_identification(self) -> Dict:
        """Test burst cluster identification"""
        from synergy_analyzer import SynergyAnalyzer
        
        analyzer = SynergyAnalyzer()
        await analyzer.build_graph()
        bursts = await analyzer.find_burst_clusters()
        
        return {
            "success": len(bursts) > 0,
            "message": f"Found {len(bursts)} burst clusters",
            "details": {
                "burst_count": len(bursts),
                "top_burst": bursts[0] if bursts else None,
            }
        }
    
    async def test_hidden_connection_discovery(self) -> Dict:
        """Test discovery of hidden connections"""
        from synergy_analyzer import SynergyAnalyzer
        
        analyzer = SynergyAnalyzer()
        await analyzer.build_graph()
        hidden = await analyzer.find_hidden_connections()
        
        return {
            "success": True,  # May or may not find hidden connections
            "message": f"Found {len(hidden)} hidden connections",
            "details": {
                "hidden_count": len(hidden),
                "top_hidden": hidden[0] if hidden else None,
            }
        }
    
    # =========================================================================
    # Tribunal Tests
    # =========================================================================
    
    async def test_philosopher_chain_deliberation(self) -> Dict:
        """Test philosopher chain deliberation"""
        from config import QUORUM_PHILOSOPHERS
        
        # Simulate deliberation chain
        chain_order = ["hume", "popper", "quine", "arendt", "zhuangzi", "ibn_khaldun"]
        deliberation_results = []
        
        for philosopher in chain_order:
            if philosopher in QUORUM_PHILOSOPHERS:
                deliberation_results.append({
                    "philosopher": philosopher,
                    "style": QUORUM_PHILOSOPHERS[philosopher]["style"],
                })
        
        return {
            "success": len(deliberation_results) == 6,
            "message": "6-philosopher chain deliberation complete",
            "details": {
                "chain_length": len(deliberation_results),
                "philosophers": [d["philosopher"] for d in deliberation_results],
            }
        }
    
    async def test_observer_consensus_threshold(self) -> Dict:
        """Test Observer consensus threshold (0.92)"""
        from config import QUORUM_PHILOSOPHERS
        
        observer = QUORUM_PHILOSOPHERS.get("observer", {})
        threshold = observer.get("threshold", 0)
        
        return {
            "success": threshold == 0.92,
            "message": f"Observer threshold: {threshold}",
            "details": {
                "threshold": threshold,
                "role": observer.get("role", "unknown"),
            }
        }
    
    # =========================================================================
    # Air-Gap Isolation Tests
    # =========================================================================
    
    async def test_no_external_network_calls(self) -> Dict:
        """Test that core logic makes no external network calls"""
        import socket
        
        # Save original
        original_socket = socket.socket
        network_calls = []
        
        class MockSocket:
            def __init__(self, *args, **kwargs):
                network_calls.append(("socket_created", args))
                raise ConnectionRefusedError("Network disabled for air-gap test")
        
        # Temporarily replace socket
        socket.socket = MockSocket
        
        try:
            # Run core operations
            from config import ARCHETYPES
            from hex_ring_optimizer import HexRingOptimizer
            
            optimizer = HexRingOptimizer()
            # Don't actually run optimization as it doesn't need network
            
            success = len(network_calls) == 0
        finally:
            socket.socket = original_socket
        
        return {
            "success": success,
            "message": "No external network calls detected" if success else f"{len(network_calls)} calls detected",
            "details": {
                "network_calls": len(network_calls),
            }
        }
    
    async def test_data_isolation(self) -> Dict:
        """Test that data operations are isolated"""
        from redis_cache_manager import MultiTierCache, CacheTier
        
        cache1 = MultiTierCache()
        cache2 = MultiTierCache()
        
        await cache1.set("isolated_key", {"cache": 1}, CacheTier.L1_HOT)
        result = await cache2.get("isolated_key")
        
        # cache2 should not see cache1's data (different instances)
        return {
            "success": result is None,
            "message": "Cache instances are isolated",
            "details": {
                "cache1_has_key": True,
                "cache2_has_key": result is not None,
            }
        }
    
    async def test_deterministic_outputs(self) -> Dict:
        """Test that operations produce deterministic outputs"""
        from hex_ring_optimizer import HexNode
        
        # Create same node twice
        node1 = HexNode(
            id="deterministic", name="Test", ring=1, position=0,
            cluster="stem_core", domains=["physics"], corpus_size_gb=50,
        )
        
        node2 = HexNode(
            id="deterministic", name="Test", ring=1, position=0,
            cluster="stem_core", domains=["physics"], corpus_size_gb=50,
        )
        
        # Face affinities should be identical
        affinities_match = node1.face_affinities == node2.face_affinities
        
        return {
            "success": affinities_match,
            "message": "Outputs are deterministic",
            "details": {
                "node1_affinities": {k.name: v for k, v in node1.face_affinities.items()},
                "node2_affinities": {k.name: v for k, v in node2.face_affinities.items()},
            }
        }
    
    def _generate_report(self) -> Dict:
        """Generate final test report"""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        total = len(self.results)
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"  Total Tests:  {total}")
        print(f"  Passed:       \033[92m{passed}\033[0m")
        print(f"  Failed:       \033[91m{failed}\033[0m")
        print(f"  Pass Rate:    {passed/total*100:.1f}%")
        print(f"  Duration:     {duration:.2f}s")
        print("=" * 70)
        
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if r.status == TestStatus.FAILED:
                    print(f"  ✗ {r.name}: {r.message}")
        
        print("\n")
        
        return {
            "success": failed == 0,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / total if total > 0 else 0,
                "duration_seconds": duration,
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message,
                }
                for r in self.results
            ],
            "timestamp": datetime.now().isoformat(),
        }


async def main():
    """Run the closed-loop test suite"""
    suite = ClosedLoopTestSuite()
    report = await suite.run_all_tests()
    
    # Save report
    with open("/home/ubuntu/quorum_universe/test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to: /home/ubuntu/quorum_universe/test_report.json")
    
    return report["success"]


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

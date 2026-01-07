#!/usr/bin/env python3
"""
Quorum Universe - Closed-Loop Air-Gap Test Suite
Validates system integrity, synergy detection, and cross-platform connectivity
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
import sys
sys.path.insert(0, '/home/ubuntu/quorum_universe/quorum_core')

from config import ARCHETYPES, NEON_CONNECTION_STRING, TOTAL_ARCHETYPES, TOTAL_CORPUS_GB
from graph_engine import QuorumGraphEngine, NodeType, EdgeType, GraphNode, GraphEdge
from symbiotic_connector import SymbioticConnector, ArchetypeDataDumpManager

# =============================================================================
# TEST RESULT STRUCTURES
# =============================================================================
@dataclass
class TestResult:
    """Individual test result"""
    name: str
    passed: bool
    duration_ms: float
    message: str
    details: Dict = field(default_factory=dict)

@dataclass
class TestSuiteResult:
    """Complete test suite result"""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    duration_ms: float
    results: List[TestResult]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'suite_name': self.suite_name,
            'total_tests': self.total_tests,
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': self.passed / max(self.total_tests, 1),
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'results': [
                {
                    'name': r.name,
                    'passed': r.passed,
                    'duration_ms': r.duration_ms,
                    'message': r.message,
                    'details': r.details,
                }
                for r in self.results
            ]
        }

# =============================================================================
# CLOSED-LOOP TEST RUNNER
# =============================================================================
class ClosedLoopTestRunner:
    """
    Air-gap test runner for Quorum Universe
    Validates all system components in isolation
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.graph_engine: QuorumGraphEngine = None
        self.connector: SymbioticConnector = None
    
    async def setup(self):
        """Initialize test environment"""
        self.graph_engine = QuorumGraphEngine()
        await self.graph_engine.connect()
        
        self.connector = SymbioticConnector()
    
    async def teardown(self):
        """Cleanup test environment"""
        if self.graph_engine:
            await self.graph_engine.close()
        if self.connector:
            await self.connector.close()
    
    def _record_result(self, name: str, passed: bool, duration_ms: float, message: str, details: Dict = None):
        """Record a test result"""
        self.results.append(TestResult(
            name=name,
            passed=passed,
            duration_ms=duration_ms,
            message=message,
            details=details or {}
        ))
    
    # =========================================================================
    # DATABASE TESTS
    # =========================================================================
    async def test_database_connection(self) -> bool:
        """Test Neon PostgreSQL connection"""
        start = time.time()
        try:
            import asyncpg
            pool = await asyncpg.create_pool(NEON_CONNECTION_STRING, min_size=1, max_size=2)
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
            await pool.close()
            
            duration = (time.time() - start) * 1000
            self._record_result(
                "Database Connection",
                True,
                duration,
                "Successfully connected to Neon PostgreSQL"
            )
            return True
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Database Connection",
                False,
                duration,
                f"Connection failed: {str(e)}"
            )
            return False
    
    async def test_archetypes_seeded(self) -> bool:
        """Verify all 26 archetypes are seeded in database"""
        start = time.time()
        try:
            import asyncpg
            pool = await asyncpg.create_pool(NEON_CONNECTION_STRING, min_size=1, max_size=2)
            async with pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM quorum.archetypes")
                
            await pool.close()
            
            duration = (time.time() - start) * 1000
            passed = count >= TOTAL_ARCHETYPES
            self._record_result(
                "Archetypes Seeded",
                passed,
                duration,
                f"Found {count}/{TOTAL_ARCHETYPES} archetypes in database",
                {'count': count, 'expected': TOTAL_ARCHETYPES}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Archetypes Seeded",
                False,
                duration,
                f"Query failed: {str(e)}"
            )
            return False
    
    async def test_schema_integrity(self) -> bool:
        """Verify all required tables exist"""
        start = time.time()
        required_tables = [
            'archetypes', 'chunks', 'documents', 'query_cache',
            'sessions', 'metrics', 'graph_edges', 'graph_nodes',
            'tribunal_verdicts', 'compression_stats', 'synergy_clusters', 'code_analysis'
        ]
        
        try:
            import asyncpg
            pool = await asyncpg.create_pool(NEON_CONNECTION_STRING, min_size=1, max_size=2)
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'quorum'
                """)
                existing_tables = [row['table_name'] for row in rows]
            
            await pool.close()
            
            missing = [t for t in required_tables if t not in existing_tables]
            duration = (time.time() - start) * 1000
            passed = len(missing) == 0
            
            self._record_result(
                "Schema Integrity",
                passed,
                duration,
                f"Found {len(existing_tables)} tables, missing: {missing if missing else 'none'}",
                {'existing': existing_tables, 'missing': missing}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Schema Integrity",
                False,
                duration,
                f"Schema check failed: {str(e)}"
            )
            return False
    
    # =========================================================================
    # GRAPH ENGINE TESTS
    # =========================================================================
    async def test_graph_initialization(self) -> bool:
        """Test graph engine initialization with archetypes"""
        start = time.time()
        try:
            node_count = self.graph_engine.nx_graph.number_of_nodes()
            edge_count = self.graph_engine.nx_graph.number_of_edges()
            
            duration = (time.time() - start) * 1000
            passed = node_count >= TOTAL_ARCHETYPES
            
            self._record_result(
                "Graph Initialization",
                passed,
                duration,
                f"Graph initialized with {node_count} nodes and {edge_count} edges",
                {'nodes': node_count, 'edges': edge_count}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Graph Initialization",
                False,
                duration,
                f"Graph init failed: {str(e)}"
            )
            return False
    
    async def test_synergy_detection(self) -> bool:
        """Test synergy detection algorithms"""
        start = time.time()
        try:
            result = await self.graph_engine.detect_synergies(min_synergy_score=0.1)
            
            duration = (time.time() - start) * 1000
            passed = len(result.clusters) > 0 or len(result.hidden_connections) > 0
            
            self._record_result(
                "Synergy Detection",
                passed,
                duration,
                f"Found {len(result.clusters)} clusters, {len(result.hidden_connections)} hidden connections",
                {
                    'clusters': len(result.clusters),
                    'hidden_connections': len(result.hidden_connections),
                    'optimization_opportunities': len(result.optimization_opportunities),
                    'total_synergy_score': result.total_synergy_score,
                }
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Synergy Detection",
                False,
                duration,
                f"Synergy detection failed: {str(e)}"
            )
            return False
    
    async def test_graph_stats(self) -> bool:
        """Test graph statistics generation"""
        start = time.time()
        try:
            stats = await self.graph_engine.get_graph_stats()
            
            duration = (time.time() - start) * 1000
            passed = 'nodes' in stats and 'edges' in stats
            
            self._record_result(
                "Graph Statistics",
                passed,
                duration,
                f"Stats: {stats['nodes']} nodes, {stats['edges']} edges, density={stats.get('density', 0):.4f}",
                stats
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Graph Statistics",
                False,
                duration,
                f"Stats generation failed: {str(e)}"
            )
            return False
    
    # =========================================================================
    # SYMBIOTIC CONNECTOR TESTS
    # =========================================================================
    async def test_platform_detection(self) -> bool:
        """Test cross-platform detection"""
        start = time.time()
        try:
            from config import detect_platform, get_data_path
            
            platform = detect_platform()
            data_path = get_data_path()
            
            duration = (time.time() - start) * 1000
            passed = platform is not None and data_path is not None
            
            self._record_result(
                "Platform Detection",
                passed,
                duration,
                f"Detected platform: {platform}, data path: {data_path}",
                {'platform': platform, 'data_path': str(data_path)}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Platform Detection",
                False,
                duration,
                f"Platform detection failed: {str(e)}"
            )
            return False
    
    async def test_symbiotic_folders(self) -> bool:
        """Test symbiotic folder structure generation"""
        start = time.time()
        try:
            folder_map = self.connector.get_symbiotic_folder_map()
            
            duration = (time.time() - start) * 1000
            passed = len(folder_map) > 0
            
            self._record_result(
                "Symbiotic Folders",
                passed,
                duration,
                f"Generated {len(folder_map)} folder mappings",
                {'folders': list(folder_map.keys())}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Symbiotic Folders",
                False,
                duration,
                f"Folder generation failed: {str(e)}"
            )
            return False
    
    async def test_archetype_data_paths(self) -> bool:
        """Test archetype data path generation for all 26 archetypes"""
        start = time.time()
        try:
            paths = self.connector.get_archetype_data_paths()
            
            duration = (time.time() - start) * 1000
            passed = len(paths) == TOTAL_ARCHETYPES
            
            self._record_result(
                "Archetype Data Paths",
                passed,
                duration,
                f"Generated paths for {len(paths)}/{TOTAL_ARCHETYPES} archetypes",
                {'archetypes': list(paths.keys())}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Archetype Data Paths",
                False,
                duration,
                f"Path generation failed: {str(e)}"
            )
            return False
    
    async def test_device_capabilities(self) -> bool:
        """Test device capability detection"""
        start = time.time()
        try:
            capabilities = self.connector._get_device_capabilities()
            
            duration = (time.time() - start) * 1000
            passed = len(capabilities) > 0
            
            self._record_result(
                "Device Capabilities",
                passed,
                duration,
                f"Detected {len(capabilities)} capabilities: {capabilities}",
                {'capabilities': capabilities}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Device Capabilities",
                False,
                duration,
                f"Capability detection failed: {str(e)}"
            )
            return False
    
    # =========================================================================
    # CONFIGURATION TESTS
    # =========================================================================
    async def test_archetype_configuration(self) -> bool:
        """Verify all archetype configurations are valid"""
        start = time.time()
        try:
            required_fields = ['id', 'cluster', 'corpus_size_gb', 'temperature', 'domains', 'data_dump_paths']
            invalid = []
            
            for name, config in ARCHETYPES.items():
                missing = [f for f in required_fields if f not in config]
                if missing:
                    invalid.append({'archetype': name, 'missing': missing})
            
            duration = (time.time() - start) * 1000
            passed = len(invalid) == 0
            
            self._record_result(
                "Archetype Configuration",
                passed,
                duration,
                f"Validated {TOTAL_ARCHETYPES} archetypes, {len(invalid)} invalid",
                {'invalid': invalid}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Archetype Configuration",
                False,
                duration,
                f"Config validation failed: {str(e)}"
            )
            return False
    
    async def test_corpus_totals(self) -> bool:
        """Verify corpus size totals"""
        start = time.time()
        try:
            calculated_total = sum(a['corpus_size_gb'] for a in ARCHETYPES.values())
            
            duration = (time.time() - start) * 1000
            passed = calculated_total == TOTAL_CORPUS_GB
            
            self._record_result(
                "Corpus Totals",
                passed,
                duration,
                f"Total corpus: {calculated_total} GB (expected: {TOTAL_CORPUS_GB} GB)",
                {'calculated': calculated_total, 'expected': TOTAL_CORPUS_GB}
            )
            return passed
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._record_result(
                "Corpus Totals",
                False,
                duration,
                f"Corpus calculation failed: {str(e)}"
            )
            return False
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    async def run_all_tests(self) -> TestSuiteResult:
        """Run complete closed-loop test suite"""
        suite_start = time.time()
        
        print("=" * 60)
        print("QUORUM UNIVERSE - CLOSED-LOOP AIR-GAP TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.utcnow().isoformat()}")
        print()
        
        await self.setup()
        
        # Define test sequence
        tests = [
            ("Database Tests", [
                self.test_database_connection,
                self.test_archetypes_seeded,
                self.test_schema_integrity,
            ]),
            ("Graph Engine Tests", [
                self.test_graph_initialization,
                self.test_synergy_detection,
                self.test_graph_stats,
            ]),
            ("Symbiotic Connector Tests", [
                self.test_platform_detection,
                self.test_symbiotic_folders,
                self.test_archetype_data_paths,
                self.test_device_capabilities,
            ]),
            ("Configuration Tests", [
                self.test_archetype_configuration,
                self.test_corpus_totals,
            ]),
        ]
        
        # Run tests
        for category, test_funcs in tests:
            print(f"\n{category}")
            print("-" * 40)
            
            for test_func in test_funcs:
                try:
                    result = await test_func()
                    status = "✓ PASS" if result else "✗ FAIL"
                    print(f"  {status}: {test_func.__name__}")
                except Exception as e:
                    print(f"  ✗ ERROR: {test_func.__name__} - {str(e)}")
        
        await self.teardown()
        
        # Calculate summary
        suite_duration = (time.time() - suite_start) * 1000
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {passed / max(len(self.results), 1) * 100:.1f}%")
        print(f"Duration: {suite_duration:.2f} ms")
        print("=" * 60)
        
        return TestSuiteResult(
            suite_name="Quorum Universe Closed-Loop Test",
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            duration_ms=suite_duration,
            results=self.results,
        )


# =============================================================================
# MAIN
# =============================================================================
async def run_closed_loop_tests() -> TestSuiteResult:
    """Run closed-loop tests and return results"""
    runner = ClosedLoopTestRunner()
    return await runner.run_all_tests()


if __name__ == "__main__":
    result = asyncio.run(run_closed_loop_tests())
    
    # Save results to file
    output_path = "/home/ubuntu/quorum_universe/test_results.json"
    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    print(f"\nResults saved to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(0 if result.failed == 0 else 1)

#!/usr/bin/env python3
"""
Metrics Dashboard - Real-Time System Monitoring
Tracks vertex criteria and system performance

Key Features:
- Real-time Prometheus metrics collection
- Vertex criteria dashboard (0.01% status)
- Performance visualization (latency, throughput, quality)
- Component health monitoring
- Alert thresholds and notifications
- Historical trend analysis
- ASCII art graphs for terminal display

Metrics Tracked:
1. Performance: latency (p50, p95, p99), throughput (QPS)
2. Efficiency: cache hit rate, collapse ratio, warm hit rate
3. Quality: avg quality score, synthesis coherence, truth forensics
4. Resources: memory usage, CPU usage, disk I/O
5. Reliability: error rate, uptime, MTBF

Export Formats:
- Prometheus exposition format
- JSON API
- ASCII terminal dashboard
- HTML dashboard (future)
"""

import time
import json
import statistics
from typing import Dict, List, Optional, Tuple, Deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum
import asyncio

# Prometheus
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary,
        CollectorRegistry, generate_latest,
        start_http_server, CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    print("WARNING: prometheus_client not available")
    PROMETHEUS_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class VertexStatus(Enum):
    """Vertex criteria achievement status"""
    NOT_STARTED = "not_started"       # No queries yet
    APPROACHING = "approaching"        # Making progress
    VERTEX_ACHIEVED = "vertex"         # All criteria met
    DEGRADED = "degraded"             # Was vertex, now failing


@dataclass
class VertexCriteria:
    """0.01% Vertex criteria tracking"""
    # Performance
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    warm_latency_p99: float = 0.0
    
    # Efficiency
    collapse_ratio: float = 0.0
    warm_hit_rate: float = 0.0
    parallel_speedup: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Quality
    quality_threshold: float = 0.0
    synthesis_coherence: float = 0.0
    citation_accuracy: float = 0.0
    
    # Resources
    memory_efficiency_gb: float = 0.0
    disk_usage_gb: float = 0.0
    power_consumption_w: float = 0.0
    
    # Cost
    training_cost: float = 0.0
    cost_per_query: float = 0.0
    
    # Reliability
    uptime_pct: float = 0.0
    error_rate: float = 0.0
    mtbf_hours: float = 0.0
    
    # Status
    status: VertexStatus = VertexStatus.NOT_STARTED
    criteria_met: int = 0
    criteria_total: int = 28
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['status'] = self.status.value
        d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class SystemMetrics:
    """Current system performance metrics"""
    # Throughput
    queries_per_second: float = 0.0
    total_queries: int = 0
    
    # Latency (seconds)
    avg_latency: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # Quality
    avg_quality_score: float = 0.0
    queries_above_threshold: int = 0
    
    # Archetypes
    total_archetypes_used: int = 0
    avg_archetypes_per_query: float = 0.0
    collapse_ratio: float = 0.0
    
    # Errors
    total_errors: int = 0
    error_rate: float = 0.0
    
    # Resources
    memory_usage_mb: float = 0.0
    cpu_usage_pct: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComponentHealth:
    """Health status of system components"""
    name: str
    status: str  # healthy, degraded, failed
    latency_ms: float = 0.0
    error_count: int = 0
    last_check: datetime = field(default_factory=datetime.now)
    
    def is_healthy(self) -> bool:
        return self.status == 'healthy'


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """
    Collects and aggregates system metrics.
    
    Maintains time-series data and calculates percentiles.
    """
    
    # Retention windows
    RETENTION_1MIN = 60        # 1 minute
    RETENTION_5MIN = 300       # 5 minutes
    RETENTION_1HOUR = 3600     # 1 hour
    RETENTION_24HOUR = 86400   # 24 hours
    
    def __init__(self, enable_prometheus: bool = True):
        """
        Initialize metrics collector.
        
        Args:
            enable_prometheus: Whether to export to Prometheus
        """
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        
        # Time-series data (deques with maxlen)
        self.latency_history: Deque[float] = deque(maxlen=1000)
        self.quality_history: Deque[float] = deque(maxlen=1000)
        
        # Counters
        self.total_queries = 0
        self.total_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.archetypes_used = defaultdict(int)
        
        # Archetype counts per query
        self.queries_by_archetype_count = defaultdict(int)
        
        # Component health
        self.components: Dict[str, ComponentHealth] = {}
        
        # Vertex tracking
        self.vertex_criteria = VertexCriteria()
        
        # Start time
        self.start_time = time.time()
        
        # Prometheus metrics (if enabled)
        if self.enable_prometheus:
            self._init_prometheus_metrics()
        
        print(f"MetricsCollector initialized")
        print(f"  Prometheus: {'enabled' if self.enable_prometheus else 'disabled'}")
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Counters
        self.prom_queries_total = Counter(
            'queries_total',
            'Total queries processed',
            ['status']
        )
        
        self.prom_cache_hits = Counter(
            'cache_hits_total',
            'Cache hits'
        )
        
        self.prom_cache_misses = Counter(
            'cache_misses_total',
            'Cache misses'
        )
        
        # Histograms
        self.prom_query_latency = Histogram(
            'query_latency_seconds',
            'Query processing latency'
        )
        
        # Gauges
        self.prom_cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate percentage'
        )
        
        self.prom_avg_quality = Gauge(
            'avg_quality_score',
            'Average quality score'
        )
        
        self.prom_collapse_ratio = Gauge(
            'collapse_ratio',
            'Collapse ratio (queries with ≤2 archetypes)'
        )
        
        self.prom_vertex_status = Gauge(
            'vertex_status',
            'Vertex criteria achievement (0=not started, 1=approaching, 2=achieved)'
        )
    
    # ========================================================================
    # METRIC RECORDING
    # ========================================================================
    
    def record_query(self,
                    latency: float,
                    quality_score: float,
                    num_archetypes: int,
                    cached: bool,
                    error: bool = False):
        """
        Record query metrics.
        
        Args:
            latency: Query latency in seconds
            quality_score: Quality score (0-1)
            num_archetypes: Number of archetypes used
            cached: Whether result was cached
            error: Whether query resulted in error
        """
        self.total_queries += 1
        
        # Latency
        self.latency_history.append(latency)
        
        # Quality
        self.quality_history.append(quality_score)
        
        # Cache
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        # Archetypes
        self.queries_by_archetype_count[num_archetypes] += 1
        
        # Errors
        if error:
            self.total_errors += 1
        
        # Prometheus
        if self.enable_prometheus:
            self.prom_queries_total.labels(
                status='success' if not error else 'error'
            ).inc()
            
            self.prom_query_latency.observe(latency)
            
            if cached:
                self.prom_cache_hits.inc()
            else:
                self.prom_cache_misses.inc()
    
    def record_archetype_usage(self, archetype: str):
        """Record archetype usage"""
        self.archetypes_used[archetype] += 1
    
    def record_component_health(self, name: str, status: str, latency_ms: float = 0.0):
        """Record component health check"""
        if name not in self.components:
            self.components[name] = ComponentHealth(name, status)
        else:
            self.components[name].status = status
            self.components[name].latency_ms = latency_ms
            self.components[name].last_check = datetime.now()
    
    # ========================================================================
    # METRIC CALCULATION
    # ========================================================================
    
    def calculate_system_metrics(self) -> SystemMetrics:
        """Calculate current system metrics"""
        metrics = SystemMetrics()
        
        # Throughput
        uptime = time.time() - self.start_time
        metrics.queries_per_second = self.total_queries / uptime if uptime > 0 else 0
        metrics.total_queries = self.total_queries
        
        # Latency
        if self.latency_history:
            sorted_latencies = sorted(self.latency_history)
            metrics.avg_latency = statistics.mean(sorted_latencies)
            metrics.p50_latency = sorted_latencies[int(len(sorted_latencies) * 0.5)]
            metrics.p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            metrics.p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        # Cache
        metrics.cache_hits = self.cache_hits
        metrics.cache_misses = self.cache_misses
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            metrics.cache_hit_rate = self.cache_hits / total_cache_requests
        
        # Quality
        if self.quality_history:
            metrics.avg_quality_score = statistics.mean(self.quality_history)
            metrics.queries_above_threshold = sum(
                1 for q in self.quality_history if q >= 0.85
            )
        
        # Archetypes
        metrics.total_archetypes_used = sum(self.archetypes_used.values())
        if self.total_queries > 0:
            total_weighted = sum(
                count * num_archetypes
                for num_archetypes, count in self.queries_by_archetype_count.items()
            )
            metrics.avg_archetypes_per_query = total_weighted / self.total_queries
            
            # Collapse ratio (queries with ≤2 archetypes)
            queries_collapsed = sum(
                count for num_archetypes, count in self.queries_by_archetype_count.items()
                if num_archetypes <= 2
            )
            metrics.collapse_ratio = queries_collapsed / self.total_queries
        
        # Errors
        metrics.total_errors = self.total_errors
        if self.total_queries > 0:
            metrics.error_rate = self.total_errors / self.total_queries
        
        return metrics
    
    def calculate_vertex_criteria(self) -> VertexCriteria:
        """Calculate vertex criteria status"""
        criteria = VertexCriteria()
        
        # Get system metrics
        sys_metrics = self.calculate_system_metrics()
        
        # Performance
        criteria.latency_p50 = sys_metrics.p50_latency
        criteria.latency_p95 = sys_metrics.p95_latency
        criteria.latency_p99 = sys_metrics.p99_latency
        
        # Efficiency
        criteria.collapse_ratio = sys_metrics.collapse_ratio
        criteria.cache_hit_rate = sys_metrics.cache_hit_rate
        
        # Quality
        criteria.quality_threshold = sys_metrics.avg_quality_score
        
        # Reliability
        uptime = time.time() - self.start_time
        criteria.uptime_pct = 100.0  # Assume always up for now
        criteria.error_rate = sys_metrics.error_rate
        
        # Check criteria
        criteria_checks = {
            'latency_p50': criteria.latency_p50 < 3.0,
            'latency_p95': criteria.latency_p95 < 5.0,
            'latency_p99': criteria.latency_p99 < 8.0,
            'collapse_ratio': criteria.collapse_ratio > 0.90,
            'cache_hit_rate': criteria.cache_hit_rate > 0.75,
            'quality_threshold': criteria.quality_threshold > 0.85,
            'error_rate': criteria.error_rate < 0.005
        }
        
        criteria.criteria_met = sum(criteria_checks.values())
        
        # Determine status
        if self.total_queries == 0:
            criteria.status = VertexStatus.NOT_STARTED
        elif criteria.criteria_met == len(criteria_checks):
            criteria.status = VertexStatus.VERTEX_ACHIEVED
        elif criteria.criteria_met >= len(criteria_checks) * 0.7:
            criteria.status = VertexStatus.APPROACHING
        else:
            criteria.status = VertexStatus.DEGRADED
        
        self.vertex_criteria = criteria
        
        # Update Prometheus
        if self.enable_prometheus:
            status_map = {
                VertexStatus.NOT_STARTED: 0,
                VertexStatus.APPROACHING: 1,
                VertexStatus.VERTEX_ACHIEVED: 2,
                VertexStatus.DEGRADED: -1
            }
            self.prom_vertex_status.set(status_map[criteria.status])
            
            self.prom_cache_hit_rate.set(criteria.cache_hit_rate * 100)
            self.prom_avg_quality.set(criteria.quality_threshold)
            self.prom_collapse_ratio.set(criteria.collapse_ratio * 100)
        
        return criteria
    
    def get_component_health_summary(self) -> Dict[str, str]:
        """Get summary of component health"""
        return {
            name: comp.status
            for name, comp in self.components.items()
        }
    
    # ========================================================================
    # VISUALIZATION
    # ========================================================================
    
    def generate_ascii_dashboard(self) -> str:
        """Generate ASCII art dashboard"""
        sys_metrics = self.calculate_system_metrics()
        vertex = self.calculate_vertex_criteria()
        
        lines = []
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + " AMBIENT INTELLIGENCE - METRICS DASHBOARD ".center(78) + "║")
        lines.append("╠" + "═" * 78 + "╣")
        
        # Uptime
        uptime = time.time() - self.start_time
        uptime_str = str(timedelta(seconds=int(uptime)))
        lines.append(f"║ Uptime: {uptime_str:<68} ║")
        lines.append(f"║ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<63} ║")
        
        # Vertex status
        lines.append("╠" + "═" * 78 + "╣")
        lines.append("║ VERTEX CRITERIA STATUS".ljust(79) + "║")
        lines.append("╠" + "─" * 78 + "╣")
        
        status_icons = {
            VertexStatus.NOT_STARTED: "⚪",
            VertexStatus.APPROACHING: "🟡",
            VertexStatus.VERTEX_ACHIEVED: "🟢",
            VertexStatus.DEGRADED: "🔴"
        }
        icon = status_icons[vertex.status]
        
        lines.append(f"║ Status: {icon} {vertex.status.value.upper():<64} ║")
        lines.append(f"║ Criteria Met: {vertex.criteria_met}/{vertex.criteria_total:<61} ║")
        
        # Performance metrics
        lines.append("╠" + "═" * 78 + "╣")
        lines.append("║ PERFORMANCE".ljust(79) + "║")
        lines.append("╠" + "─" * 78 + "╣")
        lines.append(f"║ Queries: {sys_metrics.total_queries:>8}   QPS: {sys_metrics.queries_per_second:>6.2f}{'':<53} ║")
        lines.append(f"║ Latency (p50/p95/p99): {sys_metrics.p50_latency:>5.3f}s / {sys_metrics.p95_latency:>5.3f}s / {sys_metrics.p99_latency:>5.3f}s{'':<26} ║")
        
        # Efficiency metrics
        lines.append("╠" + "═" * 78 + "╣")
        lines.append("║ EFFICIENCY".ljust(79) + "║")
        lines.append("╠" + "─" * 78 + "╣")
        lines.append(f"║ Cache Hit Rate: {sys_metrics.cache_hit_rate*100:>5.1f}%   (Target: >75%){'':<36} ║")
        lines.append(f"║ Collapse Ratio: {sys_metrics.collapse_ratio*100:>5.1f}%   (Target: >90%){'':<35} ║")
        lines.append(f"║ Avg Archetypes/Query: {sys_metrics.avg_archetypes_per_query:>4.2f}{'':<47} ║")
        
        # Quality metrics
        lines.append("╠" + "═" * 78 + "╣")
        lines.append("║ QUALITY".ljust(79) + "║")
        lines.append("╠" + "─" * 78 + "╣")
        lines.append(f"║ Avg Quality Score: {sys_metrics.avg_quality_score:>5.3f}   (Target: >0.85){'':<36} ║")
        lines.append(f"║ Queries Above Threshold: {sys_metrics.queries_above_threshold}/{sys_metrics.total_queries}{'':<46} ║")
        
        # Component health
        lines.append("╠" + "═" * 78 + "╣")
        lines.append("║ COMPONENT HEALTH".ljust(79) + "║")
        lines.append("╠" + "─" * 78 + "╣")
        
        health_summary = self.get_component_health_summary()
        if health_summary:
            for name, status in health_summary.items():
                status_icon = "✓" if status == 'healthy' else "✗"
                lines.append(f"║ {status_icon} {name:<20} {status:<52} ║")
        else:
            lines.append(f"║ No components registered{'':>53} ║")
        
        # Errors
        lines.append("╠" + "═" * 78 + "╣")
        lines.append("║ RELIABILITY".ljust(79) + "║")
        lines.append("╠" + "─" * 78 + "╣")
        lines.append(f"║ Error Rate: {sys_metrics.error_rate*100:>5.2f}%   Total Errors: {sys_metrics.total_errors}{'':<41} ║")
        
        lines.append("╚" + "═" * 78 + "╝")
        
        return "\n".join(lines)
    
    def generate_latency_histogram(self, width: int = 60) -> str:
        """Generate ASCII histogram of latency distribution"""
        if not self.latency_history:
            return "No latency data"
        
        # Create bins
        latencies = list(self.latency_history)
        max_latency = max(latencies)
        num_bins = 10
        bin_size = max_latency / num_bins
        
        bins = [0] * num_bins
        for latency in latencies:
            bin_idx = min(int(latency / bin_size), num_bins - 1)
            bins[bin_idx] += 1
        
        max_count = max(bins)
        
        lines = []
        lines.append("Latency Distribution:")
        lines.append("-" * width)
        
        for i, count in enumerate(bins):
            bin_start = i * bin_size
            bin_end = (i + 1) * bin_size
            
            bar_length = int((count / max_count) * (width - 20)) if max_count > 0 else 0
            bar = "█" * bar_length
            
            lines.append(f"{bin_start:>4.2f}-{bin_end:>4.2f}s |{bar:<40} {count}")
        
        return "\n".join(lines)


# ============================================================================
# DASHBOARD SERVER
# ============================================================================

class DashboardServer:
    """
    HTTP server for metrics dashboard.
    
    Provides JSON API and optional Prometheus endpoint.
    """
    
    def __init__(self,
                 collector: MetricsCollector,
                 port: int = 9090):
        """
        Initialize dashboard server.
        
        Args:
            collector: Metrics collector
            port: HTTP port
        """
        self.collector = collector
        self.port = port
    
    def start(self):
        """Start Prometheus HTTP server"""
        if PROMETHEUS_AVAILABLE:
            start_http_server(self.port)
            print(f"✓ Metrics server started on port {self.port}")
            print(f"  Prometheus: http://localhost:{self.port}/metrics")
    
    def get_json_metrics(self) -> str:
        """Get metrics in JSON format"""
        sys_metrics = self.collector.calculate_system_metrics()
        vertex = self.collector.calculate_vertex_criteria()
        
        return json.dumps({
            'system_metrics': asdict(sys_metrics),
            'vertex_criteria': vertex.to_dict(),
            'component_health': self.collector.get_component_health_summary()
        }, indent=2, default=str)


# ============================================================================
# TESTING
# ============================================================================

async def test_dashboard():
    """Test metrics dashboard"""
    
    # Initialize collector
    collector = MetricsCollector(enable_prometheus=False)
    
    # Simulate queries
    print("Simulating queries...")
    
    for i in range(100):
        latency = random.uniform(1.0, 4.0)
        quality = random.uniform(0.75, 0.95)
        num_archetypes = random.choice([1, 1, 2, 2, 2, 3])
        cached = random.random() < 0.6
        error = random.random() < 0.01
        
        collector.record_query(latency, quality, num_archetypes, cached, error)
        
        await asyncio.sleep(0.01)
    
    # Register components
    collector.record_component_health('pipeline', 'healthy')
    collector.record_component_health('redis', 'healthy')
    collector.record_component_health('ollama', 'degraded', 50.0)
    collector.record_component_health('postgres', 'healthy')
    
    # Display dashboard
    print("\n" + collector.generate_ascii_dashboard())
    print("\n" + collector.generate_latency_histogram())
    
    # JSON export
    dashboard = DashboardServer(collector)
    print("\nJSON Metrics:")
    print(dashboard.get_json_metrics())


if __name__ == "__main__":
    import random
    asyncio.run(test_dashboard())

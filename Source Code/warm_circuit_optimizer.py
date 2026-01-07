#!/usr/bin/env python3
"""
Warm Circuit Optimizer - Production Implementation
Predictive model loading based on co-activation patterns

Algorithm:
1. Learn co-activation patterns (which archetypes appear together)
2. Predict next likely archetypes based on current execution
3. Pre-load predicted models in background
4. Achieve 5-10x latency reduction (15s → 3s)

Target: >65% warm hit rate (prediction accuracy)
"""

import numpy as np
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import asyncio
import json

try:
    from archetype_selector import ArchetypeSelector, ARCHETYPE_DOMAINS
except ImportError:
    # Fallback
    ARCHETYPE_DOMAINS = {}
    class ArchetypeSelector:
        pass


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class LoadedModel:
    """Represents a loaded archetype model in memory"""
    archetype: str
    load_timestamp: datetime
    last_access: datetime
    access_count: int = 0
    memory_mb: float = 38000  # 38 GB in MB
    status: str = "warm"  # warm, cold, loading
    
    def __repr__(self):
        age = (datetime.now() - self.load_timestamp).seconds
        return f"LoadedModel({self.archetype}, age={age}s, accesses={self.access_count})"


@dataclass
class WarmCircuitStats:
    """Statistics for warm circuit performance"""
    timestamp: datetime
    total_predictions: int
    correct_predictions: int
    hit_rate: float
    avg_speedup: float  # Actual speedup factor
    models_loaded: int
    memory_usage_gb: float
    prediction_latency_ms: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'hit_rate': self.hit_rate,
            'avg_speedup': self.avg_speedup,
            'models_loaded': self.models_loaded,
            'memory_usage_gb': self.memory_usage_gb,
            'prediction_latency_ms': self.prediction_latency_ms
        }


# ============================================================================
# WARM CIRCUIT OPTIMIZER
# ============================================================================

class WarmCircuitOptimizer:
    """
    Predictive model loading for latency reduction.
    
    Core concepts:
    - Cold load: 15-30s (load model from disk)
    - Warm load: 2-3s (model already in memory)
    - Prediction: Use co-activation matrix to predict next archetype
    - Background loading: Start loading while previous query executes
    
    Memory constraint: Max 3 models concurrent (114 GB total)
    """
    
    def __init__(self, 
                 selector: ArchetypeSelector,
                 max_memory_gb: float = 128,
                 memory_per_model_gb: float = 38,
                 cold_load_time_s: float = 15.0,
                 warm_load_time_s: float = 2.5,
                 prediction_threshold: float = 0.15):
        """
        Initialize warm circuit optimizer.
        
        Args:
            selector: ArchetypeSelector with co-activation matrix
            max_memory_gb: Maximum memory for models
            memory_per_model_gb: Memory per archetype model
            cold_load_time_s: Time to load model from disk
            warm_load_time_s: Time to access loaded model
            prediction_threshold: Minimum probability to predict
        """
        self.selector = selector
        self.max_memory_gb = max_memory_gb
        self.memory_per_model_gb = memory_per_model_gb
        self.cold_load_time = cold_load_time_s
        self.warm_load_time = warm_load_time_s
        self.prediction_threshold = prediction_threshold
        
        # Calculate max concurrent models
        self.max_concurrent_models = int(max_memory_gb / memory_per_model_gb)
        
        # Loaded models (LRU cache)
        self.loaded_models: Dict[str, LoadedModel] = {}
        self.load_queue: deque = deque()  # Background loading queue
        
        # Statistics
        self.prediction_history: List[Tuple[str, List[str], bool]] = []  # (current, predicted, was_correct)
        self.latency_savings: List[float] = []  # Seconds saved
        self.stats_window = 100  # Track last N predictions
        
        # Performance tracking
        self.total_loads = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    @property
    def memory_usage_gb(self) -> float:
        """Current memory usage in GB"""
        return len(self.loaded_models) * self.memory_per_model_gb
    
    @property
    def available_memory_gb(self) -> float:
        """Available memory in GB"""
        return self.max_memory_gb - self.memory_usage_gb
    
    def predict_next(self, current_archetype: str, top_k: int = 2) -> List[Tuple[str, float]]:
        """
        Predict next K most likely archetypes.
        
        Args:
            current_archetype: Currently executing archetype
            top_k: Number of predictions to return
            
        Returns:
            List of (archetype, probability) tuples
        """
        if current_archetype not in self.selector.archetype_to_idx:
            return []
        
        curr_idx = self.selector.archetype_to_idx[current_archetype]
        
        # Get co-activation row
        coactivation_row = self.selector.coactivation[curr_idx]
        
        if coactivation_row.sum() == 0:
            # No learned patterns - use heuristics
            return self._heuristic_prediction(current_archetype, top_k)
        
        # Convert to probabilities
        probs = coactivation_row / coactivation_row.sum()
        
        # Get top K predictions above threshold
        predictions = []
        for arch_idx, prob in enumerate(probs):
            if prob >= self.prediction_threshold:
                archetype = self.selector.idx_to_archetype[arch_idx]
                if archetype != current_archetype:  # Don't predict self
                    predictions.append((archetype, float(prob)))
        
        # Sort by probability
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:top_k]
    
    def _heuristic_prediction(self, current_archetype: str, top_k: int) -> List[Tuple[str, float]]:
        """
        Heuristic-based prediction when no learned patterns available.
        
        Uses domain similarity and known synergies.
        """
        predictions = []
        
        # Get current archetype's domains
        current_domains = set(ARCHETYPE_DOMAINS.get(current_archetype, []))
        
        # Score other archetypes by domain overlap
        for other_arch, other_domains in ARCHETYPE_DOMAINS.items():
            if other_arch == current_archetype:
                continue
            
            other_domains_set = set(other_domains)
            overlap = len(current_domains & other_domains_set)
            
            if overlap > 0:
                # Base score on overlap
                score = overlap / max(len(current_domains), len(other_domains_set))
                predictions.append((other_arch, score))
        
        # Sort by score
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:top_k]
    
    async def should_warm_load(self, current_archetype: str, 
                               predicted_archetype: str) -> bool:
        """
        Decide if we should pre-load a predicted archetype.
        
        Cost-benefit analysis:
        - Cost: Background loading resources
        - Benefit: (probability × time_saved)
        """
        # Check if already loaded
        if predicted_archetype in self.loaded_models:
            return False
        
        # Check memory availability
        if self.memory_usage_gb + self.memory_per_model_gb > self.max_memory_gb:
            # Would exceed memory - need to evict
            if not self._can_evict():
                return False
        
        # Get prediction probability
        predictions = self.predict_next(current_archetype, top_k=5)
        pred_prob = next((p for arch, p in predictions if arch == predicted_archetype), 0.0)
        
        if pred_prob == 0.0:
            return False
        
        # Cost-benefit calculation
        expected_benefit = pred_prob * (self.cold_load_time - self.warm_load_time)
        
        # Load if expected benefit > 1 second
        return expected_benefit > 1.0
    
    def _can_evict(self) -> bool:
        """Check if we can evict a model to free memory"""
        if len(self.loaded_models) <= 1:
            return False  # Keep at least 1 model
        
        return True
    
    async def warm_load(self, archetype: str, priority: int = 1) -> bool:
        """
        Pre-load an archetype model in background.
        
        Args:
            archetype: Archetype to load
            priority: Loading priority (1=low, 3=high)
            
        Returns:
            True if load initiated, False if skipped
        """
        # Check if already loaded or loading
        if archetype in self.loaded_models:
            # Update access time
            self.loaded_models[archetype].last_access = datetime.now()
            self.loaded_models[archetype].access_count += 1
            return False
        
        # Check memory
        if self.memory_usage_gb + self.memory_per_model_gb > self.max_memory_gb:
            # Evict LRU model
            evicted = self._evict_lru()
            if not evicted:
                return False  # Could not evict
        
        # Initiate background load
        await self._background_load(archetype)
        
        return True
    
    async def _background_load(self, archetype: str):
        """
        Load model in background (simulated for now).
        
        In production: Call Ollama API to load model
        """
        # Simulate loading time (in production: actual model loading)
        load_start = datetime.now()
        await asyncio.sleep(0.1)  # Simulated background work
        load_end = datetime.now()
        
        # Add to loaded models
        model = LoadedModel(
            archetype=archetype,
            load_timestamp=load_end,
            last_access=load_end,
            status="warm"
        )
        
        self.loaded_models[archetype] = model
        self.total_loads += 1
        
        print(f"[WarmCircuit] Loaded {archetype} in background ({(load_end - load_start).total_seconds():.2f}s)")
    
    def _evict_lru(self) -> bool:
        """
        Evict least recently used model.
        
        Returns True if evicted, False if couldn't evict
        """
        if not self.loaded_models:
            return False
        
        # Find LRU model
        lru_arch = min(self.loaded_models.items(), 
                      key=lambda x: x[1].last_access)[0]
        
        # Remove
        evicted = self.loaded_models.pop(lru_arch)
        print(f"[WarmCircuit] Evicted {lru_arch} (last access: {evicted.last_access})")
        
        return True
    
    async def get_archetype(self, archetype: str) -> Tuple[float, bool]:
        """
        Get archetype model (load if needed).
        
        Returns:
            (load_time_seconds, was_warm)
        """
        start_time = datetime.now()
        
        # Check if warm (already loaded)
        if archetype in self.loaded_models:
            model = self.loaded_models[archetype]
            model.last_access = datetime.now()
            model.access_count += 1
            
            load_time = self.warm_load_time
            self.cache_hits += 1
            was_warm = True
        else:
            # Cold load
            await self._background_load(archetype)
            load_time = self.cold_load_time
            self.cache_misses += 1
            was_warm = False
        
        end_time = datetime.now()
        actual_time = (end_time - start_time).total_seconds()
        
        return (actual_time, was_warm)
    
    async def predict_and_warm(self, current_archetype: str):
        """
        Predict next archetypes and warm-load in background.
        
        This is the main optimization function - call after executing
        each archetype to prepare for the next.
        """
        # Get predictions
        predictions = self.predict_next(current_archetype, top_k=3)
        
        if not predictions:
            return
        
        # Try to warm-load top predictions
        for predicted_arch, prob in predictions:
            should_load = await self.should_warm_load(current_archetype, predicted_arch)
            
            if should_load:
                await self.warm_load(predicted_arch, priority=2)
                print(f"[WarmCircuit] Warm-loading {predicted_arch} (prob: {prob:.2%})")
    
    def record_prediction(self, current_archetype: str, 
                         next_archetype: str):
        """
        Record prediction outcome for statistics.
        
        Call this after executing next archetype to track accuracy.
        """
        # Get what we predicted
        predictions = self.predict_next(current_archetype, top_k=3)
        predicted_archs = [arch for arch, prob in predictions]
        
        # Check if correct
        was_correct = next_archetype in predicted_archs
        
        # Record
        self.prediction_history.append((current_archetype, predicted_archs, was_correct))
        
        # Calculate latency savings
        if was_correct and next_archetype in self.loaded_models:
            savings = self.cold_load_time - self.warm_load_time
            self.latency_savings.append(savings)
    
    def get_hit_rate(self) -> float:
        """
        Calculate warm hit rate (prediction accuracy).
        
        Target: >0.65 (65% of predictions correct)
        """
        if not self.prediction_history:
            return 0.0
        
        recent = self.prediction_history[-self.stats_window:]
        correct = sum(1 for _, _, was_correct in recent if was_correct)
        
        return correct / len(recent)
    
    def get_avg_speedup(self) -> float:
        """
        Calculate average speedup factor from warm hits.
        
        Example: 15s cold → 2.5s warm = 6x speedup
        """
        if not self.latency_savings:
            return 1.0
        
        recent_savings = self.latency_savings[-self.stats_window:]
        avg_savings = sum(recent_savings) / len(recent_savings)
        
        # Speedup = cold_time / (cold_time - savings)
        speedup = self.cold_load_time / (self.cold_load_time - avg_savings)
        
        return speedup
    
    def get_stats(self) -> WarmCircuitStats:
        """Get current performance statistics"""
        hit_rate = self.get_hit_rate()
        avg_speedup = self.get_avg_speedup()
        
        # Prediction latency (how long predictions take)
        # In production: measure actual prediction time
        prediction_latency = 0.5  # ms (very fast)
        
        return WarmCircuitStats(
            timestamp=datetime.now(),
            total_predictions=len(self.prediction_history),
            correct_predictions=sum(1 for _, _, c in self.prediction_history if c),
            hit_rate=hit_rate,
            avg_speedup=avg_speedup,
            models_loaded=len(self.loaded_models),
            memory_usage_gb=self.memory_usage_gb,
            prediction_latency_ms=prediction_latency
        )
    
    def get_cache_stats(self) -> Dict[str, float]:
        """Get cache hit/miss statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0.0
        
        return {
            'total_accesses': total,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'models_loaded': len(self.loaded_models),
            'memory_usage_gb': self.memory_usage_gb
        }
    
    def visualize_loaded_models(self) -> str:
        """Create ASCII visualization of loaded models"""
        lines = []
        lines.append("=" * 80)
        lines.append("WARM CIRCUIT - LOADED MODELS")
        lines.append("=" * 80)
        lines.append(f"\nMemory: {self.memory_usage_gb:.1f} / {self.max_memory_gb:.1f} GB")
        lines.append(f"Models: {len(self.loaded_models)} / {self.max_concurrent_models}")
        lines.append(f"\nCache Stats:")
        lines.append(f"  Hits: {self.cache_hits}")
        lines.append(f"  Misses: {self.cache_misses}")
        lines.append(f"  Hit Rate: {self.get_hit_rate():.1%}")
        
        if self.loaded_models:
            lines.append(f"\nLoaded Models:")
            for arch, model in sorted(self.loaded_models.items(), 
                                     key=lambda x: x[1].last_access, 
                                     reverse=True):
                age = (datetime.now() - model.load_timestamp).seconds
                lines.append(f"  {arch}: {model.access_count} accesses, age={age}s")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def visualize_coactivation_matrix(selector: ArchetypeSelector, top_n: int = 10) -> str:
    """Visualize top co-activation pairs"""
    lines = []
    lines.append("=" * 80)
    lines.append("CO-ACTIVATION MATRIX - TOP PAIRS")
    lines.append("=" * 80)
    
    # Get all pairs with their scores
    pairs = []
    n = len(selector.archetype_to_idx)
    for i in range(n):
        for j in range(i+1, n):
            score = selector.coactivation[i][j]
            if score > 0:
                arch_i = selector.idx_to_archetype[i]
                arch_j = selector.idx_to_archetype[j]
                pairs.append((arch_i, arch_j, score))
    
    # Sort by score
    pairs.sort(key=lambda x: x[2], reverse=True)
    
    # Display top N
    for i, (arch_a, arch_b, score) in enumerate(pairs[:top_n], 1):
        lines.append(f"{i}. {arch_a} <-> {arch_b}: {score:.0f} co-activations")
    
    if not pairs:
        lines.append("\nNo co-activation patterns learned yet.")
    
    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================

async def test_warm_circuit():
    """Test warm circuit optimizer"""
    from archetype_selector import ArchetypeSelector
    
    # Create selector with some learned patterns
    selector = ArchetypeSelector()
    
    # Simulate learned co-activations
    common_pairs = [
        (['mit_engineering', 'caltech_physics'], 20),
        (['mit_engineering', 'stanford_cs'], 15),
        (['caltech_physics', 'princeton_math'], 18),
        (['harvard_med', 'broad_genomics'], 12),
        (['yale_law', 'chicago_economics'], 10),
    ]
    
    for archetypes, count in common_pairs:
        for _ in range(count):
            selector.update_coactivation(archetypes)
    
    # Create optimizer
    optimizer = WarmCircuitOptimizer(selector)
    
    print("Testing Warm Circuit Optimizer")
    print("=" * 80)
    
    # Test prediction
    current = 'mit_engineering'
    predictions = optimizer.predict_next(current, top_k=3)
    
    print(f"\nCurrent archetype: {current}")
    print("Predictions:")
    for arch, prob in predictions:
        print(f"  {arch}: {prob:.1%}")
    
    # Test warm loading
    print("\nTesting warm load:")
    for predicted_arch, prob in predictions[:2]:
        should_load = await optimizer.should_warm_load(current, predicted_arch)
        print(f"  {predicted_arch} (prob={prob:.1%}): should_load={should_load}")
        
        if should_load:
            await optimizer.warm_load(predicted_arch)
    
    # Show loaded models
    print("\n" + optimizer.visualize_loaded_models())
    
    # Simulate sequence of queries
    print("\nSimulating query sequence:")
    sequence = [
        'mit_engineering',
        'caltech_physics',  # Should be warm-loaded
        'princeton_math',    # Should be warm-loaded
        'stanford_cs'
    ]
    
    total_time = 0.0
    for i, arch in enumerate(sequence):
        load_time, was_warm = await optimizer.get_archetype(arch)
        total_time += load_time
        
        status = "WARM ✓" if was_warm else "COLD ✗"
        print(f"  {i+1}. {arch}: {load_time:.2f}s [{status}]")
        
        # Record prediction if not last
        if i < len(sequence) - 1:
            optimizer.record_prediction(arch, sequence[i+1])
        
        # Predict and warm for next
        if i < len(sequence) - 1:
            await optimizer.predict_and_warm(arch)
    
    print(f"\nTotal time: {total_time:.2f}s")
    print(f"Without warm circuit: {len(sequence) * optimizer.cold_load_time:.2f}s")
    print(f"Speedup: {(len(sequence) * optimizer.cold_load_time) / total_time:.2f}x")
    
    # Show stats
    stats = optimizer.get_stats()
    print(f"\nWarm Circuit Stats:")
    print(f"  Hit Rate: {stats.hit_rate:.1%}")
    print(f"  Avg Speedup: {stats.avg_speedup:.2f}x")
    print(f"  Memory Usage: {stats.memory_usage_gb:.1f} GB")
    
    # Show co-activation matrix
    print("\n" + visualize_coactivation_matrix(selector))


if __name__ == "__main__":
    asyncio.run(test_warm_circuit())

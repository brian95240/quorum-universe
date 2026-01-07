#!/usr/bin/env python3
"""
Cascading Integration Example
Demonstrates complete workflow: Query → Decomposition → Selection → Warm Circuits → Execution

This shows how all components work together to achieve:
- <5s p99 latency
- >90% collapse ratio
- >65% warm hit rate
- High-quality responses
"""

import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

# Import core components
from query_decomposer import QueryDecomposer, QueryAtom, visualize_atoms
from archetype_selector import ArchetypeSelector, ArchetypeSelection, visualize_selection
from warm_circuit_optimizer import WarmCircuitOptimizer, visualize_coactivation_matrix


# ============================================================================
# INTEGRATED PIPELINE
# ============================================================================

class AmbientIntelligencePipeline:
    """
    Complete query processing pipeline.
    
    Stages:
    1. Query Decomposition (QueryDecomposer)
    2. Archetype Selection (ArchetypeSelector with collapse-to-zero)
    3. Warm Circuit Optimization (WarmCircuitOptimizer for speed)
    4. Execution (simulated - in production: Ollama)
    5. Quality Assessment (simulated)
    6. Synthesis (simulated)
    """
    
    def __init__(self):
        """Initialize all pipeline components"""
        self.decomposer = QueryDecomposer()
        self.selector = ArchetypeSelector(
            quality_threshold=0.85,
            max_archetypes=3
        )
        self.optimizer = WarmCircuitOptimizer(
            self.selector,
            max_memory_gb=128,
            cold_load_time_s=15.0,
            warm_load_time_s=2.5
        )
        
        # Track statistics
        self.query_count = 0
        self.total_latency = 0.0
        self.quality_scores = []
    
    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """
        Process a complete query through the pipeline.
        
        Returns execution results with metadata.
        """
        start_time = time.time()
        self.query_count += 1
        
        context = context or {}
        context['hour'] = datetime.now().hour
        
        print("\n" + "=" * 80)
        print(f"PROCESSING QUERY #{self.query_count}")
        print("=" * 80)
        print(f"Query: {query}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # STAGE 1: DECOMPOSITION
        print("\n[STAGE 1] Query Decomposition")
        print("-" * 80)
        decomp_start = time.time()
        
        atoms = self.decomposer.decompose(query, context)
        
        decomp_time = time.time() - decomp_start
        print(f"Decomposed into {len(atoms)} atoms ({decomp_time:.3f}s)")
        print(visualize_atoms(atoms))
        
        # STAGE 2: ARCHETYPE SELECTION (with collapse-to-zero)
        print("\n[STAGE 2] Archetype Selection (Collapse-to-Zero)")
        print("-" * 80)
        select_start = time.time()
        
        selections = []
        for i, atom in enumerate(atoms):
            atom.index = i  # Set index for visualization
            selection = self.selector.select(atom, context)
            selections.append(selection)
            print(visualize_selection(selection))
        
        select_time = time.time() - select_start
        print(f"Selection completed ({select_time:.3f}s)")
        
        # Calculate collapse metrics
        total_archetypes = sum(len(s.selected_archetypes) for s in selections)
        avg_archetypes = total_archetypes / len(selections)
        collapse_ratio = sum(1 for s in selections if len(s.selected_archetypes) <= 2) / len(selections)
        
        print(f"\nCollapse Metrics:")
        print(f"  Total archetypes selected: {total_archetypes}")
        print(f"  Average per atom: {avg_archetypes:.2f}")
        print(f"  Collapse ratio: {collapse_ratio:.1%} (target: >90%)")
        
        # STAGE 3: WARM CIRCUIT OPTIMIZATION
        print("\n[STAGE 3] Warm Circuit Optimization")
        print("-" * 80)
        
        # Get all selected archetypes
        all_archetypes = []
        for selection in selections:
            all_archetypes.extend(selection.selected_archetypes)
        unique_archetypes = list(set(all_archetypes))
        
        print(f"Unique archetypes needed: {len(unique_archetypes)}")
        print(f"Archetypes: {', '.join(unique_archetypes)}")
        
        # Check warm status and predict next
        warm_start = time.time()
        execution_plan = []
        
        for arch in unique_archetypes:
            # Check if warm
            is_warm = arch in self.optimizer.loaded_models
            
            # Predict what might come next
            predictions = self.optimizer.predict_next(arch, top_k=2)
            
            execution_plan.append({
                'archetype': arch,
                'is_warm': is_warm,
                'predictions': predictions
            })
            
            print(f"\n  {arch}:")
            print(f"    Status: {'WARM ✓' if is_warm else 'COLD (loading)'}")
            if predictions:
                print(f"    Predictions:")
                for pred_arch, prob in predictions:
                    print(f"      → {pred_arch} ({prob:.1%})")
        
        warm_time = time.time() - warm_start
        print(f"\nWarm circuit analysis completed ({warm_time:.3f}s)")
        
        # STAGE 4: EXECUTION (simulated)
        print("\n[STAGE 4] Archetype Execution")
        print("-" * 80)
        exec_start = time.time()
        
        responses = []
        total_exec_time = 0.0
        
        for i, arch in enumerate(unique_archetypes):
            # Get archetype (load if needed)
            load_time, was_warm = await self.optimizer.get_archetype(arch)
            total_exec_time += load_time
            
            # Simulate execution (in production: call Ollama)
            exec_time = 2.5  # Simulated inference time
            response = self._simulate_execution(arch, atoms)
            
            responses.append({
                'archetype': arch,
                'response': response,
                'load_time': load_time,
                'was_warm': was_warm,
                'exec_time': exec_time
            })
            
            status = "WARM ✓" if was_warm else "COLD ✗"
            print(f"  {i+1}. {arch}: load={load_time:.2f}s, exec={exec_time:.2f}s [{status}]")
            
            # Predict and warm-load for next archetype
            if i < len(unique_archetypes) - 1:
                next_arch = unique_archetypes[i+1]
                await self.optimizer.predict_and_warm(arch)
                self.optimizer.record_prediction(arch, next_arch)
        
        exec_time_total = time.time() - exec_start
        print(f"\nExecution completed ({exec_time_total:.3f}s)")
        print(f"Total load time: {total_exec_time:.2f}s")
        print(f"Without warm circuit: {len(unique_archetypes) * 15.0:.2f}s")
        speedup = (len(unique_archetypes) * 15.0) / total_exec_time if total_exec_time > 0 else 1.0
        print(f"Speedup: {speedup:.2f}x")
        
        # STAGE 5: QUALITY ASSESSMENT (simulated)
        print("\n[STAGE 5] Quality Assessment")
        print("-" * 80)
        
        quality_score = self._assess_quality(responses, atoms)
        self.quality_scores.append(quality_score)
        
        print(f"Quality Score: {quality_score:.2%} (threshold: 85%)")
        
        if quality_score < 0.85:
            print("⚠️  Quality below threshold - would trigger expansion")
            # In production: expand archetype selection
        else:
            print("✓ Quality sufficient")
        
        # STAGE 6: SYNTHESIS (simulated)
        print("\n[STAGE 6] Cross-Archetype Synthesis")
        print("-" * 80)
        
        synthesis = self._synthesize_responses(responses, atoms)
        
        print(f"Synthesized response:")
        print(f"  Coherence: {synthesis['coherence']:.2%}")
        print(f"  Conflicts detected: {synthesis['conflicts']}")
        print(f"  Citations: {synthesis['citations']}")
        
        # FINAL RESULTS
        end_time = time.time()
        total_time = end_time - start_time
        self.total_latency += total_time
        
        print("\n" + "=" * 80)
        print("QUERY PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Total latency: {total_time:.3f}s")
        print(f"Breakdown:")
        print(f"  Decomposition: {decomp_time:.3f}s ({decomp_time/total_time*100:.1f}%)")
        print(f"  Selection: {select_time:.3f}s ({select_time/total_time*100:.1f}%)")
        print(f"  Warm circuit: {warm_time:.3f}s ({warm_time/total_time*100:.1f}%)")
        print(f"  Execution: {exec_time_total:.3f}s ({exec_time_total/total_time*100:.1f}%)")
        
        # Update co-activation learning
        self.selector.update_coactivation(unique_archetypes)
        
        # Update context for next query
        context['recent_archetypes'] = unique_archetypes
        context['recent_domains'] = [d for atom in atoms for d in atom.domains]
        
        return {
            'query': query,
            'atoms': atoms,
            'selections': selections,
            'responses': responses,
            'synthesis': synthesis,
            'quality_score': quality_score,
            'total_time': total_time,
            'collapse_ratio': collapse_ratio,
            'speedup': speedup,
            'context': context
        }
    
    def _simulate_execution(self, archetype: str, atoms: List[QueryAtom]) -> str:
        """
        Simulate archetype execution.
        
        In production: Call Ollama with archetype model
        """
        # Simulate different response styles
        responses = {
            'mit_engineering': "From an engineering perspective, the optimal solution requires...",
            'caltech_physics': "The fundamental physics principles indicate that...",
            'princeton_math': "Mathematically, we can prove that...",
            'stanford_cs': "The algorithm would be implemented as follows...",
            'harvard_med': "Clinical evidence suggests that...",
            'broad_genomics': "The genetic analysis reveals...",
            'yale_law': "The legal framework establishes that...",
            'chicago_economics': "Economic theory predicts that...",
        }
        
        return responses.get(archetype, f"Response from {archetype}...")
    
    def _assess_quality(self, responses: List[Dict], atoms: List[QueryAtom]) -> float:
        """
        Assess response quality (simulated).
        
        In production: Use quality_assessor.py
        """
        # Simulate quality factors
        relevance = 0.90
        specificity = 0.85
        structure = 0.88
        confidence = 0.87
        
        quality = (relevance * 0.3 + specificity * 0.3 + 
                  structure * 0.2 + confidence * 0.2)
        
        # Add noise
        quality += np.random.normal(0, 0.05)
        quality = max(0.0, min(1.0, quality))
        
        return quality
    
    def _synthesize_responses(self, responses: List[Dict], 
                             atoms: List[QueryAtom]) -> Dict:
        """
        Synthesize multiple archetype responses (simulated).
        
        In production: Use cross_archetype_synthesizer.py
        """
        return {
            'text': "Synthesized response combining all archetype perspectives...",
            'coherence': 0.89,
            'conflicts': 0,
            'citations': len(responses) * 3
        }
    
    def get_metrics(self) -> Dict:
        """Get pipeline metrics"""
        warm_stats = self.optimizer.get_stats()
        selector_metrics = self.selector.get_metrics()
        
        return {
            'total_queries': self.query_count,
            'avg_latency': self.total_latency / self.query_count if self.query_count > 0 else 0,
            'avg_quality': sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0,
            'collapse_ratio': selector_metrics.collapse_ratio,
            'warm_hit_rate': warm_stats.hit_rate,
            'avg_speedup': warm_stats.avg_speedup,
            'models_loaded': warm_stats.models_loaded,
            'memory_usage_gb': warm_stats.memory_usage_gb
        }
    
    def show_loaded_models(self):
        """Display loaded models"""
        print(self.optimizer.visualize_loaded_models())
    
    def show_coactivation(self):
        """Display co-activation patterns"""
        print(visualize_coactivation_matrix(self.selector))


# ============================================================================
# DEMO SCENARIOS
# ============================================================================

async def demo_simple_query(pipeline: AmbientIntelligencePipeline):
    """Demo 1: Simple query (should collapse to 1 archetype)"""
    query = "What is quantum entanglement?"
    result = await pipeline.process_query(query)
    return result


async def demo_complex_query(pipeline: AmbientIntelligencePipeline):
    """Demo 2: Complex query (requires multiple archetypes)"""
    query = "Design a solar-powered water purifier for rural India under $100, explain the engineering constraints and economic feasibility"
    result = await pipeline.process_query(query)
    return result


async def demo_sequential_queries(pipeline: AmbientIntelligencePipeline):
    """Demo 3: Sequential queries (demonstrates warm circuit learning)"""
    queries = [
        "Explain the fundamentals of quantum mechanics",
        "How does quantum entanglement relate to Bell's theorem?",
        "What are the mathematical foundations of quantum field theory?",
        "Can you prove the uncertainty principle from first principles?"
    ]
    
    results = []
    for i, query in enumerate(queries, 1):
        print(f"\n\n{'='*80}")
        print(f"QUERY {i}/{len(queries)}")
        print(f"{'='*80}")
        result = await pipeline.process_query(query)
        results.append(result)
        
        # Show progressive learning
        if i > 1:
            print(f"\n[LEARNING] Co-activation patterns after {i} queries:")
            pipeline.show_coactivation()
    
    return results


async def demo_domain_switching(pipeline: AmbientIntelligencePipeline):
    """Demo 4: Domain switching (tests archetype selection robustness)"""
    queries = [
        "Explain the engineering principles behind suspension bridges",
        "What are the legal implications of autonomous vehicles?",
        "Analyze the genomic basis of Alzheimer's disease",
        "How does Daoist philosophy approach the concept of wu-wei?"
    ]
    
    results = []
    for query in queries:
        result = await pipeline.process_query(query)
        results.append(result)
    
    return results


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

async def main():
    """Run complete demonstration"""
    print("\n")
    print("=" * 80)
    print("AMBIENT INTELLIGENCE PIPELINE - CASCADING INTEGRATION DEMO")
    print("=" * 80)
    print("\nComponents:")
    print("  1. Query Decomposer (spaCy + HDBSCAN)")
    print("  2. Archetype Selector (collapse-to-zero)")
    print("  3. Warm Circuit Optimizer (predictive loading)")
    print("  4. Execution Engine (simulated Ollama)")
    print("  5. Quality Assessor (simulated)")
    print("  6. Response Synthesizer (simulated)")
    print("\nTargets:")
    print("  - Latency p99: <5s")
    print("  - Collapse ratio: >90%")
    print("  - Warm hit rate: >65%")
    print("  - Quality: >85%")
    
    # Initialize pipeline
    pipeline = AmbientIntelligencePipeline()
    
    # Demo 1: Simple query
    print("\n\n" + "=" * 80)
    print("DEMO 1: SIMPLE QUERY (Collapse to 1)")
    print("=" * 80)
    await demo_simple_query(pipeline)
    
    # Demo 2: Complex query
    print("\n\n" + "=" * 80)
    print("DEMO 2: COMPLEX QUERY (Multiple archetypes)")
    print("=" * 80)
    await demo_complex_query(pipeline)
    
    # Demo 3: Sequential queries (warm circuit learning)
    print("\n\n" + "=" * 80)
    print("DEMO 3: SEQUENTIAL QUERIES (Warm circuit learning)")
    print("=" * 80)
    await demo_sequential_queries(pipeline)
    
    # Demo 4: Domain switching
    print("\n\n" + "=" * 80)
    print("DEMO 4: DOMAIN SWITCHING (Robustness test)")
    print("=" * 80)
    await demo_domain_switching(pipeline)
    
    # Final metrics
    print("\n\n" + "=" * 80)
    print("FINAL PIPELINE METRICS")
    print("=" * 80)
    
    metrics = pipeline.get_metrics()
    print(f"\nPerformance:")
    print(f"  Total Queries: {metrics['total_queries']}")
    print(f"  Average Latency: {metrics['avg_latency']:.3f}s (target: <5s)")
    print(f"  Average Quality: {metrics['avg_quality']:.1%} (target: >85%)")
    
    print(f"\nEfficiency:")
    print(f"  Collapse Ratio: {metrics['collapse_ratio']:.1%} (target: >90%)")
    print(f"  Warm Hit Rate: {metrics['warm_hit_rate']:.1%} (target: >65%)")
    print(f"  Average Speedup: {metrics['avg_speedup']:.2f}x (target: >5x)")
    
    print(f"\nResource Usage:")
    print(f"  Models Loaded: {metrics['models_loaded']}")
    print(f"  Memory Usage: {metrics['memory_usage_gb']:.1f} GB (limit: 128 GB)")
    
    # Vertex criteria check
    print(f"\n" + "=" * 80)
    print("VERTEX CRITERIA ASSESSMENT")
    print("=" * 80)
    
    criteria_met = 0
    total_criteria = 5
    
    checks = [
        ("Latency <5s", metrics['avg_latency'] < 5.0),
        ("Quality >85%", metrics['avg_quality'] > 0.85),
        ("Collapse >90%", metrics['collapse_ratio'] > 0.90),
        ("Warm Hit >65%", metrics['warm_hit_rate'] > 0.65),
        ("Memory <128GB", metrics['memory_usage_gb'] < 128)
    ]
    
    for criterion, met in checks:
        status = "✓ PASS" if met else "✗ FAIL"
        print(f"  {criterion}: {status}")
        if met:
            criteria_met += 1
    
    print(f"\nVertex Score: {criteria_met}/{total_criteria} ({criteria_met/total_criteria*100:.0f}%)")
    
    if criteria_met == total_criteria:
        print("\n🎉 VERTEX CERTIFIED - All criteria met!")
    else:
        print(f"\n⚠️  {total_criteria - criteria_met} criteria need improvement")
    
    # Show system state
    print("\n")
    pipeline.show_loaded_models()
    print("\n")
    pipeline.show_coactivation()


if __name__ == "__main__":
    asyncio.run(main())

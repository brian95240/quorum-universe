#!/usr/bin/env python3
"""
DEMO - Knowledge Graph + Archetype Router
Demonstrates the complete system in action
"""

import asyncio
from knowledge_graph import KnowledgeGraph, ARCHETYPES, create_document_from_file
from archetype_router import ArchetypeRouter


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ambient_intelligence',
    'user': 'puck_user',
    'password': 'change_me_in_production'
}


# ============================================================================
# DEMO 1: Knowledge Graph Basics
# ============================================================================

def demo_knowledge_graph():
    """Demonstrate knowledge graph ingestion and search"""
    print("\n" + "="*80)
    print("DEMO 1: Knowledge Graph")
    print("="*80 + "\n")
    
    kg = KnowledgeGraph(DB_CONFIG)
    
    try:
        # Show available archetypes
        print("Available Archetypes:")
        for name, data in ARCHETYPES.items():
            print(f"  • {name:25s} [{data['cluster']:20s}] {data['corpus_size_gb']:3d} GB")
        
        print(f"\nTotal: {len(ARCHETYPES)} archetypes, {sum(a['corpus_size_gb'] for a in ARCHETYPES.values())} GB")
        
        # Show statistics (if any data exists)
        stats = kg.get_archetype_stats()
        if stats:
            print("\nCurrent Database Statistics:")
            for archetype, data in stats.items():
                print(f"  {archetype:20s} | {data['documents']:4d} docs | {data['chunks']:6d} chunks")
        else:
            print("\nNo data ingested yet. Use:")
            print("  python knowledge_graph.py --ingest archetype:source:path")
        
        # Example search (if data exists)
        if stats:
            print("\nExample Search: 'quantum mechanics'")
            results = kg.semantic_search("quantum mechanics", top_k=3)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. [{result['archetype']}] {result['document_title']}")
                print(f"   Similarity: {result['similarity']:.3f}")
                print(f"   Preview: {result['text'][:150]}...")
    
    finally:
        kg.close()


# ============================================================================
# DEMO 2: Simple Query Routing
# ============================================================================

async def demo_simple_routing():
    """Demonstrate simple query routing"""
    print("\n" + "="*80)
    print("DEMO 2: Simple Query Routing")
    print("="*80 + "\n")
    
    router = ArchetypeRouter(DB_CONFIG)
    
    try:
        query = "Explain quantum entanglement"
        
        print(f"Query: {query}\n")
        
        result = await router.route(query)
        
        print(f"\nArchetypes Used: {', '.join(result['archetypes_used'])}")
        print(f"Execution Time: {result['execution_time']:.2f}s")
        print(f"Number of Atoms: {len(result['atoms'])}")
        print(f"Number of Batches: {result['num_batches']}")
        
        print(f"\nSynthesis:\n{result['synthesis']}")
    
    finally:
        router.close()


# ============================================================================
# DEMO 3: Complex Multi-Step Query
# ============================================================================

async def demo_complex_routing():
    """Demonstrate complex query with micro-batching"""
    print("\n" + "="*80)
    print("DEMO 3: Complex Multi-Step Query")
    print("="*80 + "\n")
    
    router = ArchetypeRouter(DB_CONFIG)
    
    try:
        query = "Design a solar-powered water purifier for rural India under $100, then explain the manufacturing process and deployment strategy"
        
        print(f"Query: {query}\n")
        
        result = await router.route(query)
        
        print("\nQuery Decomposition:")
        for i, atom in enumerate(result['atoms'], 1):
            print(f"  {i}. {atom}")
        
        print(f"\nExecution Plan: {result['num_batches']} batches (parallel execution)")
        
        print(f"\nArchetypes Used: {', '.join(result['archetypes_used'])}")
        
        print("\nIndividual Results:")
        for atom_text, atom_result in result['results'].items():
            print(f"\n  [{atom_result['archetype']}]")
            print(f"  Atom: {atom_text}")
            print(f"  Quality: {atom_result.get('quality', 0):.2f}")
            print(f"  Time: {atom_result['time']:.2f}s")
            print(f"  Sources: {len(atom_result['sources'])}")
        
        print(f"\nTotal Time: {result['execution_time']:.2f}s")
        print(f"\nSynthesized Response:\n{result['synthesis']}")
    
    finally:
        router.close()


# ============================================================================
# DEMO 4: Collapse-to-Zero Efficiency
# ============================================================================

async def demo_collapse_efficiency():
    """Demonstrate collapse-to-zero logic"""
    print("\n" + "="*80)
    print("DEMO 4: Collapse-to-Zero Efficiency")
    print("="*80 + "\n")
    
    router = ArchetypeRouter(DB_CONFIG)
    
    try:
        queries = [
            "What is 2+2?",  # Simple - should collapse to 1
            "Explain the Standard Model of particle physics",  # Medium - might use 2
            "Compare Eastern and Western approaches to consciousness"  # Complex - might use 3
        ]
        
        for query in queries:
            print(f"\nQuery: {query}")
            
            result = await router.route(query)
            
            num_archetypes = len(result['archetypes_used'])
            print(f"  Archetypes Used: {num_archetypes} ({', '.join(result['archetypes_used'])})")
            print(f"  Execution Time: {result['execution_time']:.2f}s")
            
            # Show quality scores
            avg_quality = 0
            if result['results']:
                qualities = [r.get('quality', 0) for r in result['results'].values()]
                avg_quality = sum(qualities) / len(qualities)
            print(f"  Average Quality: {avg_quality:.2f}")
    
    finally:
        router.close()


# ============================================================================
# DEMO 5: Warm Circuit Optimization
# ============================================================================

async def demo_warm_circuits():
    """Demonstrate warm circuit predictive loading"""
    print("\n" + "="*80)
    print("DEMO 5: Warm Circuit Optimization")
    print("="*80 + "\n")
    
    router = ArchetypeRouter(DB_CONFIG)
    
    try:
        # Sequence of related queries (should trigger warm loading)
        queries = [
            "Explain dark matter",  # Physics
            "What are the mathematical models for dark matter?",  # Math (should warm-load)
            "How would we engineer a dark matter detector?"  # Engineering (follows physics)
        ]
        
        print("Running sequence of related queries...\n")
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. {query}")
            
            result = await router.route(query)
            
            print(f"   Archetypes: {', '.join(result['archetypes_used'])}")
            print(f"   Time: {result['execution_time']:.2f}s")
            
            # After first query, show warm circuit predictions
            if i == 1:
                predicted = router.optimizer.predict_next(
                    result['archetypes_used'][0],
                    top_k=2
                )
                print(f"   🔥 Warm-loading predicted: {', '.join(predicted)}")
    
    finally:
        router.close()


# ============================================================================
# DEMO 6: Context-Aware Routing
# ============================================================================

async def demo_context_routing():
    """Demonstrate temporal and contextual routing"""
    print("\n" + "="*80)
    print("DEMO 6: Context-Aware Routing")
    print("="*80 + "\n")
    
    router = ArchetypeRouter(DB_CONFIG)
    
    try:
        query = "How do I optimize this?"
        
        contexts = [
            {
                'name': 'Morning coding session',
                'hour': 9,
                'last_queries': ['Python performance', 'algorithm complexity'],
                'recent_archetypes': ['stanford_cs']
            },
            {
                'name': 'Evening workout',
                'hour': 19,
                'last_queries': ['exercise routine', 'muscle recovery'],
                'recent_archetypes': ['harvard_med']
            },
            {
                'name': 'Business meeting',
                'hour': 14,
                'last_queries': ['startup funding', 'burn rate'],
                'recent_archetypes': ['chicago_economics']
            }
        ]
        
        print(f"Same Query: '{query}'")
        print("Different Contexts:\n")
        
        for context in contexts:
            print(f"Context: {context['name']}")
            
            result = await router.route(query, context)
            
            print(f"  → Routes to: {', '.join(result['archetypes_used'])}")
            print(f"  → Response preview: {result['synthesis'][:150]}...\n")
    
    finally:
        router.close()


# ============================================================================
# MAIN DEMO RUNNER
# ============================================================================

async def run_all_demos():
    """Run all demonstrations"""
    demos = [
        ("Knowledge Graph Basics", demo_knowledge_graph, False),
        ("Simple Query Routing", demo_simple_routing, True),
        ("Complex Multi-Step Query", demo_complex_routing, True),
        ("Collapse-to-Zero Efficiency", demo_collapse_efficiency, True),
        ("Warm Circuit Optimization", demo_warm_circuits, True),
        ("Context-Aware Routing", demo_context_routing, True)
    ]
    
    print("\n" + "="*80)
    print("KNOWLEDGE GRAPH + ARCHETYPE ROUTER DEMOS")
    print("="*80)
    
    for i, (name, func, is_async) in enumerate(demos, 1):
        print(f"\n[{i}/{len(demos)}] {name}")
        input("\nPress Enter to continue...")
        
        try:
            if is_async:
                await func()
            else:
                func()
        except Exception as e:
            print(f"\nERROR in demo: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-"*80)
    
    print("\n✓ All demos complete!")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        demo_name = sys.argv[1]
        
        demos = {
            'kg': demo_knowledge_graph,
            'simple': demo_simple_routing,
            'complex': demo_complex_routing,
            'collapse': demo_collapse_efficiency,
            'warm': demo_warm_circuits,
            'context': demo_context_routing
        }
        
        if demo_name in demos:
            func = demos[demo_name]
            if demo_name == 'kg':
                func()
            else:
                asyncio.run(func())
        else:
            print(f"Unknown demo: {demo_name}")
            print(f"Available: {', '.join(demos.keys())}")
    else:
        asyncio.run(run_all_demos())


if __name__ == '__main__':
    main()

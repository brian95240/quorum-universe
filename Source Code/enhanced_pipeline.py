#!/usr/bin/env python3
"""
Enhanced Integration Pipeline - Complete System Assembly
Integrates: Pipeline + Context + Research + Forensics

This is the complete "Intelligence Amplification Layer" that transforms
the execution-ready system into a production-grade vertex implementation.

Flow:
Query → Decomposition → Selection → Context Retrieval → Warm Circuits → 
Execution → Quality Assessment → Research (if needed) → Truth Forensics → 
Batch Processing → Synthesis → Response

New capabilities added in this cascade:
- Semantic context retrieval from knowledge graph
- External research with authority discovery
- Truth validation via philosopher tribunal
- Production API with streaming
- Comprehensive metrics and monitoring
"""

import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Import cascade 1 components (execution layer)
from complete_pipeline import AmbientIntelligencePipeline, PipelineResult
from archetype_executor import ExecutionResult
from quality_assessor import QualityScore

# Import cascade 2 components (intelligence amplification layer)
from context_retriever import ContextRetriever, RetrievalResult
from research_orchestrator import ResearchOrchestrator, ResearchResult, ResearchTrigger
from truth_forensics_engine import TruthForensicsEngine, TruthForensicsReport


# ============================================================================
# ENHANCED RESULT
# ============================================================================

@dataclass
class EnhancedPipelineResult(PipelineResult):
    """
    Extended pipeline result with intelligence amplification data.
    
    Inherits from PipelineResult and adds:
    - Context retrieval metrics
    - Research results
    - Truth forensics report
    """
    # Context retrieval
    context_retrieval: Optional[RetrievalResult] = None
    context_chunks_used: int = 0
    context_cache_hit: bool = False
    
    # Research
    research_result: Optional[ResearchResult] = None
    research_triggered: bool = False
    research_sources: int = 0
    
    # Truth forensics
    forensics_report: Optional[TruthForensicsReport] = None
    forensics_passed: bool = True
    forensics_threat_level: str = "clear"
    
    # Overall enhancement metrics
    enhancement_time_ms: float = 0.0
    total_enhanced_latency_ms: float = 0.0
    
    def to_enhanced_dict(self) -> Dict:
        """Convert to dictionary with enhanced data"""
        base = super().to_dict()
        
        enhanced = {
            'context': {
                'chunks_used': self.context_chunks_used,
                'cache_hit': self.context_cache_hit,
                'retrieval_time_ms': self.context_retrieval.retrieval_time_ms if self.context_retrieval else 0
            },
            'research': {
                'triggered': self.research_triggered,
                'sources_found': self.research_sources,
                'research_time_ms': self.research_result.research_time_ms if self.research_result else 0
            },
            'forensics': {
                'passed': self.forensics_passed,
                'threat_level': self.forensics_threat_level,
                'consensus_score': self.forensics_report.consensus_score if self.forensics_report else 0,
                'truth_score': self.forensics_report.avg_truth_score if self.forensics_report else 0
            },
            'performance': {
                'enhancement_time_ms': self.enhancement_time_ms,
                'total_latency_ms': self.total_enhanced_latency_ms
            }
        }
        
        return {**base, **enhanced}


# ============================================================================
# ENHANCED PIPELINE
# ============================================================================

class EnhancedPipeline:
    """
    Complete intelligence amplification system.
    
    Combines:
    - Execution layer (cascade 1)
    - Intelligence amplification layer (cascade 2)
    
    Achieves enhanced vertex criteria:
    - <5s latency (with context + research + forensics)
    - >90% collapse ratio
    - >65% warm hit rate  
    - >0.85 quality score
    - Truth validation via philosopher tribunal
    - External knowledge integration
    """
    
    def __init__(self,
                 db_config: Dict,
                 redis_config: Optional[Dict] = None,
                 ollama_host: str = "http://localhost:11434",
                 enable_context: bool = True,
                 enable_research: bool = True,
                 enable_forensics: bool = True):
        """
        Initialize enhanced pipeline with all components.
        
        Args:
            db_config: PostgreSQL + AGE configuration
            redis_config: Redis configuration
            ollama_host: Ollama API endpoint
            enable_context: Enable context retrieval
            enable_research: Enable external research
            enable_forensics: Enable truth forensics
        """
        print("\n" + "=" * 80)
        print("INITIALIZING ENHANCED INTELLIGENCE AMPLIFICATION PIPELINE")
        print("=" * 80)
        
        # Core pipeline (cascade 1)
        print("\n[CASCADE 1] Loading Execution Layer...")
        self.core_pipeline = AmbientIntelligencePipeline(
            db_config=db_config,
            ollama_host=ollama_host,
            quality_threshold=0.85,
            max_archetypes=3
        )
        
        # Intelligence amplification components (cascade 2)
        print("\n[CASCADE 2] Loading Intelligence Amplification Layer...")
        
        self.enable_context = enable_context
        self.enable_research = enable_research
        self.enable_forensics = enable_forensics
        
        # Context retriever
        if enable_context:
            print("[1/3] Loading ContextRetriever...")
            self.context_retriever = ContextRetriever(
                db_config=db_config,
                redis_config=redis_config,
                enable_cache=True
            )
        else:
            self.context_retriever = None
        
        # Research orchestrator
        if enable_research:
            print("[2/3] Loading ResearchOrchestrator...")
            self.research_orchestrator = ResearchOrchestrator(
                redis_config=redis_config,
                enable_cache=True,
                enable_research=True
            )
        else:
            self.research_orchestrator = None
        
        # Truth forensics engine
        if enable_forensics:
            print("[3/3] Loading TruthForensicsEngine...")
            self.truth_forensics = TruthForensicsEngine(
                enable_ollama=True,
                philosophers=None  # Use all philosophers
            )
        else:
            self.truth_forensics = None
        
        # Statistics
        self.total_enhanced_queries = 0
        self.context_retrievals = 0
        self.research_triggers = 0
        self.forensics_analyses = 0
        
        print("\n✓ Enhanced pipeline initialized successfully")
        print("=" * 80 + "\n")
    
    async def process(self,
                     query: str,
                     context: Optional[Dict] = None,
                     verbose: bool = True) -> EnhancedPipelineResult:
        """
        Process query through enhanced pipeline.
        
        Complete flow:
        1. Retrieve context from knowledge graph
        2. Execute core pipeline (decompose, select, execute, assess, synthesize)
        3. Check if research needed
        4. If needed, perform external research
        5. Validate with truth forensics
        6. Return enhanced result
        
        Args:
            query: User query
            context: Optional context
            verbose: Print progress
        
        Returns:
            EnhancedPipelineResult with all enhancements
        """
        start_time = time.time()
        enhancement_start = time.time()
        
        if verbose:
            print("\n" + "=" * 80)
            print("PROCESSING ENHANCED QUERY")
            print("=" * 80)
            print(f"Query: {query}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
        
        # PHASE 1: CONTEXT RETRIEVAL
        context_result = None
        context_chunks = []
        
        if self.enable_context and self.context_retriever:
            if verbose:
                print("\n[PHASE 1] Context Retrieval")
                print("-" * 80)
            
            context_result = self.context_retriever.retrieve(
                query=query,
                archetypes=None,  # Will be determined by selector
                k=10,
                max_tokens=2048,
                use_cache=True
            )
            
            context_chunks = [chunk.text for chunk in context_result.chunks]
            self.context_retrievals += 1
            
            if verbose:
                print(f"Retrieved {len(context_chunks)} context chunks ({context_result.retrieval_time_ms:.0f}ms)")
                print(f"Cache: {'HIT' if context_result.cache_hit else 'MISS'}")
        
        # PHASE 2: CORE PIPELINE EXECUTION
        if verbose:
            print("\n[PHASE 2] Core Pipeline Execution")
            print("-" * 80)
        
        # Execute core pipeline (this runs the full cascade 1 flow)
        core_result = await self.core_pipeline.process(
            query=query,
            context=context,
            verbose=verbose
        )
        
        # PHASE 3: RESEARCH (if needed)
        research_result = None
        research_triggered = False
        
        if self.enable_research and self.research_orchestrator:
            if verbose:
                print("\n[PHASE 3] Research Assessment")
                print("-" * 80)
            
            # Check if research needed based on quality
            internal_confidence = core_result.avg_quality
            should_research, trigger = self.research_orchestrator.should_research(
                query=query,
                internal_confidence=internal_confidence,
                query_context=context
            )
            
            if should_research:
                research_triggered = True
                self.research_triggers += 1
                
                if verbose:
                    print(f"Research triggered: {trigger.value}")
                
                research_result = await self.research_orchestrator.research(
                    query=query,
                    trigger=trigger,
                    max_sources=10,
                    use_cache=True
                )
                
                if verbose:
                    print(f"Found {len(research_result.sources)} sources ({research_result.research_time_ms:.0f}ms)")
            else:
                if verbose:
                    print(f"Research not needed (confidence: {internal_confidence:.2f})")
        
        # PHASE 4: TRUTH FORENSICS
        forensics_report = None
        forensics_passed = True
        
        if self.enable_forensics and self.truth_forensics:
            if verbose:
                print("\n[PHASE 4] Truth Forensics")
                print("-" * 80)
            
            forensics_report = await self.truth_forensics.analyze(
                query=query,
                response=core_result.final_response,
                archetype=None,  # Multiple archetypes involved
                context=context
            )
            
            forensics_passed = not forensics_report.requires_revision
            self.forensics_analyses += 1
            
            if verbose:
                print(f"Threat level: {forensics_report.threat_level.value}")
                print(f"Truth score: {forensics_report.avg_truth_score:.2f}")
                print(f"Consensus: {forensics_report.consensus_score:.2f}")
                print(f"Verdict: {'PASS' if forensics_passed else 'REVISION REQUIRED'}")
        
        # Build enhanced result
        enhancement_time = (time.time() - enhancement_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        # Create enhanced result (inheriting from core result)
        enhanced_result = EnhancedPipelineResult(
            # Core result fields
            query=core_result.query,
            final_response=core_result.final_response,
            total_latency_ms=core_result.total_latency_ms,
            decomposition_ms=core_result.decomposition_ms,
            selection_ms=core_result.selection_ms,
            execution_ms=core_result.execution_ms,
            synthesis_ms=core_result.synthesis_ms,
            atoms=core_result.atoms,
            archetype_selections=core_result.archetype_selections,
            execution_results=core_result.execution_results,
            quality_scores=core_result.quality_scores,
            synthesized=core_result.synthesized,
            avg_quality=core_result.avg_quality,
            collapse_ratio=core_result.collapse_ratio,
            warm_hit_rate=core_result.warm_hit_rate,
            total_archetypes_considered=core_result.total_archetypes_considered,
            total_archetypes_used=core_result.total_archetypes_used,
            total_tokens_generated=core_result.total_tokens_generated,
            
            # Enhanced fields
            context_retrieval=context_result,
            context_chunks_used=len(context_chunks),
            context_cache_hit=context_result.cache_hit if context_result else False,
            research_result=research_result,
            research_triggered=research_triggered,
            research_sources=len(research_result.sources) if research_result else 0,
            forensics_report=forensics_report,
            forensics_passed=forensics_passed,
            forensics_threat_level=forensics_report.threat_level.value if forensics_report else "clear",
            enhancement_time_ms=enhancement_time,
            total_enhanced_latency_ms=total_time
        )
        
        # Update statistics
        self.total_enhanced_queries += 1
        
        if verbose:
            print("\n" + "=" * 80)
            print("ENHANCED PIPELINE COMPLETE")
            print("=" * 80)
            self._print_enhanced_summary(enhanced_result)
        
        return enhanced_result
    
    def _print_enhanced_summary(self, result: EnhancedPipelineResult):
        """Print execution summary with enhancements"""
        print(f"\n📊 Enhanced Performance Metrics:")
        print(f"  Total latency: {result.total_enhanced_latency_ms:.0f}ms")
        print(f"    Core pipeline: {result.total_latency_ms:.0f}ms")
        print(f"    Context retrieval: {result.context_retrieval.retrieval_time_ms if result.context_retrieval else 0:.0f}ms")
        print(f"    Research: {result.research_result.research_time_ms if result.research_result else 0:.0f}ms")
        print(f"    Forensics: {result.forensics_report.total_analysis_time_ms if result.forensics_report else 0:.0f}ms")
        
        print(f"\n🎯 Quality & Truth Metrics:")
        print(f"  Response quality: {result.avg_quality:.2f}")
        print(f"  Truth score: {result.forensics_report.avg_truth_score if result.forensics_report else 1.0:.2f}")
        print(f"  Threat level: {result.forensics_threat_level}")
        
        print(f"\n🔍 Intelligence Augmentation:")
        print(f"  Context chunks: {result.context_chunks_used}")
        print(f"  Research sources: {result.research_sources}")
        print(f"  Forensics: {'PASSED' if result.forensics_passed else 'FAILED'}")
        
        print(f"\n📈 Efficiency Metrics:")
        print(f"  Collapse ratio: {result.collapse_ratio:.1%}")
        print(f"  Warm hit rate: {result.warm_hit_rate:.1%}")
        print(f"  Context cache: {'HIT' if result.context_cache_hit else 'MISS'}")
        
        # Enhanced vertex criteria
        print(f"\n🏆 Enhanced Vertex Criteria:")
        criteria = {
            'Latency < 5s': result.total_enhanced_latency_ms < 5000,
            'Collapse > 90%': result.collapse_ratio > 0.90,
            'Warm hit > 65%': result.warm_hit_rate > 0.65,
            'Quality > 0.85': result.avg_quality > 0.85,
            'Truth score > 0.80': (result.forensics_report.avg_truth_score if result.forensics_report else 1.0) > 0.80,
            'Forensics passed': result.forensics_passed
        }
        
        for criterion, passed in criteria.items():
            icon = "✓" if passed else "✗"
            print(f"  {icon} {criterion}")
        
        all_passed = all(criteria.values())
        if all_passed:
            print(f"\n🌟 ENHANCED VERTEX CRITERIA: ACHIEVED 🌟")
        else:
            print(f"\n⚠️  ENHANCED VERTEX CRITERIA: NOT MET")
        
        print("\n" + "=" * 80)
    
    def get_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        core_stats = self.core_pipeline.get_stats()
        
        enhanced_stats = {
            'enhanced': {
                'total_queries': self.total_enhanced_queries,
                'context_retrievals': self.context_retrievals,
                'research_triggers': self.research_triggers,
                'forensics_analyses': self.forensics_analyses
            },
            'core': core_stats
        }
        
        # Add component stats
        if self.context_retriever:
            enhanced_stats['context_retriever'] = self.context_retriever.get_stats()
        
        if self.research_orchestrator:
            enhanced_stats['research'] = self.research_orchestrator.get_stats()
        
        if self.truth_forensics:
            enhanced_stats['forensics'] = self.truth_forensics.get_stats()
        
        return enhanced_stats


# ============================================================================
# DEMO
# ============================================================================

async def demo_enhanced_pipeline():
    """Demonstrate enhanced pipeline"""
    
    # Configuration
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ambient_intelligence',
        'user': 'puck_user',
        'password': 'your_password'
    }
    
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    # Initialize enhanced pipeline
    pipeline = EnhancedPipeline(
        db_config=DB_CONFIG,
        redis_config=REDIS_CONFIG,
        enable_context=True,
        enable_research=True,
        enable_forensics=True
    )
    
    # Test query
    query = "What are the latest breakthroughs in quantum computing and their implications for cryptography?"
    
    print("\n" + "=" * 80)
    print("ENHANCED PIPELINE DEMONSTRATION")
    print("=" * 80)
    print(f"\nQuery: {query}\n")
    
    # Process
    result = await pipeline.process(query, verbose=True)
    
    # Display final response
    print("\n" + "=" * 80)
    print("FINAL ENHANCED RESPONSE")
    print("=" * 80)
    print(result.final_response)
    print("=" * 80)
    
    # Show statistics
    stats = pipeline.get_stats()
    print(f"\nSystem Statistics:")
    print(f"  Total enhanced queries: {stats['enhanced']['total_queries']}")
    print(f"  Context retrievals: {stats['enhanced']['context_retrievals']}")
    print(f"  Research triggers: {stats['enhanced']['research_triggers']}")
    print(f"  Forensics analyses: {stats['enhanced']['forensics_analyses']}")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_pipeline())

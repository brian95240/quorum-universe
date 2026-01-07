#!/usr/bin/env python3
"""
Archetype Executor - Production Implementation
Executes queries through Ollama with composite LoRA models

Key Features:
- Async execution with timeout protection
- Composite LoRA model support (base + voice adapter)
- Streaming and batch modes
- Retry logic with exponential backoff
- Token usage tracking
- Model health monitoring

Architecture:
- Base models: stem_core, life_systems, social_fabric, ancient_wisdom
- Voice adapters: 20 institutional voices layered on bases
- Format: {base}+{voice} (e.g., "stem_core+mit_engineering")
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    print("WARNING: ollama-python not found. Install: pip install ollama")
    OLLAMA_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class ExecutionStatus(Enum):
    """Execution status codes"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass
class ExecutionResult:
    """Result from archetype execution"""
    archetype: str
    query: str
    response: str
    status: ExecutionStatus
    
    # Performance metrics
    latency_ms: float
    tokens_generated: int = 0
    tokens_per_second: float = 0.0
    
    # Model info
    model_name: str = ""
    base_model: str = ""
    voice_adapter: str = ""
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    error_message: str = ""
    
    # Context used
    context_chunks: List[str] = field(default_factory=list)
    context_tokens: int = 0
    
    def __repr__(self):
        status_icon = "✓" if self.status == ExecutionStatus.SUCCESS else "✗"
        return (f"ExecutionResult({status_icon} {self.archetype}, "
                f"{self.latency_ms:.0f}ms, {self.tokens_generated} tokens)")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'archetype': self.archetype,
            'query': self.query,
            'response': self.response,
            'status': self.status.value,
            'latency_ms': self.latency_ms,
            'tokens_generated': self.tokens_generated,
            'tokens_per_second': self.tokens_per_second,
            'model_name': self.model_name,
            'timestamp': self.timestamp.isoformat(),
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'context_chunks_count': len(self.context_chunks),
            'context_tokens': self.context_tokens
        }


@dataclass
class ModelHealth:
    """Health status of an Ollama model"""
    model_name: str
    available: bool
    last_check: datetime
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    total_requests: int = 0
    failed_requests: int = 0


# ============================================================================
# ARCHETYPE EXECUTOR
# ============================================================================

class ArchetypeExecutor:
    """
    Production-ready execution engine for archetype queries.
    
    Features:
    - Composite LoRA model orchestration
    - Async execution with concurrency control
    - Automatic retry with exponential backoff
    - Health monitoring and graceful degradation
    - Context injection from knowledge graph
    - Streaming support for real-time responses
    """
    
    # Model architecture mapping
    BASE_MODELS = {
        'stem_core': ['mit_engineering', 'caltech_physics', 'stanford_cs', 
                      'berkeley_ai', 'princeton_math'],
        'life_systems': ['harvard_med', 'johns_hopkins_clinical', 'broad_genomics',
                        'rockefeller_bio', 'ucsd_longevity'],
        'social_fabric': ['yale_law', 'oxford_phil', 'chicago_econ', 
                         'stanford_strategy', 'mit_media'],
        'ancient_wisdom': ['beijing_classical', 'baghdad_golden', 'nalanda_vedic',
                          'alexandria_greek', 'mensa_polymath']
    }
    
    # Default generation parameters
    DEFAULT_PARAMS = {
        'temperature': 0.7,
        'top_p': 0.9,
        'top_k': 40,
        'num_predict': 1024,  # Max tokens
        'repeat_penalty': 1.1,
        'stop': ['</answer>', '\n\nHuman:', '\n\nUser:']
    }
    
    # Archetype-specific overrides
    ARCHETYPE_PARAMS = {
        'mit_engineering': {'temperature': 0.6, 'num_predict': 1536},
        'caltech_physics': {'temperature': 0.7, 'num_predict': 1536},
        'princeton_math': {'temperature': 0.5, 'num_predict': 2048},
        'harvard_med': {'temperature': 0.6, 'num_predict': 1536},
        'yale_law': {'temperature': 0.5, 'num_predict': 2048},
        'oxford_phil': {'temperature': 0.8, 'num_predict': 1536},
        'chicago_econ': {'temperature': 0.7, 'num_predict': 1536},
        'mensa_polymath': {'temperature': 0.8, 'num_predict': 2048},
    }
    
    def __init__(self,
                 ollama_host: str = "http://localhost:11434",
                 max_retries: int = 3,
                 timeout_seconds: int = 120,
                 max_concurrent: int = 3):
        """
        Initialize executor.
        
        Args:
            ollama_host: Ollama API endpoint
            max_retries: Maximum retry attempts per query
            timeout_seconds: Query timeout
            max_concurrent: Maximum concurrent executions
        """
        self.ollama_host = ollama_host
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.max_concurrent = max_concurrent
        
        # Health tracking
        self.model_health: Dict[str, ModelHealth] = {}
        
        # Execution statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_latency_ms = 0.0
        self.total_tokens = 0
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Model cache (tracks loaded models)
        self.loaded_models: set = set()
        
        print(f"ArchetypeExecutor initialized")
        print(f"  Ollama: {ollama_host}")
        print(f"  Max concurrent: {max_concurrent}")
        print(f"  Timeout: {timeout_seconds}s")
    
    def get_model_name(self, archetype: str) -> str:
        """
        Get composite model name for archetype.
        
        Format: {base_model}+{voice_adapter}
        Example: stem_core+mit_engineering
        """
        # Find which base model contains this archetype
        for base, voices in self.BASE_MODELS.items():
            if archetype in voices:
                return f"{base}+{archetype}"
        
        # Fallback: use first base
        return f"stem_core+{archetype}"
    
    def get_generation_params(self, archetype: str) -> Dict:
        """Get generation parameters for archetype"""
        params = self.DEFAULT_PARAMS.copy()
        
        # Apply archetype-specific overrides
        if archetype in self.ARCHETYPE_PARAMS:
            params.update(self.ARCHETYPE_PARAMS[archetype])
        
        return params
    
    async def check_model_health(self, model_name: str) -> bool:
        """
        Check if model is loaded and healthy.
        
        Returns True if model is available.
        """
        if not OLLAMA_AVAILABLE:
            return False
        
        try:
            # Check if model is in loaded list
            models = await asyncio.to_thread(ollama.list)
            loaded = any(m['name'] == model_name for m in models.get('models', []))
            
            # Update health tracking
            if model_name not in self.model_health:
                self.model_health[model_name] = ModelHealth(
                    model_name=model_name,
                    available=loaded,
                    last_check=datetime.now()
                )
            else:
                self.model_health[model_name].available = loaded
                self.model_health[model_name].last_check = datetime.now()
            
            return loaded
        
        except Exception as e:
            print(f"Health check failed for {model_name}: {e}")
            return False
    
    async def load_model(self, model_name: str) -> bool:
        """
        Ensure model is loaded in Ollama.
        
        Returns True if model is loaded successfully.
        """
        if not OLLAMA_AVAILABLE:
            print("ERROR: Ollama not available")
            return False
        
        try:
            # Check if already loaded
            if await self.check_model_health(model_name):
                return True
            
            print(f"Loading model: {model_name}...")
            
            # Pull/load model (this will download if needed)
            await asyncio.to_thread(
                ollama.pull,
                model_name
            )
            
            self.loaded_models.add(model_name)
            return True
        
        except Exception as e:
            print(f"Failed to load model {model_name}: {e}")
            return False
    
    async def execute(self,
                     archetype: str,
                     query: str,
                     context_chunks: Optional[List[str]] = None,
                     system_prompt: Optional[str] = None) -> ExecutionResult:
        """
        Execute query with specified archetype.
        
        Args:
            archetype: Archetype name (e.g., 'mit_engineering')
            query: User query
            context_chunks: Relevant context from knowledge graph
            system_prompt: Optional system prompt override
        
        Returns:
            ExecutionResult with response and metadata
        """
        start_time = time.time()
        model_name = self.get_model_name(archetype)
        
        # Initialize result
        result = ExecutionResult(
            archetype=archetype,
            query=query,
            response="",
            status=ExecutionStatus.PENDING,
            latency_ms=0.0,
            model_name=model_name,
            context_chunks=context_chunks or []
        )
        
        # Extract base and voice
        if '+' in model_name:
            result.base_model, result.voice_adapter = model_name.split('+', 1)
        
        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            result.retry_count = attempt
            
            try:
                # Acquire semaphore for concurrency control
                async with self.semaphore:
                    result.status = ExecutionStatus.RUNNING
                    
                    # Ensure model is loaded
                    if not await self.load_model(model_name):
                        raise Exception(f"Failed to load model: {model_name}")
                    
                    # Build prompt with context
                    full_prompt = self._build_prompt(
                        query, 
                        context_chunks,
                        system_prompt
                    )
                    
                    # Get generation parameters
                    params = self.get_generation_params(archetype)
                    
                    # Execute with timeout
                    try:
                        response = await asyncio.wait_for(
                            self._execute_ollama(model_name, full_prompt, params),
                            timeout=self.timeout_seconds
                        )
                        
                        result.response = response
                        result.status = ExecutionStatus.SUCCESS
                        
                        # Calculate metrics
                        result.latency_ms = (time.time() - start_time) * 1000
                        result.tokens_generated = len(response.split())  # Rough estimate
                        result.tokens_per_second = (
                            result.tokens_generated / (result.latency_ms / 1000)
                            if result.latency_ms > 0 else 0
                        )
                        
                        # Update statistics
                        self.total_executions += 1
                        self.successful_executions += 1
                        self.total_latency_ms += result.latency_ms
                        self.total_tokens += result.tokens_generated
                        
                        # Update model health
                        if model_name in self.model_health:
                            health = self.model_health[model_name]
                            health.total_requests += 1
                            health.avg_latency_ms = (
                                (health.avg_latency_ms * (health.total_requests - 1) + 
                                 result.latency_ms) / health.total_requests
                            )
                            health.success_rate = (
                                (health.total_requests - health.failed_requests) / 
                                health.total_requests
                            )
                        
                        return result
                    
                    except asyncio.TimeoutError:
                        result.status = ExecutionStatus.TIMEOUT
                        result.error_message = f"Query timeout after {self.timeout_seconds}s"
                        raise
            
            except Exception as e:
                result.status = ExecutionStatus.RETRYING if attempt < self.max_retries - 1 else ExecutionStatus.FAILED
                result.error_message = str(e)
                
                # Update health
                if model_name in self.model_health:
                    self.model_health[model_name].failed_requests += 1
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    print(f"Execution failed (attempt {attempt + 1}/{self.max_retries}), "
                          f"retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    print(f"Execution failed after {self.max_retries} attempts: {e}")
        
        # All retries exhausted
        result.latency_ms = (time.time() - start_time) * 1000
        self.total_executions += 1
        self.failed_executions += 1
        
        return result
    
    async def _execute_ollama(self, 
                             model: str, 
                             prompt: str, 
                             params: Dict) -> str:
        """Execute query through Ollama API"""
        if not OLLAMA_AVAILABLE:
            raise Exception("Ollama not available")
        
        # Use ollama-python library for clean async execution
        response = await asyncio.to_thread(
            ollama.generate,
            model=model,
            prompt=prompt,
            options=params
        )
        
        return response['response']
    
    async def execute_streaming(self,
                               archetype: str,
                               query: str,
                               context_chunks: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        """
        Execute with streaming response.
        
        Yields response chunks as they're generated.
        """
        model_name = self.get_model_name(archetype)
        
        # Ensure model loaded
        if not await self.load_model(model_name):
            raise Exception(f"Failed to load model: {model_name}")
        
        # Build prompt
        full_prompt = self._build_prompt(query, context_chunks)
        params = self.get_generation_params(archetype)
        
        # Stream response
        if OLLAMA_AVAILABLE:
            stream = ollama.generate(
                model=model_name,
                prompt=full_prompt,
                options=params,
                stream=True
            )
            
            for chunk in stream:
                if 'response' in chunk:
                    yield chunk['response']
    
    def _build_prompt(self,
                     query: str,
                     context_chunks: Optional[List[str]] = None,
                     system_prompt: Optional[str] = None) -> str:
        """
        Build complete prompt with context injection.
        
        Format:
        [SYSTEM]
        {system_prompt or default}
        
        [CONTEXT]
        {context from knowledge graph}
        
        [QUERY]
        {user query}
        """
        parts = []
        
        # System prompt
        if system_prompt:
            parts.append(f"[SYSTEM]\n{system_prompt}\n")
        else:
            parts.append(
                "[SYSTEM]\n"
                "You are a vertex-tier expert providing institutional-grade knowledge. "
                "Answer with precision, depth, and clarity. "
                "Cite context when available.\n"
            )
        
        # Context from knowledge graph
        if context_chunks:
            context_text = "\n\n".join(context_chunks[:5])  # Top 5 chunks
            parts.append(f"[CONTEXT]\n{context_text}\n")
        
        # Query
        parts.append(f"[QUERY]\n{query}\n\n[RESPONSE]")
        
        return "\n".join(parts)
    
    def get_stats(self) -> Dict:
        """Get execution statistics"""
        avg_latency = (
            self.total_latency_ms / self.total_executions 
            if self.total_executions > 0 else 0
        )
        
        success_rate = (
            self.successful_executions / self.total_executions 
            if self.total_executions > 0 else 0
        )
        
        avg_tokens_per_second = (
            self.total_tokens / (self.total_latency_ms / 1000)
            if self.total_latency_ms > 0 else 0
        )
        
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': success_rate,
            'avg_latency_ms': avg_latency,
            'total_tokens': self.total_tokens,
            'avg_tokens_per_second': avg_tokens_per_second,
            'loaded_models': list(self.loaded_models),
            'model_health': {
                name: {
                    'available': health.available,
                    'avg_latency_ms': health.avg_latency_ms,
                    'success_rate': health.success_rate,
                    'total_requests': health.total_requests
                }
                for name, health in self.model_health.items()
            }
        }
    
    def visualize_stats(self) -> str:
        """Create ASCII visualization of execution statistics"""
        stats = self.get_stats()
        
        lines = []
        lines.append("=" * 80)
        lines.append("ARCHETYPE EXECUTOR - STATISTICS")
        lines.append("=" * 80)
        lines.append(f"\nTotal Executions: {stats['total_executions']}")
        lines.append(f"Success Rate: {stats['success_rate']:.1%}")
        lines.append(f"Avg Latency: {stats['avg_latency_ms']:.0f}ms")
        lines.append(f"Avg Tokens/sec: {stats['avg_tokens_per_second']:.1f}")
        
        if stats['model_health']:
            lines.append(f"\nModel Health:")
            for model, health in stats['model_health'].items():
                status = "✓" if health['available'] else "✗"
                lines.append(
                    f"  {status} {model}: {health['success_rate']:.1%} success, "
                    f"{health['avg_latency_ms']:.0f}ms avg"
                )
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


# ============================================================================
# BATCH EXECUTION
# ============================================================================

async def execute_batch(executor: ArchetypeExecutor,
                       queries: List[Tuple[str, str]],
                       context_map: Optional[Dict[str, List[str]]] = None) -> List[ExecutionResult]:
    """
    Execute multiple queries in parallel.
    
    Args:
        executor: ArchetypeExecutor instance
        queries: List of (archetype, query) tuples
        context_map: Optional dict mapping query -> context chunks
    
    Returns:
        List of ExecutionResults
    """
    context_map = context_map or {}
    
    tasks = []
    for archetype, query in queries:
        context = context_map.get(query, [])
        task = executor.execute(archetype, query, context)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    return [r for r in results if isinstance(r, ExecutionResult)]


# ============================================================================
# TESTING
# ============================================================================

async def test_executor():
    """Test archetype executor"""
    executor = ArchetypeExecutor(max_concurrent=2)
    
    # Test queries
    queries = [
        ("mit_engineering", "Design a low-cost water purification system"),
        ("caltech_physics", "Explain quantum entanglement"),
        ("harvard_med", "What causes Alzheimer's disease?"),
    ]
    
    print("\nTesting Archetype Executor")
    print("=" * 80)
    
    # Execute batch
    results = await execute_batch(executor, queries)
    
    # Display results
    for result in results:
        print(f"\n{result}")
        if result.status == ExecutionStatus.SUCCESS:
            print(f"Response: {result.response[:200]}...")
    
    # Display stats
    print(executor.visualize_stats())


if __name__ == "__main__":
    asyncio.run(test_executor())

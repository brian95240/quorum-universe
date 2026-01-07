#!/usr/bin/env python3
"""
Archetype Router - Intelligent Query Routing with Micro-Batching
Hyper-efficient, hyper-dynamic selection with warm circuits and collapse-to-zero
"""

import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import json

try:
    from ollama import chat
except ImportError:
    print("WARNING: ollama not found. Using simulation mode.")
    chat = None

from knowledge_graph import ARCHETYPES, KnowledgeGraph


# ============================================================================
# QUERY DECOMPOSITION
# ============================================================================

@dataclass
class QueryAtom:
    """Atomic semantic unit of a query"""
    text: str
    domains: List[str]
    dependencies: List[int] = field(default_factory=list)
    priority: float = 1.0
    complexity: float = 0.5
    
    def __hash__(self):
        return hash(self.text)


class QueryDecomposer:
    """Break complex queries into atomic units"""
    
    # Domain keywords for classification
    DOMAIN_KEYWORDS = {
        'physics': ['quantum', 'particle', 'force', 'energy', 'relativity', 'cosmology'],
        'mathematics': ['proof', 'theorem', 'equation', 'algebra', 'topology', 'calculus'],
        'engineering': ['design', 'build', 'system', 'optimize', 'constraint', 'prototype'],
        'medicine': ['diagnose', 'treatment', 'symptom', 'clinical', 'patient', 'disease'],
        'law': ['legal', 'precedent', 'court', 'rights', 'statute', 'liability'],
        'computer_science': ['algorithm', 'code', 'software', 'data', 'machine learning'],
        'economics': ['market', 'price', 'incentive', 'cost', 'trade', 'policy'],
        'philosophy': ['ethics', 'metaphysics', 'epistemology', 'logic', 'morality'],
        'history': ['historical', 'century', 'civilization', 'empire', 'revolution'],
        'design': ['aesthetic', 'form', 'function', 'user', 'interface', 'visual'],
        'strategy': ['tactics', 'advantage', 'opponent', 'plan', 'maneuver'],
        'consciousness': ['awareness', 'perception', 'experience', 'phenomenology', 'mind'],
        'ecology': ['ecosystem', 'sustainable', 'environment', 'species', 'biodiversity'],
        'complexity': ['emergence', 'network', 'chaos', 'nonlinear', 'self-organization']
    }
    
    def decompose(self, query: str) -> List[QueryAtom]:
        """
        Decompose query into atoms.
        Simple implementation - in production, use spaCy + transformers.
        """
        # For now, split on conjunctions and create atoms
        # In production: use dependency parsing, coreference resolution
        
        separators = [' and ', ', ', ' then ', ' also ', ' plus ', ' with ']
        
        parts = [query]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        atoms = []
        for i, part in enumerate(parts):
            if not part.strip():
                continue
            
            domains = self._classify_domains(part)
            complexity = self._calculate_complexity(part)
            
            atoms.append(QueryAtom(
                text=part.strip(),
                domains=domains,
                dependencies=[],
                priority=1.0,
                complexity=complexity
            ))
        
        # Build dependency graph
        atoms = self._build_dependencies(atoms)
        
        return atoms
    
    def _classify_domains(self, text: str) -> List[str]:
        """Classify text into domains based on keywords"""
        text_lower = text.lower()
        matches = []
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                matches.append(domain)
        
        return matches if matches else ['general']
    
    def _calculate_complexity(self, text: str) -> float:
        """Estimate query complexity (0.0-1.0)"""
        # Simple heuristic: length + technical terms + question depth
        words = text.split()
        
        # Length factor
        length_score = min(len(words) / 50, 1.0)
        
        # Technical terms
        technical_terms = ['algorithm', 'theorem', 'mechanism', 'synthesis', 
                          'optimization', 'differential', 'stochastic']
        tech_score = sum(1 for term in technical_terms if term in text.lower()) / 5
        
        # Question depth (how, why, explain vs what, is)
        depth_words = ['how', 'why', 'explain', 'analyze', 'compare', 'synthesize']
        depth_score = 1.0 if any(w in text.lower() for w in depth_words) else 0.5
        
        return (length_score * 0.3 + tech_score * 0.3 + depth_score * 0.4)
    
    def _build_dependencies(self, atoms: List[QueryAtom]) -> List[QueryAtom]:
        """Identify dependencies between atoms"""
        # Simple heuristic: if atom B references concepts from atom A, A -> B
        for i, atom_a in enumerate(atoms):
            for j, atom_b in enumerate(atoms[i+1:], start=i+1):
                # Check if any words from A appear in B (dependency signal)
                words_a = set(atom_a.text.lower().split())
                words_b = set(atom_b.text.lower().split())
                
                if len(words_a & words_b) > 2:  # Significant overlap
                    atom_b.dependencies.append(i)
        
        return atoms


# ============================================================================
# ARCHETYPE SELECTOR
# ============================================================================

class ArchetypeSelector:
    """Intelligent archetype selection based on query analysis"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        
        # Domain -> Archetype mapping
        self.domain_map = self._build_domain_map()
        
        # Co-activation matrix (learned from usage)
        self.coactivation = np.zeros((20, 20))
        self.archetype_to_idx = {name: i for i, name in enumerate(ARCHETYPES.keys())}
        self.idx_to_archetype = {i: name for name, i in self.archetype_to_idx.items()}
    
    def _build_domain_map(self) -> Dict[str, List[str]]:
        """Map domains to relevant archetypes"""
        mapping = {}
        
        for archetype, data in ARCHETYPES.items():
            for domain in data['domains']:
                if domain not in mapping:
                    mapping[domain] = []
                mapping[domain].append(archetype)
        
        return mapping
    
    def select(self, atom: QueryAtom, context: Dict) -> List[str]:
        """
        Select 1-3 archetypes for a query atom.
        Returns ranked list of archetype names.
        """
        candidates = {}
        
        # Priority 1: Explicit mention
        for archetype in ARCHETYPES.keys():
            if archetype.replace('_', ' ') in atom.text.lower():
                return [archetype]
        
        # Priority 2: Domain matching
        for domain in atom.domains:
            if domain in self.domain_map:
                for archetype in self.domain_map[domain]:
                    candidates[archetype] = candidates.get(archetype, 0) + 1.0
        
        # Priority 3: Temporal context
        hour = context.get('hour', 12)
        if hour < 9:  # Morning - practical
            for arch in ['mit_engineering', 'bauhaus_design', 'stanford_cs']:
                candidates[arch] = candidates.get(arch, 0) + 0.3
        elif hour > 20:  # Evening - theoretical
            for arch in ['caltech_physics', 'princeton_math', 'oxford_classics']:
                candidates[arch] = candidates.get(arch, 0) + 0.3
        
        # Priority 4: Complexity boost (Mensa for high complexity)
        if atom.complexity > 0.7:
            candidates['mensa_orthogonal'] = candidates.get('mensa_orthogonal', 0) + 0.5
        
        # Priority 5: History-based (previous queries)
        last_queries = context.get('last_queries', [])
        if last_queries:
            # Boost archetypes related to recent queries
            for prev_arch in context.get('recent_archetypes', []):
                if prev_arch in self.archetype_to_idx:
                    idx = self.archetype_to_idx[prev_arch]
                    # Find frequently co-activated archetypes
                    coactive = np.argsort(self.coactivation[idx])[-3:]
                    for co_idx in coactive:
                        co_arch = self.idx_to_archetype[co_idx]
                        candidates[co_arch] = candidates.get(co_arch, 0) + 0.2
        
        # Rank and return top 3
        if not candidates:
            # Default: use general reasoning
            return ['caltech_physics', 'mit_engineering']
        
        ranked = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return [arch for arch, score in ranked[:3]]
    
    def update_coactivation(self, archetypes_used: List[str]):
        """Update co-activation matrix from actual usage"""
        for i, arch_a in enumerate(archetypes_used):
            if arch_a not in self.archetype_to_idx:
                continue
            idx_a = self.archetype_to_idx[arch_a]
            
            for arch_b in archetypes_used[i+1:]:
                if arch_b not in self.archetype_to_idx:
                    continue
                idx_b = self.archetype_to_idx[arch_b]
                
                # Increment both directions
                self.coactivation[idx_a][idx_b] += 1
                self.coactivation[idx_b][idx_a] += 1


# ============================================================================
# WARM CIRCUIT OPTIMIZER
# ============================================================================

class WarmCircuitOptimizer:
    """Predictive loading of archetypes based on co-activation"""
    
    def __init__(self, selector: ArchetypeSelector):
        self.selector = selector
        self.loaded_archetypes: Set[str] = set()
        self.load_times: Dict[str, float] = {}
        
        # Timing constants
        self.warm_load_time = 0.3  # seconds (background load)
        self.cold_load_time = 3.2  # seconds (on-demand load)
        self.memory_per_archetype = 38  # GB
        self.max_memory = 128  # GB available
    
    def should_warm_load(self, current: str, predicted: str) -> bool:
        """Decide if we should pre-load predicted archetype"""
        if predicted in self.loaded_archetypes:
            return False  # Already loaded
        
        # Check memory availability
        if len(self.loaded_archetypes) * self.memory_per_archetype >= self.max_memory:
            return False  # Out of memory
        
        # Get probability from co-activation matrix
        if current not in self.selector.archetype_to_idx:
            return False
        
        curr_idx = self.selector.archetype_to_idx[current]
        pred_idx = self.selector.archetype_to_idx.get(predicted)
        
        if pred_idx is None:
            return False
        
        # Calculate probability
        row_sum = self.selector.coactivation[curr_idx].sum()
        if row_sum == 0:
            prob = 0.1  # Default low probability
        else:
            prob = self.selector.coactivation[curr_idx][pred_idx] / row_sum
        
        # Cost-benefit analysis
        expected_benefit = prob * (self.cold_load_time - self.warm_load_time)
        
        # Warm load if expected benefit > 1 second
        return expected_benefit > 1.0
    
    def predict_next(self, current: str, top_k: int = 2) -> List[str]:
        """Predict next K most likely archetypes"""
        if current not in self.selector.archetype_to_idx:
            return []
        
        curr_idx = self.selector.archetype_to_idx[current]
        probs = self.selector.coactivation[curr_idx]
        
        if probs.sum() == 0:
            return []
        
        top_indices = np.argsort(probs)[-top_k:][::-1]
        return [self.selector.idx_to_archetype[i] for i in top_indices]
    
    async def warm_load(self, archetype: str):
        """Background load of archetype"""
        print(f"  🔥 Warm-loading {archetype}...")
        await asyncio.sleep(self.warm_load_time)  # Simulate load time
        self.loaded_archetypes.add(archetype)
        self.load_times[archetype] = time.time()
    
    def unload_stale(self, inactive_threshold: float = 30.0):
        """Unload archetypes that haven't been used recently"""
        current_time = time.time()
        to_unload = []
        
        for archetype, load_time in self.load_times.items():
            if current_time - load_time > inactive_threshold:
                to_unload.append(archetype)
        
        for archetype in to_unload:
            print(f"  ❄️  Unloading stale {archetype}")
            self.loaded_archetypes.discard(archetype)
            del self.load_times[archetype]


# ============================================================================
# QUALITY ASSESSOR
# ============================================================================

class QualityAssessor:
    """Assess quality of generated responses"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
    
    def assess(self, response: str, query_atom: QueryAtom) -> float:
        """
        Multi-factor quality score (0.0-1.0).
        """
        # Factor 1: Length (too short or too long is bad)
        word_count = len(response.split())
        length_score = 1.0
        if word_count < 20:
            length_score = word_count / 20
        elif word_count > 500:
            length_score = max(0.5, 1.0 - (word_count - 500) / 500)
        
        # Factor 2: Relevance (keywords from query appear in response)
        query_words = set(query_atom.text.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words)
        relevance_score = min(overlap / max(len(query_words), 1), 1.0)
        
        # Factor 3: Specificity (avoids generic phrases)
        generic_phrases = ['it depends', 'in general', 'many factors', 'complex topic']
        generic_count = sum(1 for phrase in generic_phrases if phrase in response.lower())
        specificity_score = max(0.3, 1.0 - generic_count * 0.2)
        
        # Factor 4: Structure (has clear organization)
        structure_score = 0.7  # Default
        if any(marker in response for marker in ['1.', 'First,', 'However,', 'Therefore,']):
            structure_score = 1.0
        
        # Weighted combination
        quality = (
            0.20 * length_score +
            0.35 * relevance_score +
            0.25 * specificity_score +
            0.20 * structure_score
        )
        
        return quality


# ============================================================================
# ARCHETYPE EXECUTOR
# ============================================================================

class ArchetypeExecutor:
    """Execute queries through archetypes (Ollama integration)"""
    
    def __init__(self):
        self.simulation_mode = (chat is None)
        
        # Base models (composite LoRA architecture)
        self.base_models = {
            'stem_core': ['mit_engineering', 'caltech_physics', 'princeton_math', 
                         'stanford_cs', 'complexity_science'],
            'life_systems': ['harvard_med', 'broad_genomics', 'berkeley_psychedelics', 
                           'longevity_research'],
            'human_systems': ['yale_law', 'chicago_economics', 'oxford_classics'],
            'non_western': ['beijing_classical', 'baghdad_golden', 'nalanda_vedic'],
            'creative_synthesis': ['bauhaus_design', 'hacker_insurgent', 
                                  'indigenous_ecology', 'mensa_orthogonal'],
            'applied_tech': ['stanford_cs', 'hacker_insurgent', 'ai_safety']
        }
        
        # Reverse map: archetype -> base model
        self.archetype_to_base = {}
        for base, archetypes in self.base_models.items():
            for arch in archetypes:
                self.archetype_to_base[arch] = base
    
    def execute(
        self,
        archetype: str,
        query_atom: QueryAtom,
        knowledge_chunks: List[Dict],
        context: Optional[str] = None
    ) -> Dict:
        """
        Execute query through archetype.
        Returns: {archetype, response, sources, time}
        """
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(query_atom, knowledge_chunks, context)
        
        # Get archetype config
        config = ARCHETYPES.get(archetype, ARCHETYPES['caltech_physics'])
        
        if self.simulation_mode:
            # Simulation mode (no Ollama)
            response = self._simulate_response(archetype, query_atom, knowledge_chunks)
        else:
            # Real mode (Ollama)
            base_model = self.archetype_to_base.get(archetype, 'stem_core')
            model_name = f"{base_model}+{archetype}"
            
            try:
                result = chat(
                    model=model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                    options={'temperature': config['temperature']}
                )
                response = result['message']['content']
            except Exception as e:
                print(f"WARNING: Ollama execution failed: {e}")
                response = self._simulate_response(archetype, query_atom, knowledge_chunks)
        
        execution_time = time.time() - start_time
        
        return {
            'archetype': archetype,
            'atom': query_atom.text,
            'response': response,
            'sources': [c['source'] for c in knowledge_chunks],
            'time': execution_time,
            'style': config['style']
        }
    
    def _build_prompt(
        self,
        atom: QueryAtom,
        chunks: List[Dict],
        context: Optional[str] = None
    ) -> str:
        """Build prompt with knowledge context"""
        prompt_parts = []
        
        # Add previous context if available
        if context:
            prompt_parts.append(f"Previous context:\n{context}\n")
        
        # Add relevant knowledge
        if chunks:
            prompt_parts.append("Relevant knowledge:\n")
            for i, chunk in enumerate(chunks[:5], 1):  # Top 5 chunks
                prompt_parts.append(f"[{i}] {chunk['text'][:300]}...")
        
        # Add query
        prompt_parts.append(f"\nQuery: {atom.text}")
        prompt_parts.append("\nProvide a clear, expert-level response:")
        
        return "\n".join(prompt_parts)
    
    def _simulate_response(
        self,
        archetype: str,
        atom: QueryAtom,
        chunks: List[Dict]
    ) -> str:
        """Simulate response when Ollama is unavailable"""
        config = ARCHETYPES[archetype]
        
        # Generate a style-appropriate response
        response = f"[{config['style']}]\n\n"
        response += f"Regarding '{atom.text}':\n\n"
        
        if chunks:
            response += f"Based on {len(chunks)} relevant sources from {archetype}, "
        
        response += f"the analysis suggests [simulated expert response in {archetype} style]."
        
        return response


# ============================================================================
# MICRO-BATCH PROCESSOR
# ============================================================================

class MicroBatchProcessor:
    """Process complex queries with parallel micro-batching"""
    
    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        selector: ArchetypeSelector,
        executor: ArchetypeExecutor,
        assessor: QualityAssessor,
        optimizer: WarmCircuitOptimizer
    ):
        self.kg = knowledge_graph
        self.selector = selector
        self.executor = executor
        self.assessor = assessor
        self.optimizer = optimizer
    
    async def process(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process query with micro-batching and parallel execution.
        """
        print(f"\n{'='*80}")
        print(f"PROCESSING QUERY: {query}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Step 1: Decompose query
        decomposer = QueryDecomposer()
        atoms = decomposer.decompose(query)
        
        print(f"Decomposed into {len(atoms)} atoms:")
        for i, atom in enumerate(atoms, 1):
            print(f"  {i}. {atom.text}")
            print(f"     Domains: {', '.join(atom.domains)}")
            print(f"     Complexity: {atom.complexity:.2f}")
        print()
        
        # Step 2: Build dependency batches
        batches = self._build_batches(atoms)
        
        print(f"Execution plan: {len(batches)} batches")
        for i, batch in enumerate(batches, 1):
            print(f"  Batch {i}: {len(batch)} atoms (parallel)")
        print()
        
        # Step 3: Execute batches
        results = {}
        context = context or {}
        
        for batch_num, batch in enumerate(batches, 1):
            print(f"→ Executing Batch {batch_num}/{len(batches)}...")
            
            batch_results = await self._execute_batch(
                batch,
                results,  # Pass previous results as context
                context
            )
            
            results.update(batch_results)
        
        # Step 4: Synthesize results
        synthesis = self._synthesize(results, query)
        
        total_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"EXECUTION COMPLETE: {total_time:.2f}s")
        print(f"{'='*80}\n")
        
        # Update co-activation matrix
        archetypes_used = list(set([r['archetype'] for r in results.values()]))
        self.selector.update_coactivation(archetypes_used)
        
        return {
            'query': query,
            'atoms': [atom.text for atom in atoms],
            'results': results,
            'synthesis': synthesis,
            'archetypes_used': archetypes_used,
            'execution_time': total_time,
            'num_batches': len(batches)
        }
    
    def _build_batches(self, atoms: List[QueryAtom]) -> List[List[QueryAtom]]:
        """
        Build execution batches based on dependencies.
        Atoms in same batch can be executed in parallel.
        """
        # Topological sort with batching
        batches = []
        processed = set()
        
        while len(processed) < len(atoms):
            # Find all atoms whose dependencies are satisfied
            current_batch = []
            for i, atom in enumerate(atoms):
                if i in processed:
                    continue
                
                deps_satisfied = all(dep in processed for dep in atom.dependencies)
                if deps_satisfied:
                    current_batch.append(atom)
            
            if not current_batch:
                # Circular dependency or error - add remaining
                current_batch = [atoms[i] for i in range(len(atoms)) if i not in processed]
            
            batches.append(current_batch)
            processed.update(atoms.index(atom) for atom in current_batch)
        
        return batches
    
    async def _execute_batch(
        self,
        batch: List[QueryAtom],
        previous_results: Dict,
        context: Dict
    ) -> Dict:
        """Execute a batch of atoms in parallel"""
        tasks = []
        
        for atom in batch:
            task = self._execute_atom(atom, previous_results, context)
            tasks.append(task)
        
        # Execute in parallel
        results = await asyncio.gather(*tasks)
        
        # Convert list to dict keyed by atom text
        return {atom.text: result for atom, result in zip(batch, results)}
    
    async def _execute_atom(
        self,
        atom: QueryAtom,
        previous_results: Dict,
        context: Dict
    ) -> Dict:
        """
        Execute single atom with collapse-to-zero logic.
        Try 1 archetype first, expand if quality insufficient.
        """
        # Select archetypes
        candidates = self.selector.select(atom, context)
        
        # Phase 1: Try single archetype (collapse-to-zero)
        best_archetype = candidates[0]
        
        print(f"  → Trying {best_archetype} for: {atom.text[:50]}...")
        
        # Retrieve knowledge
        chunks = self.kg.semantic_search(
            atom.text,
            top_k=15,
            archetype_filter=best_archetype
        )
        
        # Build context from previous results
        prev_context = self._build_context(atom, previous_results)
        
        # Execute
        result = self.executor.execute(
            best_archetype,
            atom,
            chunks,
            context=prev_context
        )
        
        # Assess quality
        quality = self.assessor.assess(result['response'], atom)
        result['quality'] = quality
        
        print(f"    Quality: {quality:.2f}")
        
        # If quality sufficient, return
        if quality > 0.80:
            print(f"    ✓ Sufficient quality, collapsed to 1 archetype")
            
            # Warm-load predicted next
            predicted = self.optimizer.predict_next(best_archetype, top_k=1)
            if predicted and self.optimizer.should_warm_load(best_archetype, predicted[0]):
                asyncio.create_task(self.optimizer.warm_load(predicted[0]))
            
            return result
        
        # Phase 2: Expand to pair (if quality insufficient)
        if len(candidates) > 1 and quality < 0.80:
            second_archetype = candidates[1]
            
            print(f"    ⚠ Quality low, expanding to {second_archetype}...")
            
            # Get chunks from second archetype
            chunks_2 = self.kg.semantic_search(
                atom.text,
                top_k=10,
                archetype_filter=second_archetype
            )
            
            # Execute second
            result_2 = self.executor.execute(
                second_archetype,
                atom,
                chunks_2,
                context=result['response']  # Use first result as context
            )
            
            # Merge results
            merged_response = self._merge_responses([result, result_2])
            quality_2 = self.assessor.assess(merged_response, atom)
            
            print(f"    Quality (merged): {quality_2:.2f}")
            
            if quality_2 > quality:
                result['response'] = merged_response
                result['archetypes'] = [best_archetype, second_archetype]
                result['quality'] = quality_2
                print(f"    ✓ Improved with 2 archetypes")
            
        return result
    
    def _build_context(self, atom: QueryAtom, previous_results: Dict) -> Optional[str]:
        """Build context from previous results"""
        if not previous_results or not atom.dependencies:
            return None
        
        context_parts = []
        for dep_idx in atom.dependencies:
            # Find result from dependency
            for prev_atom_text, prev_result in previous_results.items():
                # Simplified - in production use proper indexing
                context_parts.append(f"[{prev_result['archetype']}]: {prev_result['response'][:200]}...")
        
        return "\n".join(context_parts) if context_parts else None
    
    def _merge_responses(self, results: List[Dict]) -> str:
        """Merge multiple archetype responses"""
        merged = []
        
        for result in results:
            arch_name = result['archetype'].replace('_', ' ').title()
            merged.append(f"[{arch_name} Perspective]\n{result['response']}\n")
        
        return "\n".join(merged)
    
    def _synthesize(self, results: Dict, original_query: str) -> str:
        """Synthesize all results into coherent answer"""
        synthesis_parts = []
        
        synthesis_parts.append(f"Analysis of: {original_query}\n")
        
        # Group by archetype
        by_archetype = {}
        for atom_text, result in results.items():
            arch = result['archetype']
            if arch not in by_archetype:
                by_archetype[arch] = []
            by_archetype[arch].append(result)
        
        # Present synthesis
        for archetype, atom_results in by_archetype.items():
            arch_name = archetype.replace('_', ' ').title()
            synthesis_parts.append(f"\n{arch_name} Analysis:")
            
            for result in atom_results:
                synthesis_parts.append(f"  • {result['response'][:200]}...")
        
        synthesis_parts.append("\n[End Synthesis]")
        
        return "\n".join(synthesis_parts)


# ============================================================================
# MAIN ROUTER CLASS
# ============================================================================

class ArchetypeRouter:
    """Main entry point for archetype routing"""
    
    def __init__(self, db_config: Dict):
        self.kg = KnowledgeGraph(db_config)
        self.selector = ArchetypeSelector(self.kg)
        self.executor = ArchetypeExecutor()
        self.assessor = QualityAssessor(self.kg)
        self.optimizer = WarmCircuitOptimizer(self.selector)
        self.processor = MicroBatchProcessor(
            self.kg,
            self.selector,
            self.executor,
            self.assessor,
            self.optimizer
        )
    
    async def route(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Main routing interface"""
        return await self.processor.process(query, context)
    
    def close(self):
        """Cleanup"""
        self.kg.close()


# ============================================================================
# MAIN (FOR TESTING)
# ============================================================================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Archetype Router')
    parser.add_argument('query', nargs='*', help='Query to route')
    parser.add_argument('--context', type=str, help='Context JSON')
    
    args = parser.parse_args()
    
    if not args.query:
        print("Usage: python archetype_router.py 'your query here'")
        return
    
    query = ' '.join(args.query)
    context = json.loads(args.context) if args.context else {}
    
    # Database config
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ambient_intelligence',
        'user': 'puck_user',
        'password': 'change_me_in_production'
    }
    
    router = ArchetypeRouter(DB_CONFIG)
    
    try:
        result = await router.route(query, context)
        
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        print(f"\nSynthesis:\n{result['synthesis']}")
        print(f"\nArchetypes used: {', '.join(result['archetypes_used'])}")
        print(f"Total time: {result['execution_time']:.2f}s")
        print(f"Batches: {result['num_batches']}")
        
    finally:
        router.close()


if __name__ == '__main__':
    asyncio.run(main())

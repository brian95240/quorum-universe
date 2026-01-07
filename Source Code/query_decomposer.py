#!/usr/bin/env python3
"""
Query Decomposer - Production Implementation
Breaks complex queries into atomic semantic units using NLP + clustering

Techniques:
- Dependency parsing (spaCy)
- Semantic clustering (HDBSCAN on sentence embeddings)
- Domain extraction (NER + embedding similarity)
- Dependency graph construction
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

# Core NLP
try:
    import spacy
    from spacy.tokens import Doc, Span, Token
    NLP_AVAILABLE = True
except ImportError:
    print("WARNING: spaCy not available. Install: pip install spacy && python -m spacy download en_core_web_lg")
    NLP_AVAILABLE = False

# Clustering
try:
    import hdbscan
    CLUSTERING_AVAILABLE = True
except ImportError:
    print("WARNING: HDBSCAN not available. Install: pip install hdbscan")
    CLUSTERING_AVAILABLE = False

# Embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    print("WARNING: SentenceTransformers not available. Install: pip install sentence-transformers")
    EMBEDDINGS_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class QueryAtom:
    """
    Atomic semantic unit of a query.
    
    Represents a single concept or question that can be addressed independently
    by one or more archetypes.
    """
    text: str                          # The atomic query text
    domains: List[str]                 # Relevant knowledge domains
    dependencies: List[int] = field(default_factory=list)  # Indices of prerequisite atoms
    priority: float = 1.0              # Execution priority (0.0-1.0)
    complexity: float = 0.5            # Estimated complexity (0.0-1.0)
    embedding: Optional[np.ndarray] = None  # Semantic embedding
    
    # Metadata
    original_span: Tuple[int, int] = (0, 0)  # Character span in original query
    entity_types: List[str] = field(default_factory=list)  # Named entities
    key_phrases: List[str] = field(default_factory=list)  # Important phrases
    
    def __hash__(self):
        return hash(self.text)
    
    def __repr__(self):
        deps = f", deps={self.dependencies}" if self.dependencies else ""
        return f"QueryAtom('{self.text[:50]}...', domains={self.domains}{deps})"


# ============================================================================
# QUERY DECOMPOSER
# ============================================================================

class QueryDecomposer:
    """
    Production-ready query decomposition with semantic clustering.
    
    Algorithm:
    1. Parse query with spaCy (dependencies, entities)
    2. Extract candidate phrases (noun chunks, verb phrases, clauses)
    3. Embed phrases with sentence-transformers
    4. Cluster with HDBSCAN to group semantically related content
    5. Create atomic queries from clusters
    6. Build dependency graph
    7. Calculate complexity scores
    """
    
    # Domain classification keywords (expanded from router)
    DOMAIN_KEYWORDS = {
        'physics': ['quantum', 'particle', 'force', 'energy', 'relativity', 'cosmology', 
                    'entropy', 'momentum', 'electromagnetism', 'thermodynamics', 'photon',
                    'wave', 'nuclear', 'atomic', 'gravitational', 'electromagnetic'],
        'mathematics': ['proof', 'theorem', 'equation', 'algebra', 'topology', 'calculus',
                       'derivative', 'integral', 'matrix', 'vector', 'polynomial', 'geometric',
                       'logarithm', 'exponential', 'differential', 'statistical', 'probability'],
        'engineering': ['design', 'build', 'system', 'optimize', 'constraint', 'prototype',
                       'mechanical', 'electrical', 'structural', 'optimize', 'efficiency',
                       'fabricate', 'manufacture', 'tolerance', 'specification', 'blueprint'],
        'medicine': ['diagnose', 'treatment', 'symptom', 'clinical', 'patient', 'disease',
                    'therapeutic', 'pharmaceutical', 'pathology', 'diagnosis', 'prognosis',
                    'syndrome', 'disorder', 'infection', 'immune', 'metabolic', 'genetic'],
        'genomics': ['gene', 'dna', 'rna', 'protein', 'genome', 'sequencing', 'mutation',
                    'chromosome', 'allele', 'expression', 'transcription', 'crispr', 'genomic'],
        'law': ['legal', 'precedent', 'court', 'rights', 'statute', 'liability',
                'jurisdiction', 'litigation', 'defendant', 'plaintiff', 'constitutional',
                'regulatory', 'contract', 'tort', 'criminal', 'civil'],
        'computer_science': ['algorithm', 'code', 'software', 'data', 'machine learning',
                            'neural network', 'database', 'compiler', 'runtime', 'recursive',
                            'api', 'framework', 'protocol', 'encryption', 'distributed'],
        'economics': ['market', 'price', 'incentive', 'cost', 'trade', 'policy',
                     'supply', 'demand', 'equilibrium', 'inflation', 'gdp', 'fiscal',
                     'monetary', 'elasticity', 'utility', 'capital', 'investment'],
        'philosophy': ['ethics', 'metaphysics', 'epistemology', 'logic', 'morality',
                      'ontology', 'existential', 'phenomenology', 'deontological',
                      'consequentialist', 'virtue', 'dialectic', 'categorical'],
        'history': ['historical', 'century', 'civilization', 'empire', 'revolution',
                   'dynasty', 'era', 'period', 'ancient', 'medieval', 'renaissance',
                   'colonial', 'reformation', 'enlightenment', 'archaeological'],
        'design': ['aesthetic', 'form', 'function', 'user', 'interface', 'visual',
                  'typography', 'composition', 'layout', 'usability', 'minimalist',
                  'bauhaus', 'modernist', 'responsive', 'interaction'],
        'strategy': ['tactics', 'advantage', 'opponent', 'plan', 'maneuver',
                    'competitive', 'positioning', 'leverage', 'asymmetric', 'game theory',
                    'zero-sum', 'nash equilibrium', 'dominant strategy'],
        'consciousness': ['awareness', 'perception', 'experience', 'phenomenology', 'mind',
                         'qualia', 'subjective', 'intentionality', 'embodied', 'cognitive',
                         'neural correlates', 'consciousness', 'sentience'],
        'ecology': ['ecosystem', 'sustainable', 'environment', 'species', 'biodiversity',
                   'habitat', 'conservation', 'ecological', 'trophic', 'symbiotic',
                   'endemic', 'invasive', 'keystone', 'resilience'],
        'complexity': ['emergence', 'network', 'chaos', 'nonlinear', 'self-organization',
                      'fractal', 'attractor', 'bifurcation', 'dynamical systems',
                      'phase transition', 'critical', 'scaling', 'power law'],
        'psychedelics': ['psychedelic', 'entheogen', 'psilocybin', 'lsd', 'dmt', 'ayahuasca',
                        'mystical', 'neuroplasticity', 'serotonin', '5-ht2a', 'default mode'],
        'longevity': ['aging', 'senescence', 'lifespan', 'healthspan', 'telomere',
                     'autophagy', 'mitochondrial', 'caloric restriction', 'rapamycin',
                     'nad+', 'metformin', 'gerontology'],
    }
    
    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        'low': ['what', 'is', 'define', 'simple', 'basic'],
        'medium': ['how', 'why', 'explain', 'describe', 'compare'],
        'high': ['analyze', 'synthesize', 'evaluate', 'design', 'optimize', 'prove',
                'critique', 'innovate', 'transform', 'reconcile']
    }
    
    def __init__(self, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 spacy_model: str = "en_core_web_lg",
                 min_cluster_size: int = 2,
                 min_samples: int = 1):
        """
        Initialize decomposer with NLP and clustering models.
        
        Args:
            embedding_model: Sentence transformer model name
            spacy_model: spaCy language model
            min_cluster_size: Minimum cluster size for HDBSCAN
            min_samples: Minimum samples for core points in HDBSCAN
        """
        self.embedding_model_name = embedding_model
        self.spacy_model_name = spacy_model
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        
        # Lazy loading of heavy models
        self._nlp = None
        self._embedder = None
        self._clusterer = None
        
        # Domain embeddings cache (for similarity matching)
        self._domain_embeddings = {}
    
    @property
    def nlp(self):
        """Lazy load spaCy model"""
        if self._nlp is None:
            if not NLP_AVAILABLE:
                raise RuntimeError("spaCy not available. Install: pip install spacy && python -m spacy download en_core_web_lg")
            try:
                self._nlp = spacy.load(self.spacy_model_name)
            except OSError:
                print(f"Downloading spaCy model {self.spacy_model_name}...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", self.spacy_model_name])
                self._nlp = spacy.load(self.spacy_model_name)
        return self._nlp
    
    @property
    def embedder(self):
        """Lazy load sentence transformer"""
        if self._embedder is None:
            if not EMBEDDINGS_AVAILABLE:
                raise RuntimeError("SentenceTransformers not available. Install: pip install sentence-transformers")
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder
    
    def decompose(self, query: str, context: Optional[Dict] = None) -> List[QueryAtom]:
        """
        Main decomposition pipeline.
        
        Args:
            query: Natural language query
            context: Optional context (previous queries, user preferences, etc.)
            
        Returns:
            List of QueryAtom objects representing atomic semantic units
        """
        # Handle simple queries (no decomposition needed)
        if len(query.split()) < 5:
            atom = self._create_simple_atom(query)
            return [atom]
        
        # Parse query with spaCy
        doc = self.nlp(query)
        
        # Extract candidate phrases
        phrases = self._extract_phrases(doc)
        
        if len(phrases) <= 1:
            # Single concept query
            atom = self._create_simple_atom(query)
            return [atom]
        
        # Cluster phrases semantically
        clusters = self._cluster_phrases(phrases, doc)
        
        # Create atoms from clusters
        atoms = self._create_atoms_from_clusters(clusters, doc, query)
        
        # Build dependency graph
        atoms = self._build_dependencies(atoms, doc)
        
        # Calculate priorities
        atoms = self._calculate_priorities(atoms)
        
        return atoms
    
    def _create_simple_atom(self, text: str) -> QueryAtom:
        """Create a single atom for simple queries"""
        domains = self._classify_domains(text)
        complexity = self._calculate_complexity(text)
        embedding = self.embedder.encode(text)
        
        return QueryAtom(
            text=text.strip(),
            domains=domains,
            complexity=complexity,
            embedding=embedding,
            priority=1.0
        )
    
    def _extract_phrases(self, doc: Doc) -> List[Tuple[str, Span]]:
        """
        Extract candidate phrases from parsed document.
        
        Returns list of (text, span) tuples.
        """
        phrases = []
        
        # 1. Noun chunks (subjects, objects)
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:  # Filter single words
                phrases.append((chunk.text, chunk))
        
        # 2. Verb phrases (actions, processes)
        for token in doc:
            if token.pos_ == 'VERB':
                # Get verb + direct objects + prepositional phrases
                verb_phrase = self._get_verb_phrase(token)
                if verb_phrase and len(verb_phrase.text.split()) >= 2:
                    phrases.append((verb_phrase.text, verb_phrase))
        
        # 3. Clauses (from sentence structure)
        for sent in doc.sents:
            # Look for coordinating conjunctions (and, or, but)
            for token in sent:
                if token.dep_ == 'cc':  # Coordinating conjunction
                    # Split on conjunction
                    left = doc[sent.start:token.i]
                    right = doc[token.i+1:sent.end]
                    
                    if len(left.text.split()) >= 2:
                        phrases.append((left.text, left))
                    if len(right.text.split()) >= 2:
                        phrases.append((right.text, right))
        
        # 4. Named entity contexts
        for ent in doc.ents:
            # Get context around entity (entity + verb + related words)
            context = self._get_entity_context(ent, doc)
            if context and len(context.text.split()) >= 2:
                phrases.append((context.text, context))
        
        # Deduplicate by text similarity
        phrases = self._deduplicate_phrases(phrases)
        
        return phrases
    
    def _get_verb_phrase(self, verb: Token) -> Optional[Span]:
        """Extract full verb phrase including objects and modifiers"""
        start = verb.i
        end = verb.i + 1
        
        # Extend right to include objects and prep phrases
        for child in verb.children:
            if child.dep_ in ['dobj', 'pobj', 'prep', 'advmod', 'acomp']:
                end = max(end, child.i + 1)
                # Include children of objects
                for grandchild in child.subtree:
                    end = max(end, grandchild.i + 1)
        
        # Extend left to include subjects and modifiers
        for child in verb.children:
            if child.dep_ in ['nsubj', 'nsubjpass', 'aux', 'neg']:
                start = min(start, child.i)
        
        if end - start <= 1:
            return None
        
        return verb.doc[start:end]
    
    def _get_entity_context(self, entity: Span, doc: Doc) -> Optional[Span]:
        """Get contextual phrase around named entity"""
        # Find the sentence containing the entity
        for sent in doc.sents:
            if entity.start >= sent.start and entity.end <= sent.end:
                # Get entity + surrounding verb phrase
                start = entity.start
                end = entity.end
                
                # Extend to include related verb
                for token in entity.root.head.subtree:
                    start = min(start, token.i)
                    end = max(end, token.i + 1)
                
                return doc[start:end]
        
        return None
    
    def _deduplicate_phrases(self, phrases: List[Tuple[str, Span]]) -> List[Tuple[str, Span]]:
        """Remove duplicate or highly overlapping phrases"""
        if not phrases:
            return []
        
        # Sort by length (longer phrases preferred)
        phrases = sorted(phrases, key=lambda x: len(x[0]), reverse=True)
        
        unique = []
        seen_tokens = set()
        
        for text, span in phrases:
            # Get token indices
            tokens = set(range(span.start, span.end))
            
            # Check overlap with already seen phrases
            overlap = len(tokens & seen_tokens)
            if overlap / len(tokens) < 0.7:  # Less than 70% overlap
                unique.append((text, span))
                seen_tokens.update(tokens)
        
        return unique
    
    def _cluster_phrases(self, phrases: List[Tuple[str, Span]], doc: Doc) -> Dict[int, List[Tuple[str, Span]]]:
        """
        Cluster phrases using HDBSCAN on embeddings.
        
        Returns dict mapping cluster_id -> list of phrases
        """
        if len(phrases) <= 2:
            # Too few phrases to cluster meaningfully
            return {i: [phrase] for i, phrase in enumerate(phrases)}
        
        # Get embeddings for all phrases
        texts = [text for text, span in phrases]
        embeddings = self.embedder.encode(texts)
        
        # Cluster with HDBSCAN
        if not CLUSTERING_AVAILABLE:
            # Fallback: simple keyword-based clustering
            return self._fallback_clustering(phrases)
        
        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric='euclidean'
            )
            labels = clusterer.fit_predict(embeddings)
        except Exception as e:
            print(f"HDBSCAN clustering failed: {e}. Using fallback.")
            return self._fallback_clustering(phrases)
        
        # Group phrases by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            clusters[label].append(phrases[i])
        
        # Noise points (label -1) each get their own cluster
        if -1 in clusters:
            noise = clusters.pop(-1)
            max_label = max(clusters.keys()) if clusters else 0
            for i, phrase in enumerate(noise, start=max_label + 1):
                clusters[i] = [phrase]
        
        return dict(clusters)
    
    def _fallback_clustering(self, phrases: List[Tuple[str, Span]]) -> Dict[int, List[Tuple[str, Span]]]:
        """Simple keyword-based clustering when HDBSCAN unavailable"""
        clusters = defaultdict(list)
        
        for text, span in phrases:
            # Find domain with most keyword matches
            text_lower = text.lower()
            max_score = 0
            best_domain = None
            
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in text_lower)
                if score > max_score:
                    max_score = score
                    best_domain = domain
            
            # Use domain as cluster ID (hash for consistency)
            cluster_id = hash(best_domain) if best_domain else 0
            clusters[cluster_id].append((text, span))
        
        return dict(clusters)
    
    def _create_atoms_from_clusters(self, clusters: Dict[int, List[Tuple[str, Span]]], 
                                    doc: Doc, original_query: str) -> List[QueryAtom]:
        """
        Convert clusters into QueryAtom objects.
        
        Each cluster becomes one atom with combined semantic meaning.
        """
        atoms = []
        
        for cluster_id, phrases in clusters.items():
            # Combine phrases in cluster into single query
            combined_text = self._combine_phrases(phrases)
            
            # Get span boundaries
            all_spans = [span for text, span in phrases]
            start_char = min(span.start_char for span in all_spans)
            end_char = max(span.end_char for span in all_spans)
            
            # Extract entities from cluster
            entities = []
            for text, span in phrases:
                for ent in span.ents:
                    entities.append(ent.label_)
            entities = list(set(entities))
            
            # Extract key phrases
            key_phrases = [text for text, span in phrases]
            
            # Classify domains
            domains = self._classify_domains(combined_text)
            
            # Calculate complexity
            complexity = self._calculate_complexity(combined_text)
            
            # Get embedding
            embedding = self.embedder.encode(combined_text)
            
            atom = QueryAtom(
                text=combined_text,
                domains=domains,
                complexity=complexity,
                embedding=embedding,
                original_span=(start_char, end_char),
                entity_types=entities,
                key_phrases=key_phrases
            )
            
            atoms.append(atom)
        
        return atoms
    
    def _combine_phrases(self, phrases: List[Tuple[str, Span]]) -> str:
        """Intelligently combine phrases into coherent query"""
        texts = [text.strip() for text, span in phrases]
        
        # If single phrase, return as-is
        if len(texts) == 1:
            return texts[0]
        
        # If phrases are sequential, concatenate with spaces
        # Otherwise, use conjunctions
        combined = " and ".join(texts)
        
        # Ensure it's a proper question/statement
        if not combined.endswith(('.', '?', '!')):
            # Check if it's a question
            question_words = ['how', 'what', 'why', 'when', 'where', 'who', 'which']
            if any(combined.lower().startswith(qw) for qw in question_words):
                combined += '?'
        
        return combined
    
    def _build_dependencies(self, atoms: List[QueryAtom], doc: Doc) -> List[QueryAtom]:
        """
        Build dependency graph between atoms.
        
        Atom A depends on Atom B if B must be answered before A.
        """
        for i, atom_a in enumerate(atoms):
            for j, atom_b in enumerate(atoms):
                if i == j:
                    continue
                
                # Check if atom_a references concepts from atom_b
                has_dependency = self._check_dependency(atom_a, atom_b)
                
                if has_dependency and j not in atom_a.dependencies:
                    atom_a.dependencies.append(j)
        
        return atoms
    
    def _check_dependency(self, atom_a: QueryAtom, atom_b: QueryAtom) -> bool:
        """Check if atom_a depends on atom_b"""
        # 1. Embedding similarity (high similarity may indicate dependency)
        if atom_a.embedding is not None and atom_b.embedding is not None:
            similarity = np.dot(atom_a.embedding, atom_b.embedding) / (
                np.linalg.norm(atom_a.embedding) * np.linalg.norm(atom_b.embedding)
            )
            
            if similarity > 0.7:
                # High similarity - check if B is more fundamental
                if atom_b.complexity < atom_a.complexity:
                    return True
        
        # 2. Entity references (if A mentions B's entities)
        a_lower = atom_a.text.lower()
        for entity in atom_b.entity_types:
            if entity.lower() in a_lower:
                return True
        
        # 3. Key phrase overlap
        a_words = set(atom_a.text.lower().split())
        for phrase in atom_b.key_phrases:
            phrase_words = set(phrase.lower().split())
            overlap = len(a_words & phrase_words)
            if overlap >= 2:  # Significant overlap
                return True
        
        return False
    
    def _calculate_priorities(self, atoms: List[QueryAtom]) -> List[QueryAtom]:
        """
        Calculate execution priority for each atom.
        
        Priority based on:
        - Dependencies (prerequisites get higher priority)
        - Complexity (simpler queries first)
        - Domain criticality
        """
        # Build dependency graph
        in_degree = [len(atom.dependencies) for atom in atoms]
        
        for atom, degree in zip(atoms, in_degree):
            # Base priority: inverse of in-degree (fewer deps = higher priority)
            priority = 1.0 / (1 + degree)
            
            # Adjust for complexity (simpler first)
            priority *= (1.1 - atom.complexity * 0.5)
            
            # Adjust for domain criticality
            critical_domains = ['medicine', 'engineering', 'safety']
            if any(d in atom.domains for d in critical_domains):
                priority *= 1.2
            
            atom.priority = max(0.1, min(1.0, priority))
        
        return atoms
    
    def _classify_domains(self, text: str) -> List[str]:
        """
        Classify text into knowledge domains.
        
        Uses hybrid approach:
        1. Keyword matching
        2. Embedding similarity to domain descriptions
        """
        text_lower = text.lower()
        domain_scores = {}
        
        # 1. Keyword matching
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        # 2. Embedding similarity (if available)
        if EMBEDDINGS_AVAILABLE and self.embedder:
            text_embedding = self.embedder.encode(text)
            
            # Get or compute domain embeddings
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                if domain not in self._domain_embeddings:
                    domain_text = f"{domain}: {' '.join(keywords[:10])}"
                    self._domain_embeddings[domain] = self.embedder.encode(domain_text)
                
                similarity = np.dot(text_embedding, self._domain_embeddings[domain]) / (
                    np.linalg.norm(text_embedding) * np.linalg.norm(self._domain_embeddings[domain])
                )
                
                # Boost score with similarity
                if similarity > 0.3:
                    domain_scores[domain] = domain_scores.get(domain, 0) + similarity * 3
        
        # Return top domains (threshold-based)
        if not domain_scores:
            return ['general']
        
        threshold = max(domain_scores.values()) * 0.5
        relevant_domains = [d for d, s in domain_scores.items() if s >= threshold]
        
        return relevant_domains[:3]  # Max 3 domains per atom
    
    def _calculate_complexity(self, text: str) -> float:
        """
        Estimate query complexity (0.0-1.0).
        
        Factors:
        - Length (longer = more complex)
        - Technical terms (more = more complex)
        - Question depth (why/how/analyze vs what/is)
        - Syntactic complexity (clauses, dependencies)
        """
        text_lower = text.lower()
        words = text.split()
        
        # 1. Length factor (0-0.3)
        length_score = min(len(words) / 50, 1.0) * 0.3
        
        # 2. Technical density (0-0.3)
        all_technical = [kw for keywords in self.DOMAIN_KEYWORDS.values() for kw in keywords]
        tech_count = sum(1 for term in all_technical if term in text_lower)
        tech_score = min(tech_count / 10, 1.0) * 0.3
        
        # 3. Question depth (0-0.4)
        depth_score = 0.4
        if any(w in text_lower for w in self.COMPLEXITY_INDICATORS['low']):
            depth_score = 0.2
        elif any(w in text_lower for w in self.COMPLEXITY_INDICATORS['medium']):
            depth_score = 0.5
        elif any(w in text_lower for w in self.COMPLEXITY_INDICATORS['high']):
            depth_score = 0.9
        else:
            depth_score = 0.4  # Default
        
        depth_score *= 0.4
        
        total = length_score + tech_score + depth_score
        
        return min(1.0, max(0.0, total))


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def visualize_atoms(atoms: List[QueryAtom]) -> str:
    """Create ASCII visualization of atoms and dependencies"""
    lines = []
    lines.append("=" * 80)
    lines.append("QUERY DECOMPOSITION VISUALIZATION")
    lines.append("=" * 80)
    
    for i, atom in enumerate(atoms):
        lines.append(f"\nAtom {i}:")
        lines.append(f"  Text: {atom.text[:70]}{'...' if len(atom.text) > 70 else ''}")
        lines.append(f"  Domains: {', '.join(atom.domains)}")
        lines.append(f"  Complexity: {atom.complexity:.2f}")
        lines.append(f"  Priority: {atom.priority:.2f}")
        
        if atom.dependencies:
            deps = ', '.join(f"Atom {d}" for d in atom.dependencies)
            lines.append(f"  Dependencies: {deps}")
        
        if atom.entity_types:
            lines.append(f"  Entities: {', '.join(atom.entity_types)}")
    
    lines.append("\n" + "=" * 80)
    
    return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Example usage
    decomposer = QueryDecomposer()
    
    test_queries = [
        "Design a solar-powered water purifier for rural India under $100",
        "Explain quantum entanglement and how it relates to Bell's theorem",
        "What are the ethical implications of CRISPR gene editing in humans?",
        "How can we optimize battery energy density while maintaining safety?",
    ]
    
    print("Testing Query Decomposer")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\nOriginal Query: {query}")
        print("-" * 80)
        
        atoms = decomposer.decompose(query)
        print(visualize_atoms(atoms))
        print()

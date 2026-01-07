#!/usr/bin/env python3
"""
Quality Assessor - Production Implementation
Multi-dimensional response quality evaluation

Scoring Dimensions:
1. Relevance - Does it answer the query?
2. Specificity - Is it concrete vs generic?
3. Structure - Is it well-organized?
4. Completeness - Does it cover all aspects?
5. Technical Accuracy - Are claims verifiable?
6. Clarity - Is it easy to understand?

Used by collapse-to-zero algorithm to determine if more archetypes needed.
"""

import re
import math
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

# NLP dependencies
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    print("WARNING: sentence-transformers not available. Install: pip install sentence-transformers")
    EMBEDDINGS_AVAILABLE = False

try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    print("WARNING: spaCy not available. Install: pip install spacy && python -m spacy download en_core_web_sm")
    NLP_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class QualityScore:
    """
    Multi-dimensional quality assessment.
    
    Overall quality is weighted average of dimension scores.
    """
    # Dimension scores (0.0-1.0)
    relevance: float = 0.0
    specificity: float = 0.0
    structure: float = 0.0
    completeness: float = 0.0
    technical_accuracy: float = 0.0
    clarity: float = 0.0
    
    # Overall score
    overall: float = 0.0
    
    # Metadata
    query: str = ""
    response: str = ""
    archetype: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Flags
    needs_expansion: bool = False  # True if quality insufficient
    recommended_archetypes: List[str] = field(default_factory=list)
    
    # Details
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return (f"QualityScore(overall={self.overall:.2f}, "
                f"needs_expansion={self.needs_expansion})")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'relevance': self.relevance,
            'specificity': self.specificity,
            'structure': self.structure,
            'completeness': self.completeness,
            'technical_accuracy': self.technical_accuracy,
            'clarity': self.clarity,
            'overall': self.overall,
            'query': self.query,
            'archetype': self.archetype,
            'needs_expansion': self.needs_expansion,
            'recommended_archetypes': self.recommended_archetypes,
            'issues': self.issues,
            'strengths': self.strengths,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================================
# QUALITY ASSESSOR
# ============================================================================

class QualityAssessor:
    """
    Production-ready quality assessment engine.
    
    Features:
    - Multi-dimensional scoring
    - Semantic similarity matching
    - Generic content detection
    - Structure analysis
    - Technical verification
    - Adaptive thresholds
    """
    
    # Dimension weights for overall score
    DIMENSION_WEIGHTS = {
        'relevance': 0.25,      # Most important
        'specificity': 0.20,    # Avoid generic responses
        'structure': 0.15,      # Organization
        'completeness': 0.20,   # Coverage
        'technical_accuracy': 0.10,  # Factual correctness
        'clarity': 0.10         # Readability
    }
    
    # Generic phrases that reduce specificity score
    GENERIC_PHRASES = [
        'it depends', 'varies', 'many factors', 'several ways',
        'there are multiple', 'it could be', 'potentially',
        'in general', 'typically', 'usually', 'often',
        'some people', 'experts say', 'studies show',
        'research indicates', 'it is believed', 'commonly',
        'important to note', 'keep in mind', 'consider',
        'various approaches', 'different methods', 'multiple perspectives'
    ]
    
    # Stop words for clarity analysis
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
        'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Technical indicators
    TECHNICAL_INDICATORS = [
        'equation', 'theorem', 'proof', 'algorithm', 'mechanism',
        'pathway', 'structure', 'process', 'method', 'technique',
        'measurement', 'data', 'experiment', 'study', 'research',
        'finding', 'result', 'conclusion', 'analysis', 'hypothesis'
    ]
    
    def __init__(self,
                 quality_threshold: float = 0.85,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize quality assessor.
        
        Args:
            quality_threshold: Minimum overall quality for collapse-to-zero
            embedding_model: Model for semantic similarity
        """
        self.quality_threshold = quality_threshold
        self.embedding_model_name = embedding_model
        
        # Lazy loading
        self._embedder = None
        self._nlp = None
        
        # Statistics
        self.total_assessments = 0
        self.avg_quality = 0.0
        self.dimension_avgs = {k: 0.0 for k in self.DIMENSION_WEIGHTS.keys()}
        
        print(f"QualityAssessor initialized (threshold={quality_threshold:.2f})")
    
    @property
    def embedder(self):
        """Lazy load embedding model"""
        if self._embedder is None and EMBEDDINGS_AVAILABLE:
            print(f"Loading embedding model: {self.embedding_model_name}")
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder
    
    @property
    def nlp(self):
        """Lazy load spaCy model"""
        if self._nlp is None and NLP_AVAILABLE:
            print("Loading spaCy model: en_core_web_sm")
            self._nlp = spacy.load("en_core_web_sm")
        return self._nlp
    
    def assess(self,
               query: str,
               response: str,
               archetype: str,
               expected_domains: Optional[List[str]] = None) -> QualityScore:
        """
        Assess response quality across all dimensions.
        
        Args:
            query: Original query
            response: Generated response
            archetype: Archetype that generated response
            expected_domains: Expected knowledge domains
        
        Returns:
            QualityScore with multi-dimensional assessment
        """
        score = QualityScore(
            query=query,
            response=response,
            archetype=archetype
        )
        
        # 1. Relevance - semantic similarity to query
        score.relevance = self._assess_relevance(query, response)
        
        # 2. Specificity - concrete vs generic
        score.specificity = self._assess_specificity(response)
        
        # 3. Structure - organization and clarity
        score.structure = self._assess_structure(response)
        
        # 4. Completeness - covers all query aspects
        score.completeness = self._assess_completeness(query, response)
        
        # 5. Technical Accuracy - verifiable claims
        score.technical_accuracy = self._assess_technical_accuracy(response, expected_domains)
        
        # 6. Clarity - readability and comprehension
        score.clarity = self._assess_clarity(response)
        
        # Calculate overall score (weighted average)
        score.overall = sum(
            getattr(score, dim) * weight
            for dim, weight in self.DIMENSION_WEIGHTS.items()
        )
        
        # Determine if expansion needed
        score.needs_expansion = score.overall < self.quality_threshold
        
        # Identify issues and strengths
        score.issues = self._identify_issues(score)
        score.strengths = self._identify_strengths(score)
        
        # Recommend additional archetypes if needed
        if score.needs_expansion:
            score.recommended_archetypes = self._recommend_archetypes(
                query, response, score, expected_domains
            )
        
        # Update statistics
        self._update_stats(score)
        
        return score
    
    def _assess_relevance(self, query: str, response: str) -> float:
        """
        Assess semantic relevance using embeddings.
        
        Score based on cosine similarity between query and response.
        """
        if not EMBEDDINGS_AVAILABLE or not self.embedder:
            # Fallback: keyword overlap
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            overlap = len(query_words & response_words)
            return min(overlap / max(len(query_words), 1), 1.0)
        
        # Embed query and response
        query_emb = self.embedder.encode(query)
        response_emb = self.embedder.encode(response)
        
        # Cosine similarity
        similarity = np.dot(query_emb, response_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(response_emb)
        )
        
        return max(0.0, min(1.0, similarity))
    
    def _assess_specificity(self, response: str) -> float:
        """
        Assess specificity by detecting generic phrases and concrete details.
        
        High specificity = concrete examples, numbers, specific terms
        Low specificity = vague language, generic phrases
        """
        response_lower = response.lower()
        
        # Count generic phrases (penalty)
        generic_count = sum(
            1 for phrase in self.GENERIC_PHRASES 
            if phrase in response_lower
        )
        
        # Count specific indicators (bonus)
        # Numbers
        numbers = len(re.findall(r'\b\d+\.?\d*\b', response))
        
        # Proper nouns (if spaCy available)
        proper_nouns = 0
        if NLP_AVAILABLE and self.nlp:
            doc = self.nlp(response[:1000])  # First 1000 chars
            proper_nouns = len([ent for ent in doc.ents])
        
        # Technical terms
        technical_terms = sum(
            1 for term in self.TECHNICAL_INDICATORS
            if term in response_lower
        )
        
        # Calculate score
        specificity = 0.5  # Base score
        
        # Penalties
        specificity -= generic_count * 0.05
        
        # Bonuses
        specificity += min(numbers * 0.02, 0.2)
        specificity += min(proper_nouns * 0.03, 0.2)
        specificity += min(technical_terms * 0.04, 0.2)
        
        return max(0.0, min(1.0, specificity))
    
    def _assess_structure(self, response: str) -> float:
        """
        Assess structural quality.
        
        Factors:
        - Paragraph breaks
        - Sentence length variation
        - Logical flow
        - Use of transitions
        """
        # Paragraph count
        paragraphs = response.split('\n\n')
        para_count = len([p for p in paragraphs if p.strip()])
        
        # Sentence count
        sentences = re.split(r'[.!?]+', response)
        sent_count = len([s for s in sentences if s.strip()])
        
        # Average sentence length
        words = response.split()
        avg_sent_len = len(words) / max(sent_count, 1)
        
        # Ideal: 2-5 paragraphs, 15-25 words per sentence
        para_score = min(para_count / 3, 1.0) * 0.3
        sent_len_score = (
            1.0 if 15 <= avg_sent_len <= 25 
            else max(0.5, 1.0 - abs(avg_sent_len - 20) * 0.02)
        ) * 0.3
        
        # Check for list formatting (bonus)
        has_lists = bool(re.search(r'^\s*[-*•]\s', response, re.MULTILINE))
        list_score = 0.2 if has_lists else 0.0
        
        # Check for transitions
        transitions = ['however', 'therefore', 'furthermore', 'additionally',
                      'consequently', 'moreover', 'first', 'second', 'finally']
        transition_count = sum(1 for t in transitions if t in response.lower())
        transition_score = min(transition_count * 0.05, 0.2)
        
        total = para_score + sent_len_score + list_score + transition_score
        return min(1.0, total)
    
    def _assess_completeness(self, query: str, response: str) -> float:
        """
        Assess if response covers all aspects of query.
        
        Checks:
        - All query keywords addressed
        - Multiple sub-questions answered
        - Depth appropriate to query complexity
        """
        # Extract query keywords (ignore stop words)
        query_words = set(
            w.lower() for w in query.split() 
            if w.lower() not in self.STOP_WORDS
        )
        
        response_lower = response.lower()
        
        # Check coverage of query keywords
        covered = sum(1 for w in query_words if w in response_lower)
        coverage = covered / max(len(query_words), 1)
        
        # Check for multi-part answers
        # Questions often have multiple parts separated by "and" or commas
        query_parts = re.split(r',|\band\b', query)
        parts_count = len([p for p in query_parts if p.strip()])
        
        # Heuristic: response should have roughly proportional length
        response_words = len(response.split())
        query_words_count = len(query.split())
        
        # Ideal: 20-50 words per query word
        ratio = response_words / max(query_words_count, 1)
        depth_score = (
            1.0 if 20 <= ratio <= 50
            else max(0.5, 1.0 - abs(ratio - 35) * 0.01)
        )
        
        # Combine scores
        total = coverage * 0.6 + depth_score * 0.4
        return min(1.0, total)
    
    def _assess_technical_accuracy(self, 
                                   response: str, 
                                   expected_domains: Optional[List[str]] = None) -> float:
        """
        Assess technical accuracy.
        
        Checks:
        - Presence of technical terms
        - Citations or references
        - Avoidance of hedging language
        - Domain-appropriate vocabulary
        """
        response_lower = response.lower()
        
        # Check for technical indicators
        tech_count = sum(
            1 for term in self.TECHNICAL_INDICATORS
            if term in response_lower
        )
        tech_score = min(tech_count * 0.1, 0.4)
        
        # Check for citations/references
        has_citations = bool(re.search(r'\([A-Za-z]+\s+\d{4}\)', response))
        citation_score = 0.2 if has_citations else 0.0
        
        # Check for hedging (penalty)
        hedging = ['might', 'could', 'possibly', 'perhaps', 'maybe', 'seems']
        hedge_count = sum(1 for h in hedging if h in response_lower)
        hedge_penalty = min(hedge_count * 0.05, 0.2)
        
        # Domain vocabulary check (if domains provided)
        domain_score = 0.0
        if expected_domains:
            # This would ideally check domain-specific terminology
            # For now, just a placeholder
            domain_score = 0.2
        
        total = tech_score + citation_score + domain_score - hedge_penalty
        return max(0.0, min(1.0, total + 0.2))  # Base score 0.2
    
    def _assess_clarity(self, response: str) -> float:
        """
        Assess clarity and readability.
        
        Uses Flesch Reading Ease approximation.
        """
        # Count sentences
        sentences = re.split(r'[.!?]+', response)
        sent_count = len([s for s in sentences if s.strip()])
        
        # Count words
        words = response.split()
        word_count = len(words)
        
        # Count syllables (approximation)
        syllable_count = sum(self._count_syllables(w) for w in words)
        
        if sent_count == 0 or word_count == 0:
            return 0.5
        
        # Flesch Reading Ease
        # Score = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        avg_sent_len = word_count / sent_count
        avg_syllables = syllable_count / word_count
        
        flesch = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syllables
        
        # Normalize to 0-1 (Flesch ranges roughly 0-100)
        # Ideal: 60-70 (standard difficulty)
        normalized = flesch / 100
        
        return max(0.0, min(1.0, normalized))
    
    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count"""
        word = word.lower()
        vowels = 'aeiouy'
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e'):
            count -= 1
        
        return max(count, 1)
    
    def _identify_issues(self, score: QualityScore) -> List[str]:
        """Identify specific quality issues"""
        issues = []
        
        if score.relevance < 0.7:
            issues.append("Low relevance - response may not address query")
        
        if score.specificity < 0.6:
            issues.append("Too generic - needs concrete details")
        
        if score.structure < 0.6:
            issues.append("Poor structure - needs better organization")
        
        if score.completeness < 0.7:
            issues.append("Incomplete - missing query aspects")
        
        if score.technical_accuracy < 0.6:
            issues.append("Low technical depth - needs more rigor")
        
        if score.clarity < 0.6:
            issues.append("Clarity issues - complex or unclear writing")
        
        return issues
    
    def _identify_strengths(self, score: QualityScore) -> List[str]:
        """Identify quality strengths"""
        strengths = []
        
        if score.relevance >= 0.9:
            strengths.append("Highly relevant to query")
        
        if score.specificity >= 0.8:
            strengths.append("Concrete and specific")
        
        if score.structure >= 0.8:
            strengths.append("Well-organized")
        
        if score.completeness >= 0.9:
            strengths.append("Comprehensive coverage")
        
        if score.technical_accuracy >= 0.8:
            strengths.append("Technically rigorous")
        
        if score.clarity >= 0.8:
            strengths.append("Clear and readable")
        
        return strengths
    
    def _recommend_archetypes(self,
                             query: str,
                             response: str,
                             score: QualityScore,
                             expected_domains: Optional[List[str]]) -> List[str]:
        """
        Recommend additional archetypes to improve quality.
        
        Based on identified weaknesses and domain gaps.
        """
        recommendations = []
        
        # Map weaknesses to archetypes
        if score.technical_accuracy < 0.7:
            # Need more technical depth
            if expected_domains:
                if 'physics' in expected_domains:
                    recommendations.append('caltech_physics')
                elif 'engineering' in expected_domains:
                    recommendations.append('mit_engineering')
                elif 'medicine' in expected_domains:
                    recommendations.append('harvard_med')
        
        if score.specificity < 0.6:
            # Need concrete examples
            recommendations.append('mit_media')  # Design thinking
        
        if score.completeness < 0.7:
            # Need broader perspective
            recommendations.append('mensa_polymath')
        
        # Remove duplicates and limit to 2
        return list(set(recommendations))[:2]
    
    def _update_stats(self, score: QualityScore):
        """Update running statistics"""
        self.total_assessments += 1
        
        # Update average quality
        self.avg_quality = (
            (self.avg_quality * (self.total_assessments - 1) + score.overall) /
            self.total_assessments
        )
        
        # Update dimension averages
        for dim in self.DIMENSION_WEIGHTS.keys():
            old_avg = self.dimension_avgs[dim]
            new_val = getattr(score, dim)
            self.dimension_avgs[dim] = (
                (old_avg * (self.total_assessments - 1) + new_val) /
                self.total_assessments
            )
    
    def get_stats(self) -> Dict:
        """Get assessment statistics"""
        return {
            'total_assessments': self.total_assessments,
            'avg_overall_quality': self.avg_quality,
            'dimension_averages': self.dimension_avgs,
            'quality_threshold': self.quality_threshold
        }
    
    def visualize_score(self, score: QualityScore) -> str:
        """Create ASCII visualization of quality score"""
        lines = []
        lines.append("=" * 80)
        lines.append("QUALITY ASSESSMENT")
        lines.append("=" * 80)
        lines.append(f"\nQuery: {score.query[:60]}...")
        lines.append(f"Archetype: {score.archetype}")
        lines.append(f"\nOVERALL QUALITY: {score.overall:.2f} / 1.00")
        lines.append("  " + "█" * int(score.overall * 50) + "░" * (50 - int(score.overall * 50)))
        
        lines.append(f"\nDimension Scores:")
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            val = getattr(score, dim)
            bar = "█" * int(val * 30) + "░" * (30 - int(val * 30))
            lines.append(f"  {dim:20s}: {val:.2f}  {bar}")
        
        if score.needs_expansion:
            lines.append(f"\n⚠ QUALITY INSUFFICIENT - EXPANSION RECOMMENDED")
            if score.recommended_archetypes:
                lines.append(f"  Suggested: {', '.join(score.recommended_archetypes)}")
        else:
            lines.append(f"\n✓ QUALITY SUFFICIENT")
        
        if score.issues:
            lines.append(f"\nIssues:")
            for issue in score.issues:
                lines.append(f"  • {issue}")
        
        if score.strengths:
            lines.append(f"\nStrengths:")
            for strength in score.strengths:
                lines.append(f"  • {strength}")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    assessor = QualityAssessor(quality_threshold=0.85)
    
    # Test cases
    test_cases = [
        (
            "Explain quantum entanglement",
            "Quantum entanglement is when two particles are connected. "
            "It's a quantum mechanical phenomenon where particles share a state. "
            "This means measuring one affects the other.",
            "caltech_physics"
        ),
        (
            "Design a water purification system for rural areas",
            "A cost-effective water purification system for rural areas could use "
            "solar-powered UV-C sterilization (253.7 nm wavelength) combined with "
            "ceramic filtration (0.2 micron pores) and activated carbon absorption. "
            "Target cost: $50-100 per unit, treating 20L/hour. Key components: "
            "1) Pre-filter for sediment removal, 2) UV-C chamber (15W LED), "
            "3) Ceramic filter for bacteria/protozoa, 4) Carbon stage for chemicals. "
            "Solar panel: 50W monocrystalline with 12V battery backup.",
            "mit_engineering"
        )
    ]
    
    print("Testing Quality Assessor")
    print("=" * 80)
    
    for query, response, archetype in test_cases:
        score = assessor.assess(query, response, archetype)
        print(assessor.visualize_score(score))
        print()

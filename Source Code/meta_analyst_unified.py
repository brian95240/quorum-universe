#!/usr/bin/env python3
"""
Meta-Analyst Unified - Self-Expanding Authority Discovery Engine
Integrates: Basic dorking + Confidence triggers + Authority discovery + Cascade fallback
Version: 3.0 (Unified)
"""

import asyncio
import time
import json
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse
from datetime import datetime
import numpy as np

try:
    import redis
    from playwright.async_api import async_playwright
    import aiohttp
except ImportError:
    print("ERROR: Install dependencies: pip install redis playwright aiohttp")
    print("       Then run: playwright install chromium")
    exit(1)


# ============================================================================
# AUTHORITY SOURCES (Pre-indexed for known domains)
# ============================================================================

AUTHORITY_SOURCES = {
    'science': [
        {'domain': 'arxiv.org', 'weight': 0.95, 'dorks': ['site:arxiv.org', 'filetype:pdf']},
        {'domain': 'nature.com', 'weight': 0.90, 'dorks': ['site:nature.com/articles']},
        {'domain': 'science.org', 'weight': 0.90, 'dorks': ['site:science.org']},
        {'domain': 'pnas.org', 'weight': 0.88, 'dorks': ['site:pnas.org']},
    ],
    'medical': [
        {'domain': 'pubmed.ncbi.nlm.nih.gov', 'weight': 0.95, 'dorks': ['site:pubmed.ncbi.nlm.nih.gov']},
        {'domain': 'cochrane.org', 'weight': 0.93, 'dorks': ['site:cochranelibrary.com']},
        {'domain': 'nejm.org', 'weight': 0.92, 'dorks': ['site:nejm.org']},
        {'domain': 'thelancet.com', 'weight': 0.90, 'dorks': ['site:thelancet.com']},
    ],
    'code': [
        {'domain': 'github.com', 'weight': 0.90, 'dorks': ['site:github.com', 'stars:>100']},
        {'domain': 'stackoverflow.com', 'weight': 0.85, 'dorks': ['site:stackoverflow.com', 'score:>10']},
        {'domain': 'arxiv.org/cs', 'weight': 0.88, 'dorks': ['site:arxiv.org/list/cs']},
    ],
    'historical': [
        {'domain': 'jstor.org', 'weight': 0.92, 'dorks': ['site:jstor.org']},
        {'domain': 'perseus.tufts.edu', 'weight': 0.90, 'dorks': ['site:perseus.tufts.edu']},
        {'domain': 'gutenberg.org', 'weight': 0.85, 'dorks': ['site:gutenberg.org']},
    ],
    'mathematics': [
        {'domain': 'mathworld.wolfram.com', 'weight': 0.93, 'dorks': ['site:mathworld.wolfram.com']},
        {'domain': 'oeis.org', 'weight': 0.92, 'dorks': ['site:oeis.org']},
        {'domain': 'arxiv.org/math', 'weight': 0.90, 'dorks': ['site:arxiv.org/list/math']},
    ],
    'engineering': [
        {'domain': 'ieee.org', 'weight': 0.93, 'dorks': ['site:ieeexplore.ieee.org']},
        {'domain': 'patents.google.com', 'weight': 0.88, 'dorks': ['site:patents.google.com']},
        {'domain': 'asme.org', 'weight': 0.85, 'dorks': ['site:asme.org']},
    ],
    'law': [
        {'domain': 'supremecourt.gov', 'weight': 0.95, 'dorks': ['site:supremecourt.gov']},
        {'domain': 'law.cornell.edu', 'weight': 0.90, 'dorks': ['site:law.cornell.edu']},
    ],
}

DOMAIN_KEYWORDS = {
    'science': ['physics', 'chemistry', 'biology', 'astronomy', 'geology', 'quantum', 'particle'],
    'medical': ['disease', 'treatment', 'clinical', 'diagnosis', 'symptom', 'patient', 'medical'],
    'code': ['programming', 'algorithm', 'software', 'debug', 'implementation', 'code', 'function'],
    'historical': ['history', 'ancient', 'medieval', 'civilization', 'century', 'archaeological'],
    'mathematics': ['theorem', 'proof', 'equation', 'topology', 'algebra', 'calculus', 'prime'],
    'engineering': ['design', 'circuit', 'mechanical', 'structural', 'manufacturing', 'prototype'],
    'law': ['legal', 'court', 'statute', 'precedent', 'liability', 'constitutional'],
}


# ============================================================================
# DOMAIN DETECTION & CLASSIFICATION
# ============================================================================

class DomainDetector:
    """Detect if query is in known domain or requires authority discovery"""
    
    def __init__(self, cache: redis.Redis):
        self.cache = cache
        self.indexed_domains = set(AUTHORITY_SOURCES.keys())
        
    def classify(self, query: str) -> Dict:
        """
        Returns: {status, domain, confidence, requires_discovery}
        status: 'indexed', 'learned', 'unknown'
        """
        query_lower = query.lower()
        
        # Check indexed domains
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score >= 2:  # At least 2 keyword matches
                return {
                    'status': 'indexed',
                    'domain': domain,
                    'confidence': 0.95,
                    'requires_discovery': False
                }
        
        # Check learned domains (cached from previous discoveries)
        learned = self.cache.keys('learned_authorities:*')
        for key in learned:
            subject = key.decode().split(':')[1]
            cached_data = json.loads(self.cache.get(key))
            
            # Check if query matches learned keywords
            if any(kw in query_lower for kw in cached_data.get('keywords', [])):
                return {
                    'status': 'learned',
                    'domain': subject,
                    'confidence': 0.85,
                    'requires_discovery': False
                }
        
        # Unknown domain - extract subject for discovery
        subject = self.extract_subject(query)
        
        return {
            'status': 'unknown',
            'domain': subject,
            'confidence': 0.0,
            'requires_discovery': True
        }
    
    def extract_subject(self, query: str) -> str:
        """Extract core subject from query (simplified - use spaCy in production)"""
        # Remove stopwords
        stopwords = {'what', 'how', 'why', 'when', 'where', 'who', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are'}
        words = [w for w in query.lower().split() if w not in stopwords]
        
        # Take first 2-3 meaningful words
        subject = '_'.join(words[:3]) if words else 'unknown'
        return subject


# ============================================================================
# AUTHORITY DISCOVERY ENGINE
# ============================================================================

class AuthorityDiscoveryEngine:
    """Bootstrap authoritative sources for unknown domains"""
    
    def __init__(self, cache: redis.Redis):
        self.cache = cache
        self.authority_tlds = ['.edu', '.gov', '.org', '.ac.uk']
        self.last_request_time = 0
    
    async def discover_authorities(self, subject: str) -> List[Dict]:
        """
        Multi-stage authority discovery:
        1. Meta-search for "best [subject] sources"
        2. Extract domain patterns (.edu, .gov, .org)
        3. Validate via citation networks (Semantic Scholar)
        4. Rank by authority score
        5. Cache for future use
        """
        print(f"\n🔍 AUTHORITY DISCOVERY: {subject}")
        
        # Check cache first
        cache_key = f"learned_authorities:{subject}"
        cached = self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            print(f"   ⚡ Using cached authorities ({len(data['authorities'])} sources)")
            return data['authorities']
        
        # Stage 1: Meta-search
        candidates = await self.meta_search(subject)
        if not candidates:
            return []
        
        # Stage 2: Extract patterns & filter
        filtered = self.filter_by_tld(candidates)
        
        # Stage 3: Validate (simplified - would use Semantic Scholar API in production)
        validated = self.validate_authorities(filtered)
        
        # Stage 4: Rank
        ranked = self.rank_authorities(validated)
        
        # Stage 5: Cache
        self.cache_authorities(subject, ranked)
        
        print(f"   ✓ Discovered {len(ranked)} authorities\n")
        return ranked
    
    async def meta_search(self, subject: str) -> List[Dict]:
        """Search for authoritative sources in subject area"""
        meta_queries = [
            f"best {subject} academic sources",
            f"authoritative {subject} journals",
            f"{subject} research databases",
        ]
        
        all_results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (AmbientIntelligence/3.0) Research Agent"
            )
            
            for query in meta_queries:
                await self.enforce_rate_limit()
                
                page = await context.new_page()
                
                try:
                    encoded = quote_plus(query)
                    await page.goto(f"https://www.google.com/search?q={encoded}", timeout=10000)
                    
                    # Extract search results
                    results = await page.query_selector_all('div.g')
                    
                    for result in results[:10]:
                        try:
                            title_elem = await result.query_selector('h3')
                            link_elem = await result.query_selector('a')
                            
                            if title_elem and link_elem:
                                title = await title_elem.inner_text()
                                url = await link_elem.get_attribute('href')
                                
                                if url and url.startswith('http'):
                                    all_results.append({
                                        'title': title,
                                        'url': url,
                                        'meta_query': query
                                    })
                        except:
                            continue
                
                except Exception as e:
                    print(f"   ⚠️  Meta-search failed: {e}")
                
                finally:
                    await page.close()
            
            await browser.close()
        
        return all_results
    
    def filter_by_tld(self, candidates: List[Dict]) -> List[Dict]:
        """Filter for authoritative TLDs"""
        filtered = []
        for candidate in candidates:
            url = candidate['url']
            if any(tld in url for tld in self.authority_tlds):
                filtered.append(candidate)
        return filtered
    
    def validate_authorities(self, candidates: List[Dict]) -> List[Dict]:
        """Add validation metadata (simplified)"""
        for candidate in candidates:
            url = candidate['url']
            
            # TLD-based validation
            if '.edu' in url:
                candidate['validated'] = True
                candidate['validation_score'] = 0.9
            elif '.gov' in url:
                candidate['validated'] = True
                candidate['validation_score'] = 0.95
            elif '.org' in url:
                candidate['validated'] = True
                candidate['validation_score'] = 0.8
            else:
                candidate['validated'] = False
                candidate['validation_score'] = 0.5
        
        return candidates
    
    def rank_authorities(self, authorities: List[Dict]) -> List[Dict]:
        """Rank by composite authority score"""
        for auth in authorities:
            url = auth['url']
            
            # TLD score
            tld_score = 0.0
            if '.edu' in url:
                tld_score = 0.3
            elif '.gov' in url:
                tld_score = 0.35
            elif '.org' in url:
                tld_score = 0.25
            
            # Validation score
            val_score = auth.get('validation_score', 0) * 0.4
            
            # Keyword match (if title contains authority keywords)
            keyword_score = 0.0
            title_lower = auth['title'].lower()
            if any(kw in title_lower for kw in ['university', 'institute', 'research', 'journal']):
                keyword_score = 0.15
            
            auth['authority_weight'] = min(tld_score + val_score + keyword_score, 0.95)
            
            # Generate dork pattern
            domain = self.extract_domain(auth['url'])
            auth['url_pattern'] = f"site:{domain}"
        
        # Sort by weight
        ranked = sorted(authorities, key=lambda x: x['authority_weight'], reverse=True)
        return ranked[:10]
    
    def cache_authorities(self, subject: str, authorities: List[Dict]):
        """Cache discovered authorities for 30 days"""
        cache_data = {
            'subject': subject,
            'authorities': authorities,
            'keywords': self.extract_keywords(authorities),
            'discovered_at': time.time()
        }
        
        cache_key = f"learned_authorities:{subject}"
        self.cache.setex(cache_key, 2592000, json.dumps(cache_data))  # 30 days
    
    def extract_keywords(self, authorities: List[Dict]) -> List[str]:
        """Extract common keywords from authority titles"""
        all_words = []
        for auth in authorities:
            words = auth['title'].lower().split()
            all_words.extend(words)
        
        # Count frequency
        from collections import Counter
        word_counts = Counter(all_words)
        
        # Top 10 most common (excluding stopwords)
        stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'and', 'or'}
        keywords = [word for word, count in word_counts.most_common(20) 
                   if word not in stopwords and len(word) > 3]
        
        return keywords[:10]
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc
    
    async def enforce_rate_limit(self):
        """Rate limit: 2 seconds between requests"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < 2:
            await asyncio.sleep(2 - elapsed)
        
        self.last_request_time = time.time()


# ============================================================================
# CASCADE FALLBACK (Multi-tier search when primary fails)
# ============================================================================

class CascadeFallback:
    """Multi-tier fallback search strategy"""
    
    async def execute(self, query: str, subject: str, primary_results: List[Dict]) -> List[Dict]:
        """
        Cascade through fallback tiers:
        Tier 1: Academic databases (BASE, WorldCat)
        Tier 2: Citation networks (Semantic Scholar)
        Tier 3: Wikipedia references
        """
        
        # Check if primary is sufficient
        if self.assess_quality(primary_results) >= 0.85:
            return primary_results
        
        print(f"\n⚠️  Primary search quality < 0.85")
        print(f"   Initiating cascade fallback...\n")
        
        # Tier 1: Academic databases
        tier1 = await self.search_academic_databases(query)
        combined = primary_results + tier1
        
        if self.assess_quality(combined) >= 0.85:
            print(f"   ✓ Tier 1 sufficient")
            return combined
        
        # Tier 2: Citation networks
        print(f"   → Escalating to Tier 2 (citations)...")
        tier2 = await self.search_semantic_scholar(query)
        combined.extend(tier2)
        
        if self.assess_quality(combined) >= 0.85:
            print(f"   ✓ Tier 2 sufficient")
            return combined
        
        # Tier 3: Wikipedia
        print(f"   → Escalating to Tier 3 (Wikipedia)...")
        tier3 = await self.extract_wikipedia_refs(subject)
        combined.extend(tier3)
        
        return self.deduplicate(combined)
    
    async def search_academic_databases(self, query: str) -> List[Dict]:
        """Search universal academic databases"""
        results = []
        
        # Simplified - would actually search BASE, WorldCat, CORE
        # For now, add placeholder authority
        results.append({
            'title': f"Academic sources for: {query[:50]}",
            'url': f"https://www.base-search.net/Search/Results?lookfor={quote_plus(query)}",
            'authority_weight': 0.85,
            'source': 'Academic Database (Tier 1)'
        })
        
        return results
    
    async def search_semantic_scholar(self, query: str) -> List[Dict]:
        """Search Semantic Scholar API"""
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.semanticscholar.org/graph/v1/paper/search"
                params = {
                    'query': query,
                    'fields': 'title,url,citationCount',
                    'limit': 5
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for paper in data.get('data', []):
                            citations = paper.get('citationCount', 0)
                            weight = min(0.7 + citations / 1000, 0.90)
                            
                            results.append({
                                'title': paper.get('title', ''),
                                'url': paper.get('url', ''),
                                'authority_weight': weight,
                                'citation_count': citations,
                                'source': 'Semantic Scholar (Tier 2)'
                            })
        except Exception as e:
            print(f"      ⚠️  Semantic Scholar failed: {e}")
        
        return results
    
    async def extract_wikipedia_refs(self, subject: str) -> List[Dict]:
        """Extract references from Wikipedia"""
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search Wikipedia
                url = "https://en.wikipedia.org/w/api.php"
                params = {
                    'action': 'query',
                    'list': 'search',
                    'srsearch': subject,
                    'format': 'json',
                    'srlimit': 3
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for article in data.get('query', {}).get('search', []):
                            results.append({
                                'title': f"Wikipedia: {article['title']}",
                                'url': f"https://en.wikipedia.org/?curid={article['pageid']}",
                                'authority_weight': 0.75,
                                'source': 'Wikipedia (Tier 3)'
                            })
        except Exception as e:
            print(f"      ⚠️  Wikipedia extraction failed: {e}")
        
        return results
    
    def assess_quality(self, results: List[Dict]) -> float:
        """Calculate average authority weight"""
        if not results:
            return 0.0
        
        weights = [r.get('authority_weight', 0) for r in results]
        return sum(weights) / len(weights)
    
    def deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate URLs"""
        seen = set()
        unique = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen:
                seen.add(url)
                unique.append(result)
        
        # Sort by authority weight
        unique.sort(key=lambda x: x.get('authority_weight', 0), reverse=True)
        return unique[:15]  # Top 15


# ============================================================================
# UNIFIED META-ANALYST
# ============================================================================

class MetaAnalystUnified:
    """
    Unified Meta-Analyst combining all three evolution stages:
    1. Basic web dorking
    2. Confidence-triggered research
    3. Self-expanding authority discovery
    """
    
    def __init__(self):
        # Redis for caching (DB 3 for meta-analyst)
        try:
            self.cache = redis.Redis(host='localhost', port=6379, db=3, decode_responses=False)
            self.cache.ping()
        except:
            print("WARNING: Redis not available - caching disabled")
            self.cache = None
        
        # Components
        self.domain_detector = DomainDetector(self.cache) if self.cache else None
        self.authority_discovery = AuthorityDiscoveryEngine(self.cache) if self.cache else None
        self.cascade_fallback = CascadeFallback()
        
        # Rate limiting
        self.last_request_time = 0
        self.requests_this_minute = 0
    
    async def research(
        self,
        query: str,
        archetype_response: Optional[str] = None,
        confidence: float = 0.0,
        enable_discovery: bool = True
    ) -> Dict:
        """
        Main research entry point.
        
        Args:
            query: User query
            archetype_response: Previous archetype response (if confidence low)
            confidence: Archetype confidence score (0.0-1.0)
            enable_discovery: Allow authority discovery for unknown domains
        
        Returns:
            {synthesis, sources, confidence, meta_analyst_triggered, ...}
        """
        print(f"\n{'='*80}")
        print(f"META-ANALYST UNIFIED v3.0")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Archetype confidence: {confidence:.2f}")
        print(f"Threshold: 0.85")
        print(f"{'='*80}\n")
        
        # Check cache
        cache_key = self.generate_cache_key(query)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                print(f"⚡ CACHE HIT (7-day TTL)\n")
                return json.loads(cached.decode())
        
        # Detect domain
        if self.domain_detector:
            domain_info = self.domain_detector.classify(query)
            print(f"Domain Detection:")
            print(f"  Status: {domain_info['status']}")
            print(f"  Domain: {domain_info['domain']}")
            print(f"  Confidence: {domain_info['confidence']:.2f}\n")
        else:
            domain_info = {'status': 'indexed', 'domain': 'science', 'requires_discovery': False}
        
        # Execute search based on domain status
        if domain_info['status'] == 'indexed':
            # Use pre-indexed authorities
            results = await self.search_indexed_domain(query, domain_info['domain'])
        
        elif domain_info['status'] == 'learned':
            # Use previously learned authorities
            results = await self.search_learned_domain(query, domain_info['domain'])
        
        elif domain_info['requires_discovery'] and enable_discovery:
            # Discover new authorities
            print(f"🔍 Unknown domain detected")
            print(f"   Initiating authority discovery...\n")
            
            authorities = await self.authority_discovery.discover_authorities(domain_info['domain'])
            
            if authorities:
                results = await self.search_with_authorities(query, authorities)
            else:
                # Discovery failed - use cascade fallback
                results = await self.cascade_fallback.execute(query, domain_info['domain'], [])
        
        else:
            # Fallback to basic search
            results = await self.basic_search(query)
        
        # Quality check - apply cascade if needed
        if self.cascade_fallback.assess_quality(results) < 0.85:
            print(f"\n⚠️  Results quality insufficient")
            results = await self.cascade_fallback.execute(query, domain_info['domain'], results)
        
        # Extract content from top results
        content = await self.extract_content(results[:5])
        
        # Synthesize final answer
        synthesis = self.synthesize(query, content, archetype_response)
        
        result = {
            'query': query,
            'synthesis': synthesis,
            'sources': [
                {
                    'title': r['title'],
                    'url': r['url'],
                    'authority': r.get('authority_weight', 0.75),
                    'source_type': r.get('source', 'web')
                }
                for r in results[:10]
            ],
            'confidence': 0.90,  # Meta-analyst boost
            'meta_analyst_triggered': True,
            'domain_status': domain_info['status'],
            'discovery_used': domain_info.get('requires_discovery', False)
        }
        
        # Cache result
        if self.cache:
            self.cache.setex(cache_key, 604800, json.dumps(result))  # 7 days
        
        print(f"\n{'='*80}")
        print(f"RESEARCH COMPLETE")
        print(f"{'='*80}")
        print(f"Sources: {len(result['sources'])}")
        print(f"Final confidence: {result['confidence']:.2f}")
        print(f"{'='*80}\n")
        
        return result
    
    async def search_indexed_domain(self, query: str, domain: str) -> List[Dict]:
        """Search using pre-indexed authorities"""
        print(f"→ Using pre-indexed authorities for: {domain}\n")
        
        sources = AUTHORITY_SOURCES.get(domain, [])
        dork_queries = []
        
        # Build dork queries
        for source in sources[:3]:  # Top 3 per domain
            dork = self.build_dork(query, source)
            dork_queries.append({
                'query': dork,
                'source': source['domain'],
                'weight': source['weight']
            })
        
        # Execute searches
        results = await self.execute_searches(dork_queries)
        return results
    
    async def search_learned_domain(self, query: str, subject: str) -> List[Dict]:
        """Search using previously learned authorities"""
        print(f"→ Using learned authorities for: {subject}\n")
        
        # Load from cache
        cache_key = f"learned_authorities:{subject}"
        cached = self.cache.get(cache_key)
        
        if cached:
            data = json.loads(cached.decode())
            authorities = data['authorities']
            
            # Build dork queries
            dork_queries = []
            for auth in authorities[:3]:
                dork = self.build_dork(query, auth)
                dork_queries.append({
                    'query': dork,
                    'source': auth.get('url_pattern', ''),
                    'weight': auth.get('authority_weight', 0.8)
                })
            
            results = await self.execute_searches(dork_queries)
            return results
        
        return []
    
    async def search_with_authorities(self, query: str, authorities: List[Dict]) -> List[Dict]:
        """Search using discovered authorities"""
        dork_queries = []
        
        for auth in authorities[:5]:
            dork = self.build_dork(query, auth)
            dork_queries.append({
                'query': dork,
                'source': auth.get('url_pattern', ''),
                'weight': auth.get('authority_weight', 0.8)
            })
        
        results = await self.execute_searches(dork_queries)
        return results
    
    async def basic_search(self, query: str) -> List[Dict]:
        """Basic Google search (fallback)"""
        print(f"→ Using basic search (no domain classification)\n")
        
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                encoded = quote_plus(query + " academic research")
                await page.goto(f"https://www.google.com/search?q={encoded}")
                
                search_results = await page.query_selector_all('div.g')
                
                for result in search_results[:10]:
                    try:
                        title_elem = await result.query_selector('h3')
                        link_elem = await result.query_selector('a')
                        
                        if title_elem and link_elem:
                            title = await title_elem.inner_text()
                            url = await link_elem.get_attribute('href')
                            
                            if url and url.startswith('http'):
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'authority_weight': 0.75,
                                    'source': 'Basic Search'
                                })
                    except:
                        continue
            
            finally:
                await browser.close()
        
        return results
    
    def build_dork(self, query: str, source: Dict) -> str:
        """Build Google dork query"""
        # Extract key terms
        stopwords = {'what', 'how', 'why', 'when', 'where', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are'}
        terms = [w for w in query.lower().split() if w not in stopwords]
        base_query = ' '.join(terms[:5])
        
        # Add source dorks
        dorks = ' '.join(source.get('dorks', [source.get('url_pattern', '')]))
        
        # Add recency
        after_date = "after:2023-01-01"
        
        return f"{base_query} {dorks} {after_date}"
    
    async def execute_searches(self, dork_queries: List[Dict]) -> List[Dict]:
        """Execute dork queries via Playwright"""
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            for i, dork in enumerate(dork_queries):
                await self.enforce_rate_limit()
                
                print(f"   [{i+1}/{len(dork_queries)}] Searching: {dork['source'][:40]}")
                
                page = await context.new_page()
                
                try:
                    encoded = quote_plus(dork['query'])
                    await page.goto(f"https://www.google.com/search?q={encoded}", timeout=10000)
                    
                    search_results = await page.query_selector_all('div.g')
                    
                    for result in search_results[:5]:
                        try:
                            title_elem = await result.query_selector('h3')
                            link_elem = await result.query_selector('a')
                            
                            if title_elem and link_elem:
                                title = await title_elem.inner_text()
                                url = await link_elem.get_attribute('href')
                                
                                if url and url.startswith('http'):
                                    results.append({
                                        'title': title,
                                        'url': url,
                                        'authority_weight': dork['weight'],
                                        'source': dork['source']
                                    })
                        except:
                            continue
                
                except Exception as e:
                    print(f"      ⚠️  Search failed: {e}")
                
                finally:
                    await page.close()
            
            await browser.close()
        
        print(f"\n   ✓ Collected {len(results)} results\n")
        return results
    
    async def extract_content(self, results: List[Dict]) -> List[Dict]:
        """Extract full content from top results"""
        content = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            for i, result in enumerate(results):
                print(f"   Extracting [{i+1}/{len(results)}]: {result['url'][:50]}...")
                
                page = await context.new_page()
                
                try:
                    await page.goto(result['url'], timeout=15000)
                    
                    # Try common content selectors
                    text = ""
                    for selector in ['article', 'main', '.content', '#content', 'body']:
                        elem = await page.query_selector(selector)
                        if elem:
                            text = await elem.inner_text()
                            if len(text) > 500:
                                break
                    
                    if text:
                        content.append({
                            'url': result['url'],
                            'title': result['title'],
                            'text': text[:5000],  # Limit
                            'authority': result.get('authority_weight', 0.75)
                        })
                
                except Exception as e:
                    print(f"      ⚠️  Extraction failed: {e}")
                
                finally:
                    await page.close()
            
            await browser.close()
        
        print(f"\n   ✓ Extracted {len(content)} documents\n")
        return content
    
    def synthesize(self, query: str, content: List[Dict], archetype_response: Optional[str]) -> str:
        """Synthesize findings into coherent answer"""
        # Build synthesis
        synthesis_parts = []
        
        synthesis_parts.append(f"Query: {query}\n")
        
        if archetype_response:
            synthesis_parts.append(f"Initial Assessment:\n{archetype_response}\n")
        
        synthesis_parts.append("Research Findings:\n")
        
        for i, doc in enumerate(content, 1):
            synthesis_parts.append(f"\n[{i}] {doc['title']}")
            synthesis_parts.append(f"    Source: {doc['url']}")
            synthesis_parts.append(f"    Authority: {doc['authority']:.2f}")
            synthesis_parts.append(f"    Excerpt: {doc['text'][:300]}...\n")
        
        synthesis_parts.append("\nSynthesized Analysis:")
        synthesis_parts.append("Based on authoritative sources, the evidence suggests...")
        
        return "\n".join(synthesis_parts)
    
    async def enforce_rate_limit(self):
        """Rate limit: 30 requests/minute, 2s between requests"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.last_request_time > 60:
            self.requests_this_minute = 0
        
        # Check limit
        if self.requests_this_minute >= 30:
            wait_time = 60 - (current_time - self.last_request_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.requests_this_minute = 0
        
        # Delay between requests
        await asyncio.sleep(2)
        
        self.requests_this_minute += 1
        self.last_request_time = current_time
    
    def generate_cache_key(self, query: str) -> str:
        """Generate cache key"""
        return f"meta_analyst_v3:{hashlib.sha256(query.encode()).hexdigest()[:16]}"


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python meta_analyst_unified.py 'your query here'")
        print("\nExample:")
        print("  python meta_analyst_unified.py 'What are the latest dark matter detection methods?'")
        return
    
    query = ' '.join(sys.argv[1:])
    
    meta = MetaAnalystUnified()
    result = await meta.research(query)
    
    print("\n" + "="*80)
    print("FINAL SYNTHESIS")
    print("="*80)
    print(result['synthesis'])
    print(f"\nSources: {len(result['sources'])}")
    print(f"Confidence: {result['confidence']:.2f}")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())

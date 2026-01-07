#!/usr/bin/env python3
"""
Quorum - Philosopher Tribunal for Truth Forensics
Chains Hume, Popper, Quine, Arendt, Zhuangzi, Khaldun + Observer (silence)
With temporal context hashing and AGE graph pattern matching
"""

import hashlib
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Ollama integration (install: pip install ollama)
try:
    from ollama import chat
except ImportError:
    print("ERROR: Install ollama-python: pip install ollama")
    sys.exit(1)

# PostgreSQL + AGE integration (install: pip install psycopg2-binary)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("WARNING: psycopg2 not found. Install for AGE integration: pip install psycopg2-binary")
    psycopg2 = None


# ============================================================================
# PHILOSOPHER CONFIGURATION
# ============================================================================

PHILOSOPHERS = {
    'hume': {
        'lora': 'hume-70b',  # Model name in Ollama
        'style': 'Empirical skeptic - demands evidence, questions causation',
        'temperature': 0.7
    },
    'popper': {
        'lora': 'popper-70b',
        'style': 'Falsificationist - seeks what can be disproven, not confirmed',
        'temperature': 0.6
    },
    'quine': {
        'lora': 'quine-70b',
        'style': 'Naturalist - dissolves distinctions, challenges definitions',
        'temperature': 0.65
    },
    'arendt': {
        'lora': 'arendt-70b',
        'style': 'Political theorist - examines power, propaganda, banal evil',
        'temperature': 0.7
    },
    'zhuangzi': {
        'lora': 'zhuangzi-70b',
        'style': 'Daoist sage - seeks paradox, values uselessness, embraces perspective',
        'temperature': 0.8
    },
    'khaldun': {
        'lora': 'khaldun-70b',
        'style': 'Civilizational analyst - tracks cycles, material forces, group solidarity',
        'temperature': 0.65
    }
}

OBSERVER_THRESHOLD = 0.92  # Silence probability when consensus emerges


# ============================================================================
# DATABASE CONFIGURATION (Apache AGE)
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ambient_intelligence',
    'user': 'puck_user',
    'password': 'change_me_in_production'
}

AGE_GRAPH = 'quorum_graph'


# ============================================================================
# CONTEXT HASHING (with temporal decay)
# ============================================================================

def hash_context(query: str, last_queries: List[str] = None, 
                 gaze_target: str = "", location: str = "") -> str:
    """
    Generate context-aware hash with hourly rotation.
    Same conceptual query gets different treatment based on time/context.
    """
    timestamp_hour = int(time.time() / 3600)  # Rotates every hour
    
    context_string = f"{query}|"
    
    if last_queries:
        context_string += "|".join(last_queries[-3:]) + "|"
    
    context_string += f"{gaze_target}|{location}|{timestamp_hour}"
    
    return hashlib.sha256(context_string.encode()).hexdigest()[:16]


# ============================================================================
# OLLAMA INTERFACE
# ============================================================================

def ask_philosopher(philosopher: str, question: str, 
                   context_chain: str = "") -> Dict:
    """
    Query a single philosopher LoRA via Ollama.
    Returns: {philosopher, response, confidence, timestamp}
    """
    config = PHILOSOPHERS[philosopher]
    
    # Build prompt with chain context
    if context_chain:
        full_prompt = f"Previous arguments:\n{context_chain}\n\nNow respond to: {question}"
    else:
        full_prompt = question
    
    try:
        response = chat(
            model=config['lora'],
            messages=[{
                'role': 'user',
                'content': full_prompt
            }],
            options={
                'temperature': config['temperature'],
                'num_predict': 300  # Keep responses concise
            }
        )
        
        return {
            'philosopher': philosopher,
            'response': response['message']['content'],
            'confidence': 1.0,  # Ollama doesn't return confidence, set default
            'timestamp': datetime.utcnow().isoformat(),
            'style': config['style']
        }
    
    except Exception as e:
        print(f"ERROR querying {philosopher}: {e}")
        return None


# ============================================================================
# AGE DATABASE INTEGRATION
# ============================================================================

class QuorumDatabase:
    """Handle PostgreSQL + Apache AGE graph storage and pattern matching"""
    
    def __init__(self, config: Dict):
        if psycopg2 is None:
            print("WARNING: Database disabled (psycopg2 not installed)")
            self.conn = None
            return
        
        try:
            self.conn = psycopg2.connect(**config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            self._init_graph()
        except Exception as e:
            print(f"WARNING: Database connection failed: {e}")
            self.conn = None
    
    def _init_graph(self):
        """Initialize AGE graph and necessary tables"""
        if not self.conn:
            return
        
        try:
            # Create AGE extension if not exists
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS age;")
            
            # Load AGE
            self.cursor.execute("LOAD 'age';")
            
            # Set search path
            self.cursor.execute("SET search_path = ag_catalog, '$user', public;")
            
            # Create graph if not exists
            self.cursor.execute(f"""
                SELECT * FROM ag_catalog.create_graph('{AGE_GRAPH}') 
                WHERE NOT EXISTS (
                    SELECT 1 FROM ag_catalog.ag_graph WHERE name = '{AGE_GRAPH}'
                );
            """)
            
            # Create verdict tracking table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS quorum_verdicts (
                    id SERIAL PRIMARY KEY,
                    context_hash VARCHAR(16),
                    query TEXT,
                    verdict TEXT,
                    consensus_score FLOAT,
                    pattern_match FLOAT,
                    falsifiable BOOLEAN,
                    commercial BOOLEAN,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            self.conn.commit()
            print("✓ AGE graph initialized")
        
        except Exception as e:
            print(f"WARNING: Graph init failed: {e}")
            self.conn.rollback()
    
    def store_verdict(self, context_hash: str, query: str, verdict: str,
                     consensus: float, pattern_match: float = 0.0,
                     falsifiable: bool = True, commercial: bool = False):
        """Store a Quorum verdict in the database"""
        if not self.conn:
            return
        
        try:
            self.cursor.execute("""
                INSERT INTO quorum_verdicts 
                (context_hash, query, verdict, consensus_score, pattern_match, 
                 falsifiable, commercial)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (context_hash, query, verdict, consensus, pattern_match,
                  falsifiable, commercial))
            
            self.conn.commit()
        
        except Exception as e:
            print(f"WARNING: Failed to store verdict: {e}")
            self.conn.rollback()
    
    def get_pattern_match(self, query: str, threshold: float = 0.8) -> Optional[Dict]:
        """
        Check if query matches historical patterns.
        After 50+ verdicts, returns cached answer if similarity > threshold.
        """
        if not self.conn:
            return None
        
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as total FROM quorum_verdicts
            """)
            
            count = self.cursor.fetchone()['total']
            
            if count < 50:
                return None  # Need minimum 50 runs for pattern matching
            
            # Simple text similarity (in production, use PGVector embeddings)
            self.cursor.execute("""
                SELECT verdict, consensus_score, falsifiable, commercial,
                       similarity(query, %s) as match_score
                FROM quorum_verdicts
                WHERE similarity(query, %s) > %s
                ORDER BY match_score DESC
                LIMIT 1
            """, (query, query, threshold))
            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'cached_verdict': result['verdict'],
                    'pattern_match': result['match_score'],
                    'falsifiable': result['falsifiable'],
                    'commercial': result['commercial']
                }
            
            return None
        
        except Exception as e:
            print(f"WARNING: Pattern match failed: {e}")
            return None
    
    def close(self):
        if self.conn:
            self.conn.close()


# ============================================================================
# QUORUM CORE LOGIC
# ============================================================================

def run_quorum(query: str, context_hash: str = None, 
               last_queries: List[str] = None,
               db: QuorumDatabase = None) -> Dict:
    """
    Run the philosopher tribunal chain.
    Returns: {verdict, chain, consensus, pattern_match, philosophers}
    """
    
    # Generate context hash if not provided
    if context_hash is None:
        context_hash = hash_context(query, last_queries)
    
    print(f"\n{'='*80}")
    print(f"QUORUM INITIATED")
    print(f"Query: {query}")
    print(f"Context Hash: {context_hash}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")
    
    # Check for pattern match in database
    if db:
        pattern = db.get_pattern_match(query)
        if pattern:
            print(f"⚡ PATTERN MATCH: {pattern['pattern_match']:.2f}")
            print(f"   Cached verdict: {pattern['cached_verdict']}")
            print(f"   Falsifiable: {pattern['falsifiable']}")
            print(f"   Commercial: {pattern['commercial']}")
            print(f"\n   [Skipping full Quorum - returning cached result]\n")
            return {
                'verdict': pattern['cached_verdict'],
                'chain': [],
                'consensus': pattern['pattern_match'],
                'pattern_match': pattern['pattern_match'],
                'cached': True,
                'philosophers': []
            }
    
    # Run the philosopher chain
    chain = []
    accumulated_context = query
    
    for philosopher in PHILOSOPHERS.keys():
        print(f"→ {philosopher.upper()} analyzing...")
        
        result = ask_philosopher(philosopher, query, accumulated_context)
        
        if result:
            chain.append(result)
            print(f"  {result['response'][:120]}...")
            print()
            
            # Accumulate for next philosopher
            accumulated_context += f"\n\n{philosopher.upper()}: {result['response']}"
    
    # Calculate consensus (simple: check for keyword overlap)
    verdict = chain[-1]['response'] if chain else "No verdict reached"
    consensus_score = calculate_consensus(chain)
    
    # Check if Observer should enforce silence
    if consensus_score > OBSERVER_THRESHOLD:
        print(f"\n⊙ OBSERVER: Consensus {consensus_score:.2f} > {OBSERVER_THRESHOLD}")
        print(f"   Verdict is stable. Enforcing silence.\n")
        observer_active = True
    else:
        observer_active = False
    
    print(f"{'='*80}")
    print(f"FINAL VERDICT")
    print(f"{'='*80}")
    print(verdict)
    print(f"\nConsensus: {consensus_score:.2f}")
    print(f"Observer Active: {observer_active}")
    print(f"{'='*80}\n")
    
    # Store in database
    if db:
        # Simple heuristics for falsifiable/commercial flags
        falsifiable = not any(word in verdict.lower() 
                            for word in ['always', 'never', 'absolute', 'certain'])
        commercial = any(word in verdict.lower() 
                        for word in ['sell', 'buy', 'profit', 'market', 'product'])
        
        db.store_verdict(
            context_hash=context_hash,
            query=query,
            verdict=verdict,
            consensus=consensus_score,
            falsifiable=falsifiable,
            commercial=commercial
        )
    
    return {
        'verdict': verdict,
        'chain': chain,
        'consensus': consensus_score,
        'pattern_match': 0.0,
        'cached': False,
        'philosophers': [c['philosopher'] for c in chain],
        'observer_active': observer_active
    }


def calculate_consensus(chain: List[Dict]) -> float:
    """
    Calculate consensus score from philosopher chain.
    Simple implementation: check keyword overlap in responses.
    """
    if len(chain) < 2:
        return 0.0
    
    # Extract key terms from each response (words > 5 chars)
    term_sets = []
    for response in chain:
        words = response['response'].lower().split()
        terms = set(w.strip('.,!?;:') for w in words if len(w) > 5)
        term_sets.append(terms)
    
    # Calculate pairwise Jaccard similarity
    similarities = []
    for i in range(len(term_sets)):
        for j in range(i+1, len(term_sets)):
            intersection = len(term_sets[i] & term_sets[j])
            union = len(term_sets[i] | term_sets[j])
            if union > 0:
                similarities.append(intersection / union)
    
    return sum(similarities) / len(similarities) if similarities else 0.0


# ============================================================================
# AUTO-TREND ANALYSIS (runs on X/social media trends)
# ============================================================================

def analyze_trends(trends: List[str], db: QuorumDatabase = None):
    """
    Run Quorum on top social media trends.
    Auto-flags propaganda before breakfast.
    """
    print(f"\n{'='*80}")
    print(f"TREND ANALYSIS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*80}\n")
    
    results = []
    for i, trend in enumerate(trends, 1):
        print(f"[{i}/{len(trends)}] Analyzing: {trend}")
        result = run_quorum(trend, db=db)
        results.append({
            'trend': trend,
            'verdict': result['verdict'],
            'consensus': result['consensus'],
            'propaganda_risk': result['consensus'] < 0.3  # Low consensus = sus
        })
        print()
    
    # Summary
    print(f"\n{'='*80}")
    print("PROPAGANDA FLAGS")
    print(f"{'='*80}")
    
    flagged = [r for r in results if r['propaganda_risk']]
    if flagged:
        for item in flagged:
            print(f"⚠️  {item['trend']}")
            print(f"   Consensus: {item['consensus']:.2f}")
            print(f"   Verdict: {item['verdict'][:100]}...\n")
    else:
        print("No high-risk propaganda detected.\n")
    
    return results


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for Quorum"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Quorum - Philosopher Tribunal for Truth Forensics'
    )
    parser.add_argument('query', nargs='*', help='Query for the Quorum')
    parser.add_argument('--trends', nargs='+', help='Analyze social media trends')
    parser.add_argument('--no-db', action='store_true', help='Disable database storage')
    parser.add_argument('--export', type=str, help='Export verdict to JSON file')
    
    args = parser.parse_args()
    
    # Initialize database
    db = None if args.no_db else QuorumDatabase(DB_CONFIG)
    
    try:
        if args.trends:
            # Trend analysis mode
            results = analyze_trends(args.trends, db=db)
            
            if args.export:
                with open(args.export, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"✓ Results exported to {args.export}")
        
        elif args.query:
            # Single query mode
            query = ' '.join(args.query)
            result = run_quorum(query, db=db)
            
            if args.export:
                with open(args.export, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"✓ Verdict exported to {args.export}")
        
        else:
            # Interactive mode
            print("QUORUM - Interactive Mode")
            print("Type 'quit' to exit\n")
            
            while True:
                query = input("Query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if query:
                    run_quorum(query, db=db)
    
    finally:
        if db:
            db.close()


if __name__ == '__main__':
    main()

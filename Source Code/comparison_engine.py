#!/usr/bin/env python3
"""
Comparison Engine - Multi-Dimensional Collapse for Product/Concept Comparisons
Enables queries like: "Best EVOO by polyphenol across price windows"
Integrates: NetworkX (graph algorithms) + MADlib (in-DB ML) + Apache AGE (graph storage)
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

try:
    import networkx as nx
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: Install dependencies: pip install networkx psycopg2-binary")
    exit(1)


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

# Price window segmentation
PRICE_WINDOWS = {
    'budget': (0, 25),
    'mid_range': (25, 50),
    'premium': (50, 100),
    'luxury': (100, float('inf'))
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ComparisonNode:
    """A node in the comparison graph"""
    id: str
    name: str
    category: str
    attributes: Dict[str, float] = field(default_factory=dict)
    certifications: List[str] = field(default_factory=list)
    price: float = 0.0
    source_url: Optional[str] = None
    authority_score: float = 0.5
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class ComparisonResult:
    """Result of a comparison collapse"""
    winner: ComparisonNode
    runners_up: List[ComparisonNode]
    score: float
    method: str
    window: Optional[str] = None
    reasoning: str = ""


# ============================================================================
# INTENT DETECTOR (NLP)
# ============================================================================

class IntentDetector:
    """
    Detect query intent: comparison vs information vs command
    Enables proper routing through the system
    """
    
    COMPARISON_SIGNALS = [
        'compare', 'versus', 'vs', 'best', 'top', 'ranking',
        'which is better', 'difference between', 'pros and cons',
        'cheaper', 'more expensive', 'higher', 'lower', 'most', 'least'
    ]
    
    PRICE_WINDOW_SIGNALS = [
        'under', 'below', 'above', 'between', 'budget', 'cheap',
        'affordable', 'premium', 'luxury', 'expensive', 'price range'
    ]
    
    OPTIMIZATION_SIGNALS = [
        'best value', 'best ratio', 'bang for buck', 'worth it',
        'optimal', 'maximize', 'minimize'
    ]
    
    def detect(self, query: str) -> Dict:
        """
        Returns: {intent, sub_intents, confidence, attributes}
        """
        query_lower = query.lower()
        
        # Check for comparison intent
        comparison_score = sum(
            1 for signal in self.COMPARISON_SIGNALS 
            if signal in query_lower
        )
        
        # Check for price window intent
        price_window_score = sum(
            1 for signal in self.PRICE_WINDOW_SIGNALS
            if signal in query_lower
        )
        
        # Check for optimization intent
        optimization_score = sum(
            1 for signal in self.OPTIMIZATION_SIGNALS
            if signal in query_lower
        )
        
        # Determine primary intent
        if comparison_score >= 1 or optimization_score >= 1:
            intent = 'comparison'
        else:
            intent = 'information'
        
        # Extract comparison attributes
        attributes = self.extract_attributes(query_lower)
        
        return {
            'intent': intent,
            'sub_intents': {
                'price_windowed': price_window_score >= 1,
                'optimization': optimization_score >= 1,
                'multi_attribute': len(attributes) > 1
            },
            'confidence': min((comparison_score + optimization_score) / 3, 1.0),
            'attributes': attributes,
            'price_windows': self.extract_price_windows(query_lower)
        }
    
    def extract_attributes(self, query: str) -> List[str]:
        """Extract comparison attributes from query"""
        # Attribute keywords (domain-specific, extensible)
        attribute_keywords = {
            'polyphenol': 'polyphenol_content',
            'antioxidant': 'antioxidant_level',
            'organic': 'organic_certified',
            'certification': 'certification_score',
            'quality': 'quality_score',
            'taste': 'taste_rating',
            'freshness': 'harvest_date'
        }
        
        found = []
        for keyword, attr in attribute_keywords.items():
            if keyword in query:
                found.append(attr)
        
        return found if found else ['quality_score']  # Default
    
    def extract_price_windows(self, query: str) -> List[str]:
        """Extract mentioned price windows"""
        windows = []
        
        for window_name in PRICE_WINDOWS.keys():
            if window_name in query:
                windows.append(window_name)
        
        # Check for numeric ranges
        import re
        price_pattern = r'\$?(\d+)\s*(?:to|-)\s*\$?(\d+)'
        matches = re.findall(price_pattern, query)
        
        if matches:
            for low, high in matches:
                for name, (wlow, whigh) in PRICE_WINDOWS.items():
                    if int(low) >= wlow and int(high) <= whigh:
                        windows.append(name)
        
        return windows if windows else list(PRICE_WINDOWS.keys())


# ============================================================================
# GRAPH BUILDER (NetworkX + AGE)
# ============================================================================

class ComparisonGraphBuilder:
    """
    Build comparison graph from research results.
    Uses NetworkX for algorithms, syncs to AGE for persistence.
    """
    
    def __init__(self, db_config: Dict):
        self.config = db_config
        self.graph = nx.DiGraph()
        self.conn = None
    
    def connect(self):
        """Connect to PostgreSQL + AGE"""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Initialize AGE
            self.cursor.execute("LOAD 'age';")
            self.cursor.execute("SET search_path = ag_catalog, '$user', public;")
            
            print("✓ Connected to PostgreSQL + AGE")
        except Exception as e:
            print(f"WARNING: Database connection failed: {e}")
            self.conn = None
    
    def build_from_research(
        self,
        research_results: List[Dict],
        category: str
    ) -> nx.DiGraph:
        """
        Build comparison graph from meta-analyst research.
        
        Args:
            research_results: List of product/concept data from research
            category: Product category (e.g., 'evoo', 'supplement')
        
        Returns:
            NetworkX directed graph with comparison structure
        """
        self.graph.clear()
        
        # Create category hub node
        hub_id = f"category_{category}"
        self.graph.add_node(
            hub_id,
            type='category_hub',
            name=category.upper()
        )
        
        # Add product nodes
        for i, result in enumerate(research_results):
            node_id = f"product_{hashlib.md5(result['name'].encode()).hexdigest()[:8]}"
            
            node = ComparisonNode(
                id=node_id,
                name=result['name'],
                category=category,
                attributes=result.get('attributes', {}),
                certifications=result.get('certifications', []),
                price=result.get('price', 0),
                source_url=result.get('url'),
                authority_score=result.get('authority', 0.5)
            )
            
            self.graph.add_node(
                node_id,
                **node.__dict__
            )
            
            # Connect to category hub
            self.graph.add_edge(hub_id, node_id, relation='contains')
            
            # Create price window edges
            price_window = self.get_price_window(node.price)
            window_node_id = f"window_{price_window}"
            
            if not self.graph.has_node(window_node_id):
                self.graph.add_node(
                    window_node_id,
                    type='price_window',
                    name=price_window,
                    range=PRICE_WINDOWS[price_window]
                )
                self.graph.add_edge(hub_id, window_node_id, relation='has_window')
            
            self.graph.add_edge(window_node_id, node_id, relation='contains')
        
        # Create comparison edges between products
        self.create_comparison_edges()
        
        return self.graph
    
    def get_price_window(self, price: float) -> str:
        """Determine price window for a given price"""
        for window, (low, high) in PRICE_WINDOWS.items():
            if low <= price < high:
                return window
        return 'luxury'
    
    def create_comparison_edges(self):
        """Create edges between comparable products"""
        product_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get('category') and not d.get('type')
        ]
        
        for i, node_a in enumerate(product_nodes):
            for node_b in product_nodes[i+1:]:
                data_a = self.graph.nodes[node_a]
                data_b = self.graph.nodes[node_b]
                
                # Compare on primary attribute
                if 'attributes' in data_a and 'attributes' in data_b:
                    for attr in data_a['attributes']:
                        if attr in data_b['attributes']:
                            diff = data_a['attributes'][attr] - data_b['attributes'][attr]
                            
                            if diff > 0:
                                self.graph.add_edge(
                                    node_a, node_b,
                                    relation='better_than',
                                    attribute=attr,
                                    margin=diff
                                )
                            elif diff < 0:
                                self.graph.add_edge(
                                    node_b, node_a,
                                    relation='better_than',
                                    attribute=attr,
                                    margin=abs(diff)
                                )
    
    def sync_to_age(self):
        """Sync NetworkX graph to Apache AGE for persistence"""
        if not self.conn:
            print("WARNING: No database connection - skipping AGE sync")
            return
        
        try:
            # Create nodes in AGE
            for node_id, data in self.graph.nodes(data=True):
                props = json.dumps(data).replace("'", "''")
                
                self.cursor.execute(f"""
                    SELECT * FROM cypher('comparison_graph', $$
                        MERGE (n:ComparisonNode {{id: '{node_id}'}})
                        SET n += {props}
                        RETURN n
                    $$) as (n agtype);
                """)
            
            # Create edges in AGE
            for source, target, data in self.graph.edges(data=True):
                relation = data.get('relation', 'related_to')
                
                self.cursor.execute(f"""
                    SELECT * FROM cypher('comparison_graph', $$
                        MATCH (a:ComparisonNode {{id: '{source}'}})
                        MATCH (b:ComparisonNode {{id: '{target}'}})
                        MERGE (a)-[r:{relation}]->(b)
                        RETURN r
                    $$) as (r agtype);
                """)
            
            self.conn.commit()
            print(f"✓ Synced {self.graph.number_of_nodes()} nodes, "
                  f"{self.graph.number_of_edges()} edges to AGE")
        
        except Exception as e:
            print(f"WARNING: AGE sync failed: {e}")
            self.conn.rollback()


# ============================================================================
# COLLAPSE ALGORITHMS (NetworkX + MADlib Integration)
# ============================================================================

class CollapseEngine:
    """
    Multi-dimensional collapse algorithms.
    Finds optimal choices within price windows, then collapses to overall winner.
    """
    
    def __init__(self, graph: nx.DiGraph, db_config: Dict = None):
        self.graph = graph
        self.db_config = db_config
    
    async def collapse(
        self,
        target_attribute: str,
        price_windows: List[str] = None,
        optimization_goal: str = 'maximize'
    ) -> Dict[str, ComparisonResult]:
        """
        Multi-stage collapse:
        1. Collapse within each price window → winner per window
        2. Calculate price/benefit ratio for each winner
        3. Final collapse → best overall value
        
        Returns: Dict mapping window names to ComparisonResult
        """
        if price_windows is None:
            price_windows = list(PRICE_WINDOWS.keys())
        
        results = {}
        window_winners = []
        
        # Stage 1: Collapse per price window
        print(f"\n{'='*60}")
        print(f"STAGE 1: Per-Window Collapse")
        print(f"{'='*60}")
        
        for window in price_windows:
            window_result = await self.collapse_window(
                window, target_attribute, optimization_goal
            )
            
            if window_result:
                results[window] = window_result
                window_winners.append(window_result)
                
                print(f"\n[{window.upper()}]")
                print(f"  Winner: {window_result.winner.name}")
                print(f"  {target_attribute}: {window_result.winner.attributes.get(target_attribute, 'N/A')}")
                print(f"  Price: ${window_result.winner.price:.2f}")
                print(f"  Score: {window_result.score:.3f}")
        
        # Stage 2: Calculate price/benefit ratios
        print(f"\n{'='*60}")
        print(f"STAGE 2: Price/Benefit Ratio Analysis")
        print(f"{'='*60}")
        
        ratios = []
        for wr in window_winners:
            attr_value = wr.winner.attributes.get(target_attribute, 0)
            price = max(wr.winner.price, 1)  # Avoid division by zero
            
            ratio = attr_value / price
            ratios.append({
                'window': wr.window,
                'winner': wr.winner,
                'attribute_value': attr_value,
                'price': price,
                'ratio': ratio
            })
            
            print(f"  {wr.window}: {attr_value:.1f} / ${price:.2f} = {ratio:.4f}")
        
        # Stage 3: Final collapse to best ratio
        print(f"\n{'='*60}")
        print(f"STAGE 3: Final Collapse - Best Value")
        print(f"{'='*60}")
        
        if ratios:
            if optimization_goal == 'maximize':
                best = max(ratios, key=lambda x: x['ratio'])
            else:
                best = min(ratios, key=lambda x: x['ratio'])
            
            results['_best_value'] = ComparisonResult(
                winner=best['winner'],
                runners_up=[r['winner'] for r in ratios if r != best],
                score=best['ratio'],
                method='price_benefit_ratio',
                window=best['window'],
                reasoning=f"Best {target_attribute} per dollar: "
                         f"{best['attribute_value']:.1f} / ${best['price']:.2f} = "
                         f"{best['ratio']:.4f}"
            )
            
            print(f"\n✓ BEST VALUE: {best['winner'].name}")
            print(f"  From window: {best['window']}")
            print(f"  Ratio: {best['ratio']:.4f}")
        
        return results
    
    async def collapse_window(
        self,
        window: str,
        target_attribute: str,
        optimization_goal: str
    ) -> Optional[ComparisonResult]:
        """Collapse products within a price window to find the winner"""
        
        # Get products in this window
        window_node = f"window_{window}"
        
        if not self.graph.has_node(window_node):
            return None
        
        # Get all products connected to this window
        products = []
        for _, target in self.graph.edges(window_node):
            data = self.graph.nodes[target]
            if 'name' in data and 'attributes' in data:
                products.append(ComparisonNode(
                    id=target,
                    name=data['name'],
                    category=data.get('category', ''),
                    attributes=data.get('attributes', {}),
                    certifications=data.get('certifications', []),
                    price=data.get('price', 0),
                    source_url=data.get('source_url'),
                    authority_score=data.get('authority_score', 0.5)
                ))
        
        if not products:
            return None
        
        # Rank products by target attribute
        if optimization_goal == 'maximize':
            sorted_products = sorted(
                products,
                key=lambda p: p.attributes.get(target_attribute, 0),
                reverse=True
            )
        else:
            sorted_products = sorted(
                products,
                key=lambda p: p.attributes.get(target_attribute, float('inf'))
            )
        
        winner = sorted_products[0]
        
        # Calculate score using PageRank-like authority
        pagerank = nx.pagerank(self.graph.to_undirected())
        winner_pr = pagerank.get(winner.id, 0.5)
        
        # Composite score: attribute weight + authority
        attr_score = winner.attributes.get(target_attribute, 0) / 1000  # Normalize
        composite_score = (attr_score * 0.7) + (winner_pr * 0.2) + (winner.authority_score * 0.1)
        
        return ComparisonResult(
            winner=winner,
            runners_up=sorted_products[1:3],
            score=composite_score,
            method='attribute_ranking_with_authority',
            window=window,
            reasoning=f"Ranked by {target_attribute} with PageRank authority boost"
        )


# ============================================================================
# MAIN COMPARISON ENGINE
# ============================================================================

class ComparisonEngine:
    """
    Main orchestrator for comparison queries.
    Integrates: NLP → Research → Graph → Collapse → Output
    """
    
    def __init__(self, db_config: Dict = None):
        self.db_config = db_config or DB_CONFIG
        self.intent_detector = IntentDetector()
        self.graph_builder = ComparisonGraphBuilder(self.db_config)
    
    async def compare(
        self,
        query: str,
        research_results: List[Dict] = None
    ) -> Dict:
        """
        Full comparison pipeline.
        
        Args:
            query: Natural language comparison query
            research_results: Pre-fetched research data (or will use mock)
        
        Returns:
            Complete comparison results with winners per window + best value
        """
        print(f"\n{'='*80}")
        print(f"COMPARISON ENGINE v1.0")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        # Step 1: Detect intent
        intent = self.intent_detector.detect(query)
        
        print(f"Intent Analysis:")
        print(f"  Type: {intent['intent']}")
        print(f"  Confidence: {intent['confidence']:.2f}")
        print(f"  Price windowed: {intent['sub_intents']['price_windowed']}")
        print(f"  Optimization: {intent['sub_intents']['optimization']}")
        print(f"  Attributes: {intent['attributes']}")
        print(f"  Windows: {intent['price_windows']}")
        
        if intent['intent'] != 'comparison':
            return {
                'status': 'redirect',
                'message': 'Query does not appear to be a comparison',
                'intent': intent
            }
        
        # Step 2: Use research results or mock data
        if research_results is None:
            research_results = self.generate_mock_evoo_data()
        
        # Step 3: Build comparison graph
        print(f"\nBuilding comparison graph...")
        category = self.extract_category(query)
        graph = self.graph_builder.build_from_research(research_results, category)
        
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        
        # Step 4: Run collapse algorithm
        collapse_engine = CollapseEngine(graph, self.db_config)
        
        primary_attribute = intent['attributes'][0] if intent['attributes'] else 'quality_score'
        
        results = await collapse_engine.collapse(
            target_attribute=primary_attribute,
            price_windows=intent['price_windows'],
            optimization_goal='maximize'
        )
        
        # Step 5: Format output
        output = {
            'query': query,
            'intent': intent,
            'category': category,
            'primary_attribute': primary_attribute,
            'window_results': {},
            'best_value': None,
            'graph_stats': {
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges()
            }
        }
        
        for window, result in results.items():
            if window == '_best_value':
                output['best_value'] = {
                    'name': result.winner.name,
                    'price': result.winner.price,
                    'attribute_value': result.winner.attributes.get(primary_attribute, 0),
                    'ratio': result.score,
                    'window': result.window,
                    'reasoning': result.reasoning
                }
            else:
                output['window_results'][window] = {
                    'winner': result.winner.name,
                    'price': result.winner.price,
                    'attribute_value': result.winner.attributes.get(primary_attribute, 0),
                    'score': result.score,
                    'runners_up': [r.name for r in result.runners_up]
                }
        
        return output
    
    def extract_category(self, query: str) -> str:
        """Extract product category from query"""
        categories = {
            'evoo': ['evoo', 'olive oil', 'extra virgin'],
            'supplement': ['supplement', 'vitamin', 'mineral'],
            'wine': ['wine', 'cabernet', 'merlot', 'pinot'],
            'coffee': ['coffee', 'espresso', 'roast']
        }
        
        query_lower = query.lower()
        for category, keywords in categories.items():
            if any(kw in query_lower for kw in keywords):
                return category
        
        return 'product'
    
    def generate_mock_evoo_data(self) -> List[Dict]:
        """Generate mock EVOO data for testing"""
        return [
            # Budget
            {
                'name': 'California Olive Ranch Everyday',
                'price': 12.99,
                'attributes': {'polyphenol_content': 180, 'quality_score': 7.2},
                'certifications': ['COOC'],
                'authority': 0.75
            },
            {
                'name': 'Kirkland Organic EVOO',
                'price': 15.99,
                'attributes': {'polyphenol_content': 220, 'quality_score': 7.5},
                'certifications': ['USDA Organic'],
                'authority': 0.70
            },
            # Mid-range
            {
                'name': 'Cobram Estate Ultra Premium',
                'price': 28.99,
                'attributes': {'polyphenol_content': 350, 'quality_score': 8.5},
                'certifications': ['COOC', 'IOC'],
                'authority': 0.82
            },
            {
                'name': 'Gaea Fresh Greek EVOO',
                'price': 32.00,
                'attributes': {'polyphenol_content': 380, 'quality_score': 8.7},
                'certifications': ['PDO', 'EU Organic'],
                'authority': 0.80
            },
            # Premium
            {
                'name': 'The Governor Premium',
                'price': 55.00,
                'attributes': {'polyphenol_content': 520, 'quality_score': 9.2},
                'certifications': ['PDO', 'Organic', 'IOC Gold'],
                'authority': 0.90
            },
            {
                'name': 'Oleoestepa Egregio',
                'price': 65.00,
                'attributes': {'polyphenol_content': 610, 'quality_score': 9.4},
                'certifications': ['PDO Estepa', 'World Champion'],
                'authority': 0.92
            },
            # Luxury
            {
                'name': 'O-Med Arbequina',
                'price': 120.00,
                'attributes': {'polyphenol_content': 750, 'quality_score': 9.7},
                'certifications': ['PDO', 'NYIOOC Gold', 'Flos Olei'],
                'authority': 0.95
            },
            {
                'name': 'Oro Bailen Reserva Familiar',
                'price': 145.00,
                'attributes': {'polyphenol_content': 820, 'quality_score': 9.8},
                'certifications': ['DOP', 'World\'s Best', 'Flos Olei 100'],
                'authority': 0.98
            }
        ]


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    import sys
    
    if len(sys.argv) < 2:
        # Default demo query
        query = "Compare highest polyphenol EVOOs with certification across price windows, best value ratio"
    else:
        query = ' '.join(sys.argv[1:])
    
    engine = ComparisonEngine()
    results = await engine.compare(query)
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS")
    print(f"{'='*80}")
    
    print(f"\nCategory: {results['category']}")
    print(f"Primary Attribute: {results['primary_attribute']}")
    
    print(f"\n{'─'*40}")
    print("WINDOW WINNERS:")
    print(f"{'─'*40}")
    
    for window, data in results.get('window_results', {}).items():
        print(f"\n[{window.upper()}]")
        print(f"  Winner: {data['winner']}")
        print(f"  Price: ${data['price']:.2f}")
        print(f"  {results['primary_attribute']}: {data['attribute_value']}")
        print(f"  Score: {data['score']:.3f}")
        if data['runners_up']:
            print(f"  Runners-up: {', '.join(data['runners_up'][:2])}")
    
    if results.get('best_value'):
        print(f"\n{'━'*40}")
        print("🏆 BEST VALUE (FINAL COLLAPSE):")
        print(f"{'━'*40}")
        bv = results['best_value']
        print(f"  Winner: {bv['name']}")
        print(f"  From: {bv['window']} window")
        print(f"  Price: ${bv['price']:.2f}")
        print(f"  {results['primary_attribute']}: {bv['attribute_value']}")
        print(f"  Ratio: {bv['ratio']:.4f}")
        print(f"  Reasoning: {bv['reasoning']}")
    
    print(f"\n{'='*80}")


if __name__ == '__main__':
    asyncio.run(main())

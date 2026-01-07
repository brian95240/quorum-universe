#!/usr/bin/env python3
"""
QUORUM EXAMPLES - Common Usage Patterns
Demonstrates the philosopher tribunal in action
"""

from quorum import run_quorum, analyze_trends, QuorumDatabase, DB_CONFIG
import json


def example_1_basic_query():
    """Example 1: Simple truth evaluation"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Query")
    print("="*80)
    
    query = "Ivermectin cures cancer"
    
    db = QuorumDatabase(DB_CONFIG)
    result = run_quorum(query, db=db)
    
    print(f"\nQuery: {query}")
    print(f"Verdict: {result['verdict'][:200]}...")
    print(f"Consensus: {result['consensus']:.2f}")
    print(f"Philosophers involved: {', '.join(result['philosophers'])}")
    
    db.close()


def example_2_temporal_context():
    """Example 2: Same query, different times = different contexts"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Temporal Context Awareness")
    print("="*80)
    
    query = "Should I exercise now?"
    
    db = QuorumDatabase(DB_CONFIG)
    
    # Simulate morning query
    print("\n[Simulating 9 AM query]")
    result_morning = run_quorum(query, db=db)
    
    # In real usage, the hourly hash rotation would handle this automatically
    # Here we just show that the same query gets different context
    
    print(f"\nMorning verdict: {result_morning['verdict'][:150]}...")
    
    db.close()


def example_3_chain_building():
    """Example 3: Watch the philosopher chain evolve"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Philosopher Chain Evolution")
    print("="*80)
    
    query = "Is democracy the best form of government?"
    
    db = QuorumDatabase(DB_CONFIG)
    result = run_quorum(query, db=db)
    
    print("\nCHAIN PROGRESSION:")
    print("-"*80)
    
    for i, step in enumerate(result['chain'], 1):
        print(f"\n{i}. {step['philosopher'].upper()}")
        print(f"   Style: {step['style']}")
        print(f"   Response: {step['response'][:200]}...")
    
    print("\n" + "-"*80)
    print(f"FINAL CONSENSUS: {result['consensus']:.2f}")
    
    if result.get('observer_active'):
        print("⊙ OBSERVER: Enforced silence (consensus too high)")
    
    db.close()


def example_4_propaganda_detection():
    """Example 4: Auto-flag suspicious claims"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Propaganda Detection")
    print("="*80)
    
    suspicious_claims = [
        "Doctors don't want you to know this one weird trick",
        "Ancient civilization had advanced technology that was hidden",
        "Mainstream media is lying about everything",
        "This miracle supplement cures all diseases"
    ]
    
    db = QuorumDatabase(DB_CONFIG)
    
    for claim in suspicious_claims:
        print(f"\n→ Testing: {claim}")
        result = run_quorum(claim, db=db)
        
        # Low consensus = philosophers disagree = red flag
        if result['consensus'] < 0.30:
            print(f"   ⚠️ PROPAGANDA RISK: Consensus only {result['consensus']:.2f}")
            print(f"   Verdict: {result['verdict'][:120]}...")
        else:
            print(f"   ✓ Reasonable: Consensus {result['consensus']:.2f}")
    
    db.close()


def example_5_pattern_matching():
    """Example 5: Cached responses after 50+ verdicts"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Pattern Matching (Cached Responses)")
    print("="*80)
    
    db = QuorumDatabase(DB_CONFIG)
    
    # First query - full Quorum
    query1 = "Will Bitcoin reach $100,000?"
    print(f"\n→ First query: {query1}")
    result1 = run_quorum(query1, db=db)
    print(f"   Time: ~30 seconds (full Quorum)")
    print(f"   Cached: {result1.get('cached', False)}")
    
    # Similar query - should be cached (after 50+ total verdicts)
    query2 = "Will BTC hit 100k in 2026?"
    print(f"\n→ Similar query: {query2}")
    result2 = run_quorum(query2, db=db)
    print(f"   Time: ~0.2 seconds (pattern match)")
    print(f"   Cached: {result2.get('cached', False)}")
    
    if result2.get('cached'):
        print(f"   Pattern match score: {result2.get('pattern_match', 0):.2f}")
    
    db.close()


def example_6_trend_analysis():
    """Example 6: Batch analyze social media trends"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Social Media Trend Analysis")
    print("="*80)
    
    # Simulate trending topics from Twitter/X
    trending_topics = [
        "AI will replace all jobs by 2030",
        "New study shows coffee increases lifespan",
        "Government covering up UFO evidence",
        "Meditation improves mental health"
    ]
    
    db = QuorumDatabase(DB_CONFIG)
    results = analyze_trends(trending_topics, db=db)
    
    print("\n" + "="*80)
    print("RISK ASSESSMENT SUMMARY")
    print("="*80)
    
    for item in results:
        risk = "HIGH" if item['propaganda_risk'] else "LOW"
        print(f"\n[{risk} RISK] {item['trend']}")
        print(f"  Consensus: {item['consensus']:.2f}")
        print(f"  Verdict: {item['verdict'][:100]}...")
    
    db.close()


def example_7_context_aware_routing():
    """Example 7: Different contexts route to different experts"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Context-Aware Expert Routing")
    print("="*80)
    
    # Same question, different contexts
    base_query = "How do I optimize this?"
    
    contexts = [
        {
            'query': base_query,
            'last_queries': ["Python performance slow", "function taking too long"],
            'context_type': "Programming optimization"
        },
        {
            'query': base_query,
            'last_queries': ["workout routine", "muscle gains plateaued"],
            'context_type': "Fitness optimization"
        },
        {
            'query': base_query,
            'last_queries': ["startup burn rate", "customer acquisition cost"],
            'context_type': "Business optimization"
        }
    ]
    
    db = QuorumDatabase(DB_CONFIG)
    
    for ctx in contexts:
        print(f"\n→ Context: {ctx['context_type']}")
        print(f"   Previous queries: {ctx['last_queries']}")
        
        result = run_quorum(
            ctx['query'],
            last_queries=ctx['last_queries'],
            db=db
        )
        
        print(f"   Verdict: {result['verdict'][:150]}...")
    
    db.close()


def example_8_export_results():
    """Example 8: Export verdicts to JSON for external processing"""
    print("\n" + "="*80)
    print("EXAMPLE 8: Export Results")
    print("="*80)
    
    query = "Should governments regulate artificial intelligence?"
    
    db = QuorumDatabase(DB_CONFIG)
    result = run_quorum(query, db=db)
    
    # Export to JSON
    export_data = {
        'query': query,
        'verdict': result['verdict'],
        'consensus': result['consensus'],
        'philosophers': result['philosophers'],
        'timestamp': result['chain'][0]['timestamp'] if result['chain'] else None,
        'observer_active': result.get('observer_active', False),
        'full_chain': [
            {
                'philosopher': step['philosopher'],
                'response': step['response'],
                'style': step['style']
            }
            for step in result['chain']
        ]
    }
    
    filename = '/tmp/quorum_verdict.json'
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Results exported to {filename}")
    print(f"  File size: {len(json.dumps(export_data))} bytes")
    
    db.close()


def example_9_custom_philosopher_order():
    """Example 9: Custom philosopher selection for specific domains"""
    print("\n" + "="*80)
    print("EXAMPLE 9: Custom Philosopher Selection")
    print("="*80)
    
    # For scientific claims, prioritize Popper and Hume
    scientific_query = "Homeopathy is effective medicine"
    
    # For political claims, prioritize Arendt and Khaldun
    political_query = "Authoritarian governments are more efficient"
    
    # Note: This would require modifying the PHILOSOPHERS dict
    # or adding a custom order parameter to run_quorum()
    
    db = QuorumDatabase(DB_CONFIG)
    
    print(f"\n→ Scientific claim: {scientific_query}")
    result_sci = run_quorum(scientific_query, db=db)
    print(f"   Consensus: {result_sci['consensus']:.2f}")
    
    print(f"\n→ Political claim: {political_query}")
    result_pol = run_quorum(political_query, db=db)
    print(f"   Consensus: {result_pol['consensus']:.2f}")
    
    db.close()


def example_10_integration_with_puck():
    """Example 10: How the Quorum integrates with ambient intelligence"""
    print("\n" + "="*80)
    print("EXAMPLE 10: Ambient Intelligence Integration")
    print("="*80)
    
    print("""
    INTEGRATION FLOW:
    
    1. User says: "Is this investment opportunity legitimate?"
       └─ Mentra glasses capture voice
    
    2. Eye-tracking detects user is looking at:
       └─ Website URL: scam-investment.com
    
    3. GPS location: 
       └─ User's home office
    
    4. Context hash generated:
       └─ query + gaze + location + time_of_day
    
    5. Quorum selector routes to:
       └─ Yale-Law (legal) + Popper (skepticism) + Khaldun (financial)
    
    6. Response synthesized and delivered via:
       └─ Bone-conduction audio
       └─ AR overlay showing red flags
    
    7. Verdict stored in AGE graph:
       └─ Linked to: website, user history, similar scams
    
    Example code:
    
    ```python
    # On glasses
    def on_voice_command(text, gaze_url, location):
        response = requests.post('http://puck.local:8000/quorum', json={
            'query': text,
            'gaze': gaze_url,
            'location': location
        })
        
        verdict = response.json()['verdict']
        confidence = response.json()['consensus']
        
        # Display via bone-conduction
        play_audio(verdict)
        
        # Show visual confidence meter
        overlay_confidence(confidence)
    ```
    """)


def main():
    """Run all examples"""
    examples = [
        ("Basic Query", example_1_basic_query),
        ("Temporal Context", example_2_temporal_context),
        ("Chain Evolution", example_3_chain_building),
        ("Propaganda Detection", example_4_propaganda_detection),
        ("Pattern Matching", example_5_pattern_matching),
        ("Trend Analysis", example_6_trend_analysis),
        ("Context Routing", example_7_context_aware_routing),
        ("Export Results", example_8_export_results),
        ("Custom Selection", example_9_custom_philosopher_order),
        ("Puck Integration", example_10_integration_with_puck),
    ]
    
    print("\n" + "="*80)
    print("QUORUM EXAMPLES - Select an example to run")
    print("="*80)
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"{i:2d}. {name}")
    
    print(f"\n 0. Run all examples")
    print(f"99. Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == "0":
        for name, func in examples:
            try:
                func()
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"ERROR: {e}")
    
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        idx = int(choice) - 1
        examples[idx][1]()
    
    elif choice == "99":
        print("Exiting...")
    
    else:
        print("Invalid choice")


if __name__ == '__main__':
    main()

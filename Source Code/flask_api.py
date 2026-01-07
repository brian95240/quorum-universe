#!/usr/bin/env python3
"""
Flask API - Voice-Triggered Comparison & Routing Gateway
Enables NLP intent routing, n8n webhook automation, and real-time streaming
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import asyncio
import json
from functools import wraps
import time
from typing import Dict, Optional
import hashlib

# Local imports (these would be your existing modules)
# from comparison_engine import ComparisonEngine, IntentDetector
# from archetype_router import ArchetypeRouter
# from meta_analyst_unified import MetaAnalystUnified
# from voice_debate_system import VoiceAwareDebateSystem

app = Flask(__name__)
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    'rate_limit': 100,  # requests per minute
    'cache_ttl': 3600,  # 1 hour
    'max_query_length': 1000,
    'enable_webhooks': True,
    'n8n_webhook_url': 'http://localhost:5678/webhook/',
    'voice_enabled': True
}

# In-memory cache (replace with Redis in production)
cache = {}
rate_limits = {}


# ============================================================================
# MIDDLEWARE
# ============================================================================

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        current_minute = int(time.time() / 60)
        
        key = f"{ip}:{current_minute}"
        rate_limits[key] = rate_limits.get(key, 0) + 1
        
        if rate_limits[key] > CONFIG['rate_limit']:
            return jsonify({
                'error': 'Rate limit exceeded',
                'limit': CONFIG['rate_limit'],
                'reset_in': 60 - (int(time.time()) % 60)
            }), 429
        
        return f(*args, **kwargs)
    return decorated


def async_route(f):
    """Wrapper to run async functions in Flask"""
    @wraps(f)
    def decorated(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return decorated


# ============================================================================
# INTENT ROUTING
# ============================================================================

class APIIntentRouter:
    """Route queries to appropriate engines based on NLP intent"""
    
    COMPARISON_SIGNALS = [
        'compare', 'versus', 'vs', 'best', 'top', 'ranking',
        'which is better', 'difference between', 'pros and cons',
        'cheaper', 'more expensive', 'higher', 'lower', 'most', 'least',
        'best value', 'best ratio'
    ]
    
    RESEARCH_SIGNALS = [
        'what is', 'how does', 'explain', 'tell me about',
        'what are', 'describe', 'define'
    ]
    
    TRUTH_SIGNALS = [
        'is it true', 'verify', 'fact check', 'debunk',
        'propaganda', 'reliable', 'trustworthy'
    ]
    
    @classmethod
    def route(cls, query: str) -> Dict:
        """Determine which engine should handle the query"""
        query_lower = query.lower()
        
        # Check for comparison intent
        if any(signal in query_lower for signal in cls.COMPARISON_SIGNALS):
            return {
                'engine': 'comparison',
                'confidence': 0.9,
                'endpoint': '/api/compare'
            }
        
        # Check for truth verification
        if any(signal in query_lower for signal in cls.TRUTH_SIGNALS):
            return {
                'engine': 'quorum',
                'confidence': 0.85,
                'endpoint': '/api/verify'
            }
        
        # Check for research intent
        if any(signal in query_lower for signal in cls.RESEARCH_SIGNALS):
            return {
                'engine': 'meta_analyst',
                'confidence': 0.8,
                'endpoint': '/api/research'
            }
        
        # Default to archetype router
        return {
            'engine': 'archetype_router',
            'confidence': 0.7,
            'endpoint': '/api/route'
        }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'engines': {
            'comparison': 'ready',
            'archetype_router': 'ready',
            'meta_analyst': 'ready',
            'quorum': 'ready',
            'voice': CONFIG['voice_enabled']
        }
    })


@app.route('/api/intent', methods=['POST'])
@rate_limit
def detect_intent():
    """
    Detect query intent and route to appropriate engine.
    
    Request:
        {"query": "Compare best EVOOs under $50"}
    
    Response:
        {"engine": "comparison", "confidence": 0.9, "endpoint": "/api/compare"}
    """
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    if len(query) > CONFIG['max_query_length']:
        return jsonify({'error': f'Query too long (max {CONFIG["max_query_length"]})'}), 400
    
    routing = APIIntentRouter.route(query)
    
    return jsonify({
        'query': query,
        'routing': routing,
        'auto_redirect': True
    })


@app.route('/api/compare', methods=['POST'])
@rate_limit
@async_route
async def compare():
    """
    Multi-dimensional comparison with price window collapse.
    
    Request:
        {
            "query": "Compare highest polyphenol EVOOs across price windows",
            "options": {
                "price_windows": ["budget", "mid_range", "premium"],
                "primary_attribute": "polyphenol_content",
                "optimization": "maximize"
            }
        }
    
    Response:
        {
            "window_results": {...},
            "best_value": {...},
            "graph_stats": {...}
        }
    """
    data = request.json
    query = data.get('query', '')
    options = data.get('options', {})
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Check cache
    cache_key = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    if cache_key in cache:
        cached = cache[cache_key]
        if time.time() - cached['timestamp'] < CONFIG['cache_ttl']:
            return jsonify({**cached['data'], 'cached': True})
    
    # Mock comparison engine (replace with actual import)
    # engine = ComparisonEngine()
    # results = await engine.compare(query)
    
    # Mock results for API demonstration
    results = {
        'query': query,
        'primary_attribute': options.get('primary_attribute', 'quality_score'),
        'window_results': {
            'budget': {
                'winner': 'Kirkland Organic EVOO',
                'price': 15.99,
                'attribute_value': 220,
                'score': 0.756
            },
            'mid_range': {
                'winner': 'Gaea Fresh Greek EVOO',
                'price': 32.00,
                'attribute_value': 380,
                'score': 0.823
            },
            'premium': {
                'winner': 'Oleoestepa Egregio',
                'price': 65.00,
                'attribute_value': 610,
                'score': 0.891
            }
        },
        'best_value': {
            'name': 'Kirkland Organic EVOO',
            'window': 'budget',
            'price': 15.99,
            'attribute_value': 220,
            'ratio': 13.76,
            'reasoning': 'Best polyphenol per dollar: 220 / $15.99 = 13.76'
        },
        'timestamp': time.time()
    }
    
    # Cache result
    cache[cache_key] = {
        'data': results,
        'timestamp': time.time()
    }
    
    # Trigger n8n webhook if enabled
    if CONFIG['enable_webhooks']:
        trigger_webhook('comparison_complete', results)
    
    return jsonify(results)


@app.route('/api/route', methods=['POST'])
@rate_limit
@async_route
async def route_query():
    """
    Route query through archetype system.
    
    Request:
        {
            "query": "Explain quantum entanglement",
            "context": {"hour": 14, "last_queries": [...]}
        }
    """
    data = request.json
    query = data.get('query', '')
    context = data.get('context', {})
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Mock archetype routing (replace with actual import)
    # router = ArchetypeRouter(DB_CONFIG)
    # result = await router.route(query, context)
    
    results = {
        'query': query,
        'archetypes_used': ['caltech_physics', 'princeton_math'],
        'synthesis': 'Quantum entanglement is a phenomenon where particles become correlated...',
        'confidence': 0.87,
        'execution_time': 3.2
    }
    
    return jsonify(results)


@app.route('/api/research', methods=['POST'])
@rate_limit
@async_route
async def research():
    """
    Meta-analyst research for unknown topics.
    
    Request:
        {"query": "Latest dark matter detection methods"}
    """
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Mock meta-analyst (replace with actual import)
    # analyst = MetaAnalystUnified()
    # result = await analyst.research(query)
    
    results = {
        'query': query,
        'synthesis': 'Current dark matter detection methods include...',
        'sources': [
            {'title': 'arXiv: Dark Matter Review', 'authority': 0.92},
            {'title': 'Nature: Detection Methods', 'authority': 0.90}
        ],
        'confidence': 0.88
    }
    
    return jsonify(results)


@app.route('/api/verify', methods=['POST'])
@rate_limit
@async_route
async def verify():
    """
    Quorum truth verification (philosopher tribunal).
    
    Request:
        {"claim": "AI will replace all jobs by 2030"}
    """
    data = request.json
    claim = data.get('claim', '')
    
    if not claim:
        return jsonify({'error': 'Claim required'}), 400
    
    # Mock Quorum (replace with actual import)
    # result = run_quorum(claim)
    
    results = {
        'claim': claim,
        'verdict': 'The claim lacks empirical support and is unfalsifiable in its current form...',
        'consensus': 0.34,
        'philosophers': ['hume', 'popper', 'quine', 'arendt', 'zhuangzi', 'khaldun'],
        'propaganda_risk': True,
        'falsifiable': False
    }
    
    return jsonify(results)


@app.route('/api/voice', methods=['POST'])
@rate_limit
@async_route
async def voice_input():
    """
    Voice input processing with intent detection and routing.
    
    Request:
        {"audio_base64": "...", "format": "wav"}
        OR
        {"transcript": "Compare best EVOOs..."}
    """
    data = request.json
    
    # If transcript provided, use directly
    transcript = data.get('transcript', '')
    
    if not transcript and 'audio_base64' in data:
        # Would process audio here with Whisper
        # For now, mock transcription
        transcript = "Compare the best EVOOs with highest polyphenols"
    
    if not transcript:
        return jsonify({'error': 'Audio or transcript required'}), 400
    
    # Detect intent and route
    routing = APIIntentRouter.route(transcript)
    
    # Execute appropriate engine
    if routing['engine'] == 'comparison':
        # Simulate calling compare endpoint
        results = {
            'transcript': transcript,
            'intent': 'comparison',
            'action': 'Executing comparison analysis...',
            'redirect': '/api/compare'
        }
    else:
        results = {
            'transcript': transcript,
            'intent': routing['engine'],
            'redirect': routing['endpoint']
        }
    
    return jsonify(results)


@app.route('/api/stream', methods=['POST'])
@rate_limit
def stream_response():
    """
    Server-sent events for streaming responses.
    Useful for long-running comparisons or research.
    """
    data = request.json
    query = data.get('query', '')
    
    def generate():
        # Stream events
        yield f"data: {json.dumps({'status': 'started', 'query': query})}\n\n"
        
        # Simulate processing stages
        stages = [
            {'stage': 'intent_detection', 'progress': 10},
            {'stage': 'research', 'progress': 30},
            {'stage': 'graph_building', 'progress': 50},
            {'stage': 'collapse_analysis', 'progress': 70},
            {'stage': 'synthesis', 'progress': 90},
            {'stage': 'complete', 'progress': 100}
        ]
        
        for stage in stages:
            time.sleep(0.5)  # Simulate processing
            yield f"data: {json.dumps(stage)}\n\n"
        
        # Final result
        result = {
            'status': 'complete',
            'best_value': 'Kirkland Organic EVOO',
            'ratio': 13.76
        }
        yield f"data: {json.dumps(result)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


# ============================================================================
# WEBHOOK INTEGRATION (n8n)
# ============================================================================

def trigger_webhook(event_type: str, data: Dict):
    """Trigger n8n webhook for automation"""
    import requests
    
    try:
        webhook_url = f"{CONFIG['n8n_webhook_url']}{event_type}"
        requests.post(webhook_url, json={
            'event': event_type,
            'timestamp': time.time(),
            'data': data
        }, timeout=5)
    except Exception as e:
        print(f"Webhook failed: {e}")


# ============================================================================
# N8N WORKFLOW ENDPOINTS
# ============================================================================

@app.route('/webhook/n8n/trigger', methods=['POST'])
def n8n_trigger():
    """
    Endpoint for n8n to trigger comparisons.
    Enables scheduled or event-driven analysis.
    """
    data = request.json
    
    # Validate n8n signature (in production)
    # signature = request.headers.get('X-N8N-Signature')
    
    action = data.get('action', '')
    
    if action == 'scheduled_comparison':
        # Run scheduled comparison (e.g., daily EVOO update)
        query = data.get('query', 'Compare top EVOOs today')
        # Async trigger comparison
        return jsonify({
            'status': 'queued',
            'query': query,
            'job_id': hashlib.md5(f"{query}{time.time()}".encode()).hexdigest()[:12]
        })
    
    elif action == 'price_alert':
        # Handle price change alert
        product = data.get('product', '')
        new_price = data.get('new_price', 0)
        
        return jsonify({
            'status': 'alert_processed',
            'product': product,
            'new_price': new_price,
            'action': 're-running comparison'
        })
    
    return jsonify({'error': 'Unknown action'}), 400


# ============================================================================
# METRICS & MONITORING (Prometheus)
# ============================================================================

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus metrics endpoint.
    """
    metrics_text = """
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{endpoint="/api/compare"} 142
api_requests_total{endpoint="/api/route"} 89
api_requests_total{endpoint="/api/research"} 45

# HELP api_latency_seconds API latency
# TYPE api_latency_seconds histogram
api_latency_seconds_bucket{endpoint="/api/compare",le="1.0"} 45
api_latency_seconds_bucket{endpoint="/api/compare",le="5.0"} 120
api_latency_seconds_bucket{endpoint="/api/compare",le="10.0"} 140

# HELP cache_hit_ratio Cache hit ratio
# TYPE cache_hit_ratio gauge
cache_hit_ratio 0.67

# HELP active_connections Active connections
# TYPE active_connections gauge
active_connections 12
"""
    return Response(metrics_text, mimetype='text/plain')


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ambient Intelligence API')
    parser.add_argument('--port', type=int, default=8000, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          AMBIENT INTELLIGENCE API v1.0                       ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints:                                                  ║
║    POST /api/intent    - Detect query intent                 ║
║    POST /api/compare   - Multi-dimensional comparison        ║
║    POST /api/route     - Archetype routing                   ║
║    POST /api/research  - Meta-analyst research               ║
║    POST /api/verify    - Quorum truth verification           ║
║    POST /api/voice     - Voice input processing              ║
║    POST /api/stream    - Streaming responses (SSE)           ║
║    GET  /health        - Health check                        ║
║    GET  /metrics       - Prometheus metrics                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=args.debug)

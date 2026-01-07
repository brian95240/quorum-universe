#!/usr/bin/env python3
"""
Quorum Universe - Production API Server
Symbiotic endpoints for cross-platform connectivity
Live URL mappings for PC/Mac/Raspberry Pi/servers/mobile
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from config import (
    NEON_CONNECTION_STRING,
    ARCHETYPES,
    TOTAL_ARCHETYPES,
    TOTAL_CORPUS_GB,
    URL_REGISTRY,
    SYMBIOTIC_FOLDERS,
    detect_platform,
    get_data_path,
)
from symbiotic_connector import SymbioticConnector, ArchetypeDataDumpManager, DeviceType
from graph_engine import QuorumGraphEngine, NodeType, EdgeType, GraphNode, GraphEdge

# =============================================================================
# PYDANTIC MODELS
# =============================================================================
class QueryRequest(BaseModel):
    query: str
    archetypes: Optional[List[str]] = None
    max_archetypes: int = Field(default=3, ge=1, le=26)
    include_tribunal: bool = False
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    response: str
    archetypes_used: List[str]
    quality_score: float
    latency_ms: float
    cached: bool = False
    tribunal_verdict: Optional[Dict] = None

class IngestRequest(BaseModel):
    archetype: str
    source_url: str
    data_type: str = "text"
    metadata: Optional[Dict] = None

class SyncRequest(BaseModel):
    archetype: Optional[str] = None
    direction: str = "pull"  # pull or push
    device_id: Optional[str] = None

class DeviceRegistration(BaseModel):
    device_type: str
    hostname: str
    capabilities: List[str] = []
    data_paths: Dict[str, str] = {}

class SynergyAnalysisRequest(BaseModel):
    min_synergy_score: float = Field(default=0.5, ge=0.0, le=1.0)
    include_hidden_connections: bool = True
    include_optimization_opportunities: bool = True

# =============================================================================
# GLOBAL STATE
# =============================================================================
class AppState:
    connector: Optional[SymbioticConnector] = None
    graph_engine: Optional[QuorumGraphEngine] = None
    data_manager: Optional[ArchetypeDataDumpManager] = None
    connected_websockets: Dict[str, WebSocket] = {}
    metrics: Dict[str, Any] = {
        'queries_processed': 0,
        'cache_hits': 0,
        'cache_misses': 0,
        'total_latency_ms': 0,
        'synergies_detected': 0,
    }

state = AppState()

# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application state"""
    # Startup
    print("🚀 Starting Quorum Universe API Server...")
    
    # Initialize symbiotic connector
    state.connector = SymbioticConnector()
    await state.connector.register_device()
    print(f"  ✓ Device registered: {state.connector.device_id}")
    
    # Initialize graph engine
    state.graph_engine = QuorumGraphEngine()
    await state.graph_engine.connect()
    print(f"  ✓ Graph engine initialized with {TOTAL_ARCHETYPES} archetypes")
    
    # Initialize data manager
    state.data_manager = ArchetypeDataDumpManager(state.connector)
    print(f"  ✓ Data manager ready for {TOTAL_CORPUS_GB} GB corpus")
    
    print("✅ Quorum Universe API Server ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Quorum Universe API Server...")
    await state.connector.close()
    await state.graph_engine.close()
    print("✅ Shutdown complete")

# =============================================================================
# FASTAPI APP
# =============================================================================
app = FastAPI(
    title="Quorum Universe API",
    description="Symbiotic cross-platform ambient intelligence system",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS for cross-platform access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": detect_platform(),
        "device_id": state.connector.device_id if state.connector else None,
    }

@app.get("/status")
async def system_status():
    """Comprehensive system status"""
    graph_stats = await state.graph_engine.get_graph_stats() if state.graph_engine else {}
    
    return {
        "status": "operational",
        "platform": detect_platform(),
        "device_id": state.connector.device_id if state.connector else None,
        "device_type": state.connector.device_type.value if state.connector else None,
        "archetypes": {
            "total": TOTAL_ARCHETYPES,
            "corpus_size_gb": TOTAL_CORPUS_GB,
        },
        "graph": graph_stats,
        "metrics": state.metrics,
        "connected_devices": len(state.connected_websockets),
        "timestamp": datetime.utcnow().isoformat(),
    }

# =============================================================================
# LIVE URL ENDPOINTS
# =============================================================================
@app.get("/api/v1/urls")
async def get_live_urls():
    """Get all live URLs for symbiotic connections"""
    return await state.connector.get_live_urls() if state.connector else {}

@app.get("/api/v1/folders")
async def get_symbiotic_folders():
    """Get symbiotic folder structure for current platform"""
    return state.connector.get_symbiotic_folder_map() if state.connector else {}

@app.get("/api/v1/archetypes")
async def get_archetypes():
    """Get all 26 archetypes with their configurations"""
    return {
        "total": TOTAL_ARCHETYPES,
        "total_corpus_gb": TOTAL_CORPUS_GB,
        "archetypes": {
            name: {
                "id": config["id"],
                "cluster": config["cluster"],
                "corpus_size_gb": config["corpus_size_gb"],
                "temperature": config["temperature"],
                "domains": config["domains"],
                "training_sources": config.get("training_sources", []),
                "data_dump_paths": config["data_dump_paths"],
            }
            for name, config in ARCHETYPES.items()
        }
    }

@app.get("/api/v1/archetypes/{archetype_name}")
async def get_archetype(archetype_name: str):
    """Get specific archetype configuration"""
    if archetype_name not in ARCHETYPES:
        raise HTTPException(status_code=404, detail=f"Archetype not found: {archetype_name}")
    
    config = ARCHETYPES[archetype_name]
    return {
        "name": archetype_name,
        "id": config["id"],
        "cluster": config["cluster"],
        "corpus_size_gb": config["corpus_size_gb"],
        "temperature": config["temperature"],
        "style": config["style"],
        "domains": config["domains"],
        "training_sources": config.get("training_sources", []),
        "data_dump_paths": config["data_dump_paths"],
    }

@app.get("/api/v1/archetypes/{archetype_name}/paths")
async def get_archetype_paths(archetype_name: str):
    """Get data paths for specific archetype on current platform"""
    if archetype_name not in ARCHETYPES:
        raise HTTPException(status_code=404, detail=f"Archetype not found: {archetype_name}")
    
    paths = state.connector.get_archetype_data_paths() if state.connector else {}
    return {
        "archetype": archetype_name,
        "platform": detect_platform(),
        "paths": paths.get(archetype_name, {}),
    }

# =============================================================================
# QUERY ENDPOINTS
# =============================================================================
@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a query through the archetype pipeline"""
    start_time = time.time()
    state.metrics['queries_processed'] += 1
    
    # Generate query hash for caching
    query_hash = hashlib.sha256(request.query.encode()).hexdigest()
    
    # Check cache (simplified - would use Redis in production)
    cached = False
    
    # Select archetypes
    if request.archetypes:
        selected_archetypes = [a for a in request.archetypes if a in ARCHETYPES]
    else:
        # Auto-select based on query (simplified)
        selected_archetypes = list(ARCHETYPES.keys())[:request.max_archetypes]
    
    # Generate response (simplified - would use actual LLM in production)
    response_text = f"[Quorum Universe Response]\n\nQuery: {request.query}\n\n"
    response_text += f"Analyzed by {len(selected_archetypes)} archetypes:\n"
    for arch in selected_archetypes:
        config = ARCHETYPES[arch]
        response_text += f"- {arch} ({config['cluster']}): {config['style']}\n"
    
    # Calculate quality score (simplified)
    quality_score = 0.85 + (len(selected_archetypes) * 0.01)
    
    latency_ms = (time.time() - start_time) * 1000
    state.metrics['total_latency_ms'] += latency_ms
    
    return QueryResponse(
        query=request.query,
        response=response_text,
        archetypes_used=selected_archetypes,
        quality_score=min(quality_score, 1.0),
        latency_ms=latency_ms,
        cached=cached,
    )

# =============================================================================
# DATA INGESTION ENDPOINTS
# =============================================================================
@app.post("/api/v1/ingest")
async def ingest_data(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest training data for an archetype"""
    if request.archetype not in ARCHETYPES:
        raise HTTPException(status_code=404, detail=f"Archetype not found: {request.archetype}")
    
    # Queue ingestion in background
    async def do_ingest():
        result = await state.data_manager.ingest_training_data(
            request.archetype,
            request.source_url,
            request.data_type
        )
        # Broadcast to connected devices
        await broadcast_message({
            'type': 'ingestion_complete',
            'archetype': request.archetype,
            'result': result,
        })
    
    background_tasks.add_task(do_ingest)
    
    return {
        "status": "queued",
        "archetype": request.archetype,
        "source_url": request.source_url,
    }

@app.get("/api/v1/ingest/stats")
async def get_ingestion_stats(archetype: Optional[str] = None):
    """Get ingestion statistics"""
    return await state.data_manager.get_archetype_stats(archetype)

@app.get("/api/v1/ingest/local")
async def get_local_data_summary():
    """Get summary of locally stored training data"""
    return state.data_manager.get_local_data_summary()

# =============================================================================
# SYNC ENDPOINTS
# =============================================================================
@app.post("/api/v1/sync")
async def sync_data(request: SyncRequest):
    """Sync archetype data between devices"""
    if request.archetype and request.archetype not in ARCHETYPES:
        raise HTTPException(status_code=404, detail=f"Archetype not found: {request.archetype}")
    
    if request.archetype:
        result = await state.connector.sync_archetype_data(
            request.archetype,
            request.direction
        )
        return result
    else:
        # Sync all archetypes
        results = {}
        for archetype_name in ARCHETYPES.keys():
            results[archetype_name] = await state.connector.sync_archetype_data(
                archetype_name,
                request.direction
            )
        return {"archetypes": results}

@app.get("/api/v1/sync/devices")
async def get_connected_devices():
    """Get list of connected devices in symbiotic network"""
    return {
        "devices": [
            device.to_dict()
            for device in state.connector.connected_devices.values()
        ] if state.connector else [],
        "total": len(state.connector.connected_devices) if state.connector else 0,
    }

# =============================================================================
# GRAPH & SYNERGY ENDPOINTS
# =============================================================================
@app.get("/api/v1/graph/stats")
async def get_graph_stats():
    """Get graph statistics"""
    return await state.graph_engine.get_graph_stats() if state.graph_engine else {}

@app.post("/api/v1/graph/synergies")
async def analyze_synergies(request: SynergyAnalysisRequest):
    """Analyze graph for hidden synergies and optimization opportunities"""
    if not state.graph_engine:
        raise HTTPException(status_code=503, detail="Graph engine not initialized")
    
    result = await state.graph_engine.detect_synergies(request.min_synergy_score)
    state.metrics['synergies_detected'] += len(result.clusters)
    
    response = {
        "clusters": [c.to_dict() for c in result.clusters],
        "total_synergy_score": result.total_synergy_score,
        "analysis_timestamp": result.analysis_timestamp.isoformat(),
    }
    
    if request.include_hidden_connections:
        response["hidden_connections"] = result.hidden_connections
    
    if request.include_optimization_opportunities:
        response["optimization_opportunities"] = result.optimization_opportunities
    
    return response

@app.get("/api/v1/graph/export")
async def export_graph():
    """Export graph to JSON format"""
    return await state.graph_engine.export_to_json() if state.graph_engine else {}

# =============================================================================
# WEBSOCKET ENDPOINTS (Real-time Sync)
# =============================================================================
@app.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket):
    """WebSocket endpoint for real-time sync between devices"""
    await websocket.accept()
    device_id = None
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('type') == 'register':
                device_id = data.get('device_id', f"ws_{id(websocket)}")
                state.connected_websockets[device_id] = websocket
                
                # Broadcast device joined
                await broadcast_message({
                    'type': 'device_joined',
                    'device_id': device_id,
                    'device_type': data.get('device_type'),
                    'capabilities': data.get('capabilities', []),
                }, exclude=device_id)
                
                # Send current device list
                await websocket.send_json({
                    'type': 'device_list',
                    'devices': list(state.connected_websockets.keys()),
                })
            
            elif data.get('type') == 'sync_request':
                # Handle sync request
                archetype = data.get('archetype')
                if archetype and archetype in ARCHETYPES:
                    result = await state.connector.sync_archetype_data(archetype, 'pull')
                    await websocket.send_json({
                        'type': 'sync_response',
                        'archetype': archetype,
                        'result': result,
                    })
            
            elif data.get('type') == 'broadcast':
                # Broadcast message to all devices
                await broadcast_message(data.get('payload', {}), exclude=device_id)
    
    except WebSocketDisconnect:
        if device_id and device_id in state.connected_websockets:
            del state.connected_websockets[device_id]
            await broadcast_message({
                'type': 'device_left',
                'device_id': device_id,
            })

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic status updates
            await websocket.send_json({
                'type': 'status',
                'metrics': state.metrics,
                'connected_devices': len(state.connected_websockets),
                'timestamp': datetime.utcnow().isoformat(),
            })
            await asyncio.sleep(5)
    
    except WebSocketDisconnect:
        pass

async def broadcast_message(message: Dict, exclude: Optional[str] = None):
    """Broadcast message to all connected WebSocket clients"""
    for device_id, ws in state.connected_websockets.items():
        if device_id != exclude:
            try:
                await ws.send_json(message)
            except:
                pass

# =============================================================================
# METRICS ENDPOINT (Prometheus compatible)
# =============================================================================
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_text = []
    
    metrics_text.append(f"# HELP quorum_queries_total Total queries processed")
    metrics_text.append(f"# TYPE quorum_queries_total counter")
    metrics_text.append(f"quorum_queries_total {state.metrics['queries_processed']}")
    
    metrics_text.append(f"# HELP quorum_cache_hits_total Total cache hits")
    metrics_text.append(f"# TYPE quorum_cache_hits_total counter")
    metrics_text.append(f"quorum_cache_hits_total {state.metrics['cache_hits']}")
    
    metrics_text.append(f"# HELP quorum_synergies_detected_total Total synergies detected")
    metrics_text.append(f"# TYPE quorum_synergies_detected_total counter")
    metrics_text.append(f"quorum_synergies_detected_total {state.metrics['synergies_detected']}")
    
    metrics_text.append(f"# HELP quorum_connected_devices Current connected devices")
    metrics_text.append(f"# TYPE quorum_connected_devices gauge")
    metrics_text.append(f"quorum_connected_devices {len(state.connected_websockets)}")
    
    metrics_text.append(f"# HELP quorum_archetypes_total Total archetypes")
    metrics_text.append(f"# TYPE quorum_archetypes_total gauge")
    metrics_text.append(f"quorum_archetypes_total {TOTAL_ARCHETYPES}")
    
    return "\n".join(metrics_text)

# =============================================================================
# MAIN
# =============================================================================
def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()

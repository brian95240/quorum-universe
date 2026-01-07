#!/usr/bin/env python3
"""
Quorum Universe - Symbiotic Connection Manager
Cross-platform connectivity for PC/Mac/Raspberry Pi/servers/mobile
Live URL mappings and real-time sync across all devices
"""

import asyncio
import hashlib
import json
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import aiohttp
import asyncpg

from config import (
    NEON_CONNECTION_STRING,
    ARCHETYPES,
    SYMBIOTIC_FOLDERS,
    URL_REGISTRY,
    REDIS_CONFIG,
    COMPRESSION_CONFIG,
    detect_platform,
    get_data_path,
    PlatformConfig,
)

# =============================================================================
# DEVICE TYPES FOR SYMBIOTIC NETWORK
# =============================================================================
class DeviceType(Enum):
    PC_WINDOWS = "pc_windows"
    PC_LINUX = "pc_linux"
    MAC = "mac"
    RASPBERRY_PI = "raspberry_pi"
    ARM_SERVER = "arm_server"
    CLOUD_SERVER = "cloud_server"
    MOBILE_IOS = "mobile_ios"
    MOBILE_ANDROID = "mobile_android"
    UNKNOWN = "unknown"

@dataclass
class ConnectedDevice:
    """Represents a device in the symbiotic network"""
    device_id: str
    device_type: DeviceType
    hostname: str
    ip_address: str
    last_seen: datetime
    sync_status: str = "idle"
    capabilities: List[str] = field(default_factory=list)
    data_paths: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type.value,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'last_seen': self.last_seen.isoformat(),
            'sync_status': self.sync_status,
            'capabilities': self.capabilities,
            'data_paths': self.data_paths,
        }

# =============================================================================
# SYMBIOTIC CONNECTION MANAGER
# =============================================================================
class SymbioticConnector:
    """
    Manages cross-platform symbiotic connections
    Enables real-time sync between PC/Mac/Raspberry Pi/servers/mobile
    """
    
    def __init__(self, base_url: str = None):
        self.platform_config = PlatformConfig()
        self.connected_devices: Dict[str, ConnectedDevice] = {}
        self.sync_callbacks: List[Callable] = []
        self.db_pool: Optional[asyncpg.Pool] = None
        self.ws_connections: Set[aiohttp.ClientWebSocketResponse] = set()
        
        # Set base URL for all endpoints
        if base_url:
            URL_REGISTRY.set_base_url(base_url)
        
        # Generate unique device ID
        self.device_id = self._generate_device_id()
        self.device_type = self._detect_device_type()
        
        # Initialize folder structure
        self._init_symbiotic_folders()
    
    def _generate_device_id(self) -> str:
        """Generate unique device identifier"""
        hostname = platform.node()
        mac = hex(hash(hostname))[:12]
        return f"quorum-{self.platform_config.platform}-{mac}"
    
    def _detect_device_type(self) -> DeviceType:
        """Detect current device type"""
        plat = detect_platform()
        mapping = {
            'windows': DeviceType.PC_WINDOWS,
            'linux_server': DeviceType.PC_LINUX,
            'macos': DeviceType.MAC,
            'raspberry_pi': DeviceType.RASPBERRY_PI,
            'arm_server': DeviceType.ARM_SERVER,
        }
        return mapping.get(plat, DeviceType.UNKNOWN)
    
    def _init_symbiotic_folders(self):
        """Initialize symbiotic folder structure for current platform"""
        base_path = self.platform_config.base_data_path
        
        for folder_name, config in SYMBIOTIC_FOLDERS.items():
            folder_path = base_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            
            for subfolder in config['subfolders']:
                (folder_path / subfolder).mkdir(parents=True, exist_ok=True)
        
        # Create archetype-specific folders
        for archetype_name, archetype_config in ARCHETYPES.items():
            for path_type, rel_path in archetype_config['data_dump_paths'].items():
                full_path = base_path / rel_path.lstrip('/')
                full_path.mkdir(parents=True, exist_ok=True)
    
    async def connect_to_database(self) -> asyncpg.Pool:
        """Establish connection to Neon PostgreSQL"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                NEON_CONNECTION_STRING,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
        return self.db_pool
    
    async def register_device(self) -> Dict:
        """Register this device in the symbiotic network"""
        pool = await self.connect_to_database()
        
        device_data = {
            'device_id': self.device_id,
            'device_type': self.device_type.value,
            'hostname': platform.node(),
            'platform': self.platform_config.platform,
            'data_path': str(self.platform_config.base_data_path),
            'capabilities': self._get_device_capabilities(),
            'registered_at': datetime.utcnow().isoformat(),
        }
        
        async with pool.acquire() as conn:
            # Upsert device registration
            await conn.execute("""
                INSERT INTO quorum.sessions (session_key, user_id, state, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                ON CONFLICT (session_key) 
                DO UPDATE SET state = $3, updated_at = NOW()
            """, f"device:{self.device_id}", self.device_type.value, json.dumps(device_data))
        
        return device_data
    
    def _get_device_capabilities(self) -> List[str]:
        """Determine device capabilities"""
        capabilities = ['query', 'cache']
        
        # Check for GPU
        try:
            import torch
            if torch.cuda.is_available():
                capabilities.append('gpu_inference')
        except ImportError:
            pass
        
        # Check available memory
        try:
            import psutil
            mem_gb = psutil.virtual_memory().total / (1024**3)
            if mem_gb >= 32:
                capabilities.extend(['full_inference', 'embedding_generation'])
            elif mem_gb >= 16:
                capabilities.append('partial_inference')
        except ImportError:
            pass
        
        # Platform-specific capabilities
        if self.device_type == DeviceType.RASPBERRY_PI:
            capabilities.extend(['edge_inference', 'sensor_integration'])
        elif self.device_type in [DeviceType.PC_WINDOWS, DeviceType.PC_LINUX, DeviceType.MAC]:
            capabilities.extend(['full_ui', 'local_storage'])
        elif self.device_type == DeviceType.CLOUD_SERVER:
            capabilities.extend(['high_throughput', 'distributed_processing'])
        
        return capabilities
    
    async def sync_archetype_data(self, archetype_name: str, direction: str = 'pull') -> Dict:
        """
        Sync archetype training data between devices
        direction: 'pull' (from server) or 'push' (to server)
        """
        if archetype_name not in ARCHETYPES:
            raise ValueError(f"Unknown archetype: {archetype_name}")
        
        archetype = ARCHETYPES[archetype_name]
        base_path = self.platform_config.base_data_path
        
        sync_result = {
            'archetype': archetype_name,
            'direction': direction,
            'files_synced': 0,
            'bytes_transferred': 0,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        for path_type, rel_path in archetype['data_dump_paths'].items():
            local_path = base_path / rel_path.lstrip('/')
            
            if direction == 'pull':
                # Pull data from server
                async with aiohttp.ClientSession() as session:
                    url = f"{URL_REGISTRY.sync_archetypes}/{archetype_name}/{path_type}"
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.read()
                                # Save to local path
                                (local_path / 'sync_manifest.json').write_bytes(data)
                                sync_result['files_synced'] += 1
                                sync_result['bytes_transferred'] += len(data)
                    except Exception as e:
                        sync_result['errors'] = sync_result.get('errors', [])
                        sync_result['errors'].append(str(e))
            
            elif direction == 'push':
                # Push local data to server
                if local_path.exists():
                    for file_path in local_path.rglob('*'):
                        if file_path.is_file():
                            async with aiohttp.ClientSession() as session:
                                url = f"{URL_REGISTRY.sync_archetypes}/{archetype_name}/{path_type}"
                                data = file_path.read_bytes()
                                try:
                                    async with session.post(url, data=data) as response:
                                        if response.status == 200:
                                            sync_result['files_synced'] += 1
                                            sync_result['bytes_transferred'] += len(data)
                                except Exception as e:
                                    sync_result['errors'] = sync_result.get('errors', [])
                                    sync_result['errors'].append(str(e))
        
        return sync_result
    
    async def establish_realtime_sync(self, on_message: Callable = None):
        """Establish WebSocket connection for real-time sync"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(URL_REGISTRY.ws_sync) as ws:
                    self.ws_connections.add(ws)
                    
                    # Send device registration
                    await ws.send_json({
                        'type': 'register',
                        'device_id': self.device_id,
                        'device_type': self.device_type.value,
                        'capabilities': self._get_device_capabilities(),
                    })
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            if data.get('type') == 'sync_request':
                                # Handle sync request from another device
                                await self._handle_sync_request(data, ws)
                            
                            elif data.get('type') == 'device_update':
                                # Update connected devices list
                                self._update_connected_devices(data)
                            
                            if on_message:
                                await on_message(data)
                        
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                    
                    self.ws_connections.discard(ws)
            
            except Exception as e:
                print(f"WebSocket connection error: {e}")
    
    async def _handle_sync_request(self, request: Dict, ws):
        """Handle incoming sync request from another device"""
        archetype = request.get('archetype')
        path_type = request.get('path_type')
        
        if archetype and path_type:
            base_path = self.platform_config.base_data_path
            local_path = base_path / ARCHETYPES[archetype]['data_dump_paths'][path_type].lstrip('/')
            
            if local_path.exists():
                # Send file list
                files = [str(f.relative_to(local_path)) for f in local_path.rglob('*') if f.is_file()]
                await ws.send_json({
                    'type': 'sync_response',
                    'archetype': archetype,
                    'path_type': path_type,
                    'files': files,
                    'device_id': self.device_id,
                })
    
    def _update_connected_devices(self, data: Dict):
        """Update the list of connected devices"""
        device_id = data.get('device_id')
        if device_id and device_id != self.device_id:
            self.connected_devices[device_id] = ConnectedDevice(
                device_id=device_id,
                device_type=DeviceType(data.get('device_type', 'unknown')),
                hostname=data.get('hostname', 'unknown'),
                ip_address=data.get('ip_address', ''),
                last_seen=datetime.utcnow(),
                capabilities=data.get('capabilities', []),
            )
    
    def get_symbiotic_folder_map(self) -> Dict[str, str]:
        """Get mapping of symbiotic folders for current platform"""
        base_path = self.platform_config.base_data_path
        folder_map = {}
        
        for folder_name, config in SYMBIOTIC_FOLDERS.items():
            folder_path = base_path / folder_name
            folder_map[folder_name] = {
                'path': str(folder_path),
                'description': config['description'],
                'sync_priority': config['sync_priority'],
                'subfolders': {
                    sub: str(folder_path / sub) for sub in config['subfolders']
                }
            }
        
        return folder_map
    
    def get_archetype_data_paths(self) -> Dict[str, Dict[str, str]]:
        """Get all archetype data dump paths for current platform"""
        base_path = self.platform_config.base_data_path
        paths = {}
        
        for archetype_name, archetype_config in ARCHETYPES.items():
            paths[archetype_name] = {
                path_type: str(base_path / rel_path.lstrip('/'))
                for path_type, rel_path in archetype_config['data_dump_paths'].items()
            }
        
        return paths
    
    async def get_live_urls(self) -> Dict[str, str]:
        """Get all live URLs for symbiotic connections"""
        return {
            'api': {
                'base': URL_REGISTRY.api_base,
                'query': URL_REGISTRY.api_query,
                'ingest': URL_REGISTRY.api_ingest,
                'sync': URL_REGISTRY.api_sync,
                'health': URL_REGISTRY.api_health,
            },
            'websocket': {
                'realtime': URL_REGISTRY.ws_realtime,
                'sync': URL_REGISTRY.ws_sync,
                'mentra': URL_REGISTRY.ws_mentra,
            },
            'sync': {
                'folder': URL_REGISTRY.sync_folder,
                'archetypes': URL_REGISTRY.sync_archetypes,
                'embeddings': URL_REGISTRY.sync_embeddings,
            },
            'monitoring': {
                'prometheus': URL_REGISTRY.metrics_prometheus,
                'grafana': URL_REGISTRY.metrics_grafana,
            }
        }
    
    async def close(self):
        """Close all connections"""
        for ws in self.ws_connections:
            await ws.close()
        
        if self.db_pool:
            await self.db_pool.close()


# =============================================================================
# DATA DUMP MANAGER FOR ARCHETYPE TRAINING
# =============================================================================
class ArchetypeDataDumpManager:
    """
    Manages data dumps for training all 26 archetypes
    Handles ingestion, compression, and distribution across symbiotic network
    """
    
    def __init__(self, connector: SymbioticConnector):
        self.connector = connector
        self.base_path = connector.platform_config.base_data_path
    
    async def ingest_training_data(
        self,
        archetype_name: str,
        source_url: str,
        data_type: str = 'text'
    ) -> Dict:
        """Ingest training data for an archetype"""
        if archetype_name not in ARCHETYPES:
            raise ValueError(f"Unknown archetype: {archetype_name}")
        
        archetype = ARCHETYPES[archetype_name]
        data_path = self.base_path / archetype['data_dump_paths']['primary'].lstrip('/')
        
        result = {
            'archetype': archetype_name,
            'source': source_url,
            'status': 'pending',
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Generate filename from URL hash
                        url_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]
                        filename = f"{url_hash}_{data_type}.dat"
                        
                        # Compress if enabled
                        if COMPRESSION_CONFIG['min_size_bytes'] < len(content):
                            try:
                                import zstandard as zstd
                                compressor = zstd.ZstdCompressor(level=COMPRESSION_CONFIG['level'])
                                content = compressor.compress(content)
                                filename += '.zst'
                            except ImportError:
                                pass
                        
                        # Save to data path
                        file_path = data_path / filename
                        file_path.write_bytes(content)
                        
                        result['status'] = 'success'
                        result['file_path'] = str(file_path)
                        result['size_bytes'] = len(content)
                        
                        # Record in database
                        pool = await self.connector.connect_to_database()
                        async with pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO quorum.documents (title, source, archetype_id, file_path, size_bytes)
                                VALUES ($1, $2, $3, $4, $5)
                            """, source_url, source_url, archetype['id'], str(file_path), len(content))
                    else:
                        result['status'] = 'failed'
                        result['error'] = f"HTTP {response.status}"
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    async def get_archetype_stats(self, archetype_name: str = None) -> Dict:
        """Get statistics for archetype training data"""
        pool = await self.connector.connect_to_database()
        
        async with pool.acquire() as conn:
            if archetype_name:
                archetype = ARCHETYPES.get(archetype_name)
                if not archetype:
                    return {'error': f"Unknown archetype: {archetype_name}"}
                
                row = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as document_count,
                        COALESCE(SUM(size_bytes), 0) as total_bytes,
                        COALESCE(SUM(chunk_count), 0) as total_chunks
                    FROM quorum.documents
                    WHERE archetype_id = $1
                """, archetype['id'])
                
                return {
                    'archetype': archetype_name,
                    'document_count': row['document_count'],
                    'total_bytes': row['total_bytes'],
                    'total_chunks': row['total_chunks'],
                    'corpus_target_gb': archetype['corpus_size_gb'],
                }
            else:
                # Get stats for all archetypes
                rows = await conn.fetch("""
                    SELECT 
                        a.name,
                        COUNT(d.id) as document_count,
                        COALESCE(SUM(d.size_bytes), 0) as total_bytes
                    FROM quorum.archetypes a
                    LEFT JOIN quorum.documents d ON a.id = d.archetype_id
                    GROUP BY a.id, a.name
                    ORDER BY a.id
                """)
                
                return {
                    'archetypes': [
                        {
                            'name': row['name'],
                            'document_count': row['document_count'],
                            'total_bytes': row['total_bytes'],
                        }
                        for row in rows
                    ]
                }
    
    def get_local_data_summary(self) -> Dict:
        """Get summary of locally stored training data"""
        summary = {
            'platform': self.connector.platform_config.platform,
            'base_path': str(self.base_path),
            'archetypes': {},
        }
        
        for archetype_name, archetype in ARCHETYPES.items():
            archetype_summary = {
                'paths': {},
                'total_files': 0,
                'total_bytes': 0,
            }
            
            for path_type, rel_path in archetype['data_dump_paths'].items():
                full_path = self.base_path / rel_path.lstrip('/')
                if full_path.exists():
                    files = list(full_path.rglob('*'))
                    file_count = len([f for f in files if f.is_file()])
                    total_size = sum(f.stat().st_size for f in files if f.is_file())
                    
                    archetype_summary['paths'][path_type] = {
                        'path': str(full_path),
                        'file_count': file_count,
                        'size_bytes': total_size,
                    }
                    archetype_summary['total_files'] += file_count
                    archetype_summary['total_bytes'] += total_size
            
            summary['archetypes'][archetype_name] = archetype_summary
        
        return summary


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
async def create_symbiotic_connector(base_url: str = None) -> SymbioticConnector:
    """Create and initialize a symbiotic connector"""
    connector = SymbioticConnector(base_url)
    await connector.register_device()
    return connector


async def get_all_live_urls(base_url: str) -> Dict:
    """Get all live URLs for the Quorum Universe system"""
    URL_REGISTRY.set_base_url(base_url)
    return {
        'api': {
            'base': URL_REGISTRY.api_base,
            'query': URL_REGISTRY.api_query,
            'ingest': URL_REGISTRY.api_ingest,
            'sync': URL_REGISTRY.api_sync,
            'health': URL_REGISTRY.api_health,
        },
        'websocket': {
            'realtime': URL_REGISTRY.ws_realtime,
            'sync': URL_REGISTRY.ws_sync,
            'mentra': URL_REGISTRY.ws_mentra,
        },
        'sync': {
            'folder': URL_REGISTRY.sync_folder,
            'archetypes': URL_REGISTRY.sync_archetypes,
            'embeddings': URL_REGISTRY.sync_embeddings,
        },
        'monitoring': {
            'prometheus': URL_REGISTRY.metrics_prometheus,
            'grafana': URL_REGISTRY.metrics_grafana,
        }
    }


if __name__ == "__main__":
    # Test symbiotic connector
    async def test():
        connector = SymbioticConnector()
        print(f"Device ID: {connector.device_id}")
        print(f"Device Type: {connector.device_type}")
        print(f"\nSymbiotic Folders:")
        for name, info in connector.get_symbiotic_folder_map().items():
            print(f"  {name}: {info['path']}")
        
        print(f"\nArchetype Data Paths (first 3):")
        paths = connector.get_archetype_data_paths()
        for name in list(paths.keys())[:3]:
            print(f"  {name}:")
            for path_type, path in paths[name].items():
                print(f"    {path_type}: {path}")
    
    asyncio.run(test())

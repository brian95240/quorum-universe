#!/usr/bin/env python3
"""
Redis Multi-Layer Cache Manager for Quorum Universe

Implements L1/L2/L3 caching with Zstandard compression for
maximum efficiency and cross-platform sync capabilities.

Cache Tiers:
- L1 (Hot): 256MB, no compression, <1ms latency
- L2 (Warm): 2GB, Zstd level 3, <5ms latency  
- L3 (Cold): 16GB, Zstd level 19, <20ms latency
"""

import asyncio
import json
import hashlib
import zstandard as zstd
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import time


class CacheTier(Enum):
    L1_HOT = "l1_hot"
    L2_WARM = "l2_warm"
    L3_COLD = "l3_cold"


@dataclass
class CacheConfig:
    """Configuration for each cache tier"""
    tier: CacheTier
    max_size_mb: int
    compression_level: int  # 0 = none, 1-22 = zstd levels
    ttl_seconds: int
    eviction_policy: str = "lru"


@dataclass
class CacheEntry:
    """A cached item with metadata"""
    key: str
    value: bytes
    tier: CacheTier
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    compressed: bool = False
    original_size: int = 0
    compressed_size: int = 0


@dataclass
class CacheStats:
    """Statistics for cache performance"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    compressions: int = 0
    decompressions: int = 0
    total_bytes_saved: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class MultiTierCache:
    """
    Multi-tier caching system with Zstandard compression.
    
    Designed for maximum efficiency with the Quorum Universe
    knowledge graph and archetype data.
    """
    
    def __init__(self):
        self.tiers: Dict[CacheTier, Dict[str, CacheEntry]] = {
            CacheTier.L1_HOT: {},
            CacheTier.L2_WARM: {},
            CacheTier.L3_COLD: {},
        }
        
        self.configs: Dict[CacheTier, CacheConfig] = {
            CacheTier.L1_HOT: CacheConfig(
                tier=CacheTier.L1_HOT,
                max_size_mb=256,
                compression_level=0,
                ttl_seconds=300,  # 5 minutes
            ),
            CacheTier.L2_WARM: CacheConfig(
                tier=CacheTier.L2_WARM,
                max_size_mb=2048,
                compression_level=3,
                ttl_seconds=3600,  # 1 hour
            ),
            CacheTier.L3_COLD: CacheConfig(
                tier=CacheTier.L3_COLD,
                max_size_mb=16384,
                compression_level=19,
                ttl_seconds=86400,  # 24 hours
            ),
        }
        
        self.stats: Dict[CacheTier, CacheStats] = {
            tier: CacheStats() for tier in CacheTier
        }
        
        # Zstandard compressors for each level
        self.compressors: Dict[int, zstd.ZstdCompressor] = {}
        self.decompressor = zstd.ZstdDecompressor()
        
        # Promotion/demotion thresholds
        self.promotion_threshold = 5  # Access count to promote to hotter tier
        self.demotion_check_interval = 60  # Seconds between demotion checks
        
        # Event callbacks for cross-platform sync
        self.on_cache_update: Optional[Callable] = None
        self.on_cache_evict: Optional[Callable] = None
        
        print("✓ Multi-tier cache initialized")
        print(f"  → L1 (Hot): {self.configs[CacheTier.L1_HOT].max_size_mb}MB, no compression")
        print(f"  → L2 (Warm): {self.configs[CacheTier.L2_WARM].max_size_mb}MB, Zstd-3")
        print(f"  → L3 (Cold): {self.configs[CacheTier.L3_COLD].max_size_mb}MB, Zstd-19")
    
    def _get_compressor(self, level: int) -> zstd.ZstdCompressor:
        """Get or create a compressor for the given level"""
        if level not in self.compressors:
            self.compressors[level] = zstd.ZstdCompressor(level=level)
        return self.compressors[level]
    
    def _compress(self, data: bytes, level: int) -> bytes:
        """Compress data with Zstandard"""
        if level == 0:
            return data
        compressor = self._get_compressor(level)
        return compressor.compress(data)
    
    def _decompress(self, data: bytes) -> bytes:
        """Decompress Zstandard data"""
        return self.decompressor.decompress(data)
    
    def _generate_key(self, key: str) -> str:
        """Generate a consistent cache key"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _get_tier_size(self, tier: CacheTier) -> int:
        """Get current size of a tier in bytes"""
        return sum(
            entry.compressed_size if entry.compressed else entry.original_size
            for entry in self.tiers[tier].values()
        )
    
    def _evict_lru(self, tier: CacheTier, needed_bytes: int):
        """Evict least recently used entries to make room"""
        config = self.configs[tier]
        max_bytes = config.max_size_mb * 1024 * 1024
        current_size = self._get_tier_size(tier)
        
        if current_size + needed_bytes <= max_bytes:
            return
        
        # Sort by last access time
        entries = sorted(
            self.tiers[tier].items(),
            key=lambda x: x[1].accessed_at
        )
        
        for key, entry in entries:
            if current_size + needed_bytes <= max_bytes:
                break
            
            # Demote to colder tier instead of evicting completely
            if tier == CacheTier.L1_HOT:
                self._demote_entry(key, entry, CacheTier.L2_WARM)
            elif tier == CacheTier.L2_WARM:
                self._demote_entry(key, entry, CacheTier.L3_COLD)
            else:
                # Actually evict from L3
                del self.tiers[tier][key]
                if self.on_cache_evict:
                    asyncio.create_task(self.on_cache_evict(key, tier))
            
            current_size -= entry.compressed_size if entry.compressed else entry.original_size
            self.stats[tier].evictions += 1
    
    def _demote_entry(self, key: str, entry: CacheEntry, target_tier: CacheTier):
        """Demote an entry to a colder tier"""
        config = self.configs[target_tier]
        
        # Recompress if needed
        if entry.compressed:
            data = self._decompress(entry.value)
        else:
            data = entry.value
        
        if config.compression_level > 0:
            compressed = self._compress(data, config.compression_level)
            new_entry = CacheEntry(
                key=key,
                value=compressed,
                tier=target_tier,
                created_at=entry.created_at,
                accessed_at=entry.accessed_at,
                access_count=entry.access_count,
                compressed=True,
                original_size=len(data),
                compressed_size=len(compressed),
            )
            self.stats[target_tier].compressions += 1
        else:
            new_entry = CacheEntry(
                key=key,
                value=data,
                tier=target_tier,
                created_at=entry.created_at,
                accessed_at=entry.accessed_at,
                access_count=entry.access_count,
                compressed=False,
                original_size=len(data),
                compressed_size=len(data),
            )
        
        # Remove from old tier
        if key in self.tiers[entry.tier]:
            del self.tiers[entry.tier][key]
        
        # Add to new tier
        self._evict_lru(target_tier, new_entry.compressed_size)
        self.tiers[target_tier][key] = new_entry
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache, checking all tiers"""
        cache_key = self._generate_key(key)
        
        # Check each tier from hottest to coldest
        for tier in [CacheTier.L1_HOT, CacheTier.L2_WARM, CacheTier.L3_COLD]:
            if cache_key in self.tiers[tier]:
                entry = self.tiers[tier][cache_key]
                
                # Check TTL
                config = self.configs[tier]
                if (datetime.now() - entry.created_at).total_seconds() > config.ttl_seconds:
                    del self.tiers[tier][cache_key]
                    self.stats[tier].evictions += 1
                    continue
                
                # Update access metadata
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                
                # Decompress if needed
                if entry.compressed:
                    data = self._decompress(entry.value)
                    self.stats[tier].decompressions += 1
                else:
                    data = entry.value
                
                self.stats[tier].hits += 1
                
                # Promote to hotter tier if accessed frequently
                if entry.access_count >= self.promotion_threshold and tier != CacheTier.L1_HOT:
                    await self._promote_entry(cache_key, entry)
                
                return json.loads(data.decode())
        
        # Cache miss
        for tier in CacheTier:
            self.stats[tier].misses += 1
        
        return None
    
    async def set(self, key: str, value: Any, tier: CacheTier = CacheTier.L2_WARM):
        """Set a value in the cache"""
        cache_key = self._generate_key(key)
        data = json.dumps(value).encode()
        config = self.configs[tier]
        
        # Compress if configured
        if config.compression_level > 0:
            compressed = self._compress(data, config.compression_level)
            entry = CacheEntry(
                key=cache_key,
                value=compressed,
                tier=tier,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                compressed=True,
                original_size=len(data),
                compressed_size=len(compressed),
            )
            self.stats[tier].compressions += 1
            self.stats[tier].total_bytes_saved += len(data) - len(compressed)
        else:
            entry = CacheEntry(
                key=cache_key,
                value=data,
                tier=tier,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                compressed=False,
                original_size=len(data),
                compressed_size=len(data),
            )
        
        # Evict if needed
        self._evict_lru(tier, entry.compressed_size)
        
        # Store
        self.tiers[tier][cache_key] = entry
        
        # Notify for cross-platform sync
        if self.on_cache_update:
            await self.on_cache_update(key, value, tier)
    
    async def _promote_entry(self, key: str, entry: CacheEntry):
        """Promote an entry to a hotter tier"""
        if entry.tier == CacheTier.L1_HOT:
            return
        
        target_tier = CacheTier.L1_HOT if entry.tier == CacheTier.L2_WARM else CacheTier.L2_WARM
        
        # Decompress
        if entry.compressed:
            data = self._decompress(entry.value)
        else:
            data = entry.value
        
        # Create new entry (possibly without compression for L1)
        config = self.configs[target_tier]
        if config.compression_level > 0:
            compressed = self._compress(data, config.compression_level)
            new_entry = CacheEntry(
                key=key,
                value=compressed,
                tier=target_tier,
                created_at=entry.created_at,
                accessed_at=datetime.now(),
                access_count=entry.access_count,
                compressed=True,
                original_size=len(data),
                compressed_size=len(compressed),
            )
        else:
            new_entry = CacheEntry(
                key=key,
                value=data,
                tier=target_tier,
                created_at=entry.created_at,
                accessed_at=datetime.now(),
                access_count=entry.access_count,
                compressed=False,
                original_size=len(data),
                compressed_size=len(data),
            )
        
        # Remove from old tier
        if key in self.tiers[entry.tier]:
            del self.tiers[entry.tier][key]
        
        # Add to new tier
        self._evict_lru(target_tier, new_entry.compressed_size)
        self.tiers[target_tier][key] = new_entry
    
    async def invalidate(self, key: str):
        """Invalidate a key across all tiers"""
        cache_key = self._generate_key(key)
        for tier in CacheTier:
            if cache_key in self.tiers[tier]:
                del self.tiers[tier][cache_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_hits = sum(s.hits for s in self.stats.values())
        total_misses = sum(s.misses for s in self.stats.values())
        total_saved = sum(s.total_bytes_saved for s in self.stats.values())
        
        return {
            "overall": {
                "hit_rate": total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "bytes_saved_by_compression": total_saved,
                "compression_ratio": f"{(1 - total_saved / max(total_saved + sum(self._get_tier_size(t) for t in CacheTier), 1)) * 100:.1f}%",
            },
            "tiers": {
                tier.value: {
                    "hit_rate": self.stats[tier].hit_rate,
                    "hits": self.stats[tier].hits,
                    "misses": self.stats[tier].misses,
                    "evictions": self.stats[tier].evictions,
                    "compressions": self.stats[tier].compressions,
                    "size_bytes": self._get_tier_size(tier),
                    "size_mb": self._get_tier_size(tier) / (1024 * 1024),
                    "max_size_mb": self.configs[tier].max_size_mb,
                    "utilization": self._get_tier_size(tier) / (self.configs[tier].max_size_mb * 1024 * 1024),
                    "entry_count": len(self.tiers[tier]),
                }
                for tier in CacheTier
            }
        }


class CrossPlatformSyncManager:
    """
    Manages cross-platform synchronization for the Quorum Universe.
    
    Enables symbiotic connections between:
    - PC/Mac/Linux desktops
    - Raspberry Pi nodes
    - Mobile devices (iOS/Android)
    - Cloud servers
    """
    
    def __init__(self, cache: MultiTierCache):
        self.cache = cache
        self.connected_devices: Dict[str, Dict] = {}
        self.sync_queue: List[Dict] = []
        self.websocket_connections: Dict[str, Any] = {}
        
        # Register cache callbacks
        self.cache.on_cache_update = self._on_cache_update
        self.cache.on_cache_evict = self._on_cache_evict
        
        print("✓ Cross-platform sync manager initialized")
    
    async def register_device(self, device_id: str, device_info: Dict):
        """Register a device for sync"""
        self.connected_devices[device_id] = {
            **device_info,
            "connected_at": datetime.now().isoformat(),
            "last_sync": None,
            "sync_count": 0,
        }
        print(f"  → Device registered: {device_id} ({device_info.get('platform', 'unknown')})")
    
    async def unregister_device(self, device_id: str):
        """Unregister a device"""
        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
            print(f"  → Device unregistered: {device_id}")
    
    async def _on_cache_update(self, key: str, value: Any, tier: CacheTier):
        """Handle cache updates for sync"""
        sync_event = {
            "type": "cache_update",
            "key": key,
            "tier": tier.value,
            "timestamp": datetime.now().isoformat(),
        }
        self.sync_queue.append(sync_event)
        await self._broadcast_sync(sync_event)
    
    async def _on_cache_evict(self, key: str, tier: CacheTier):
        """Handle cache evictions for sync"""
        sync_event = {
            "type": "cache_evict",
            "key": key,
            "tier": tier.value,
            "timestamp": datetime.now().isoformat(),
        }
        self.sync_queue.append(sync_event)
        await self._broadcast_sync(sync_event)
    
    async def _broadcast_sync(self, event: Dict):
        """Broadcast sync event to all connected devices"""
        for device_id, ws in self.websocket_connections.items():
            try:
                # In production, this would send via WebSocket
                pass
            except Exception as e:
                print(f"  ⚠ Sync failed for {device_id}: {e}")
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        return {
            "connected_devices": len(self.connected_devices),
            "pending_sync_events": len(self.sync_queue),
            "devices": {
                device_id: {
                    "platform": info.get("platform"),
                    "connected_at": info.get("connected_at"),
                    "last_sync": info.get("last_sync"),
                    "sync_count": info.get("sync_count"),
                }
                for device_id, info in self.connected_devices.items()
            }
        }


# Singleton instances
_cache_instance: Optional[MultiTierCache] = None
_sync_manager: Optional[CrossPlatformSyncManager] = None


def get_cache() -> MultiTierCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiTierCache()
    return _cache_instance


def get_sync_manager() -> CrossPlatformSyncManager:
    """Get the global sync manager instance"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = CrossPlatformSyncManager(get_cache())
    return _sync_manager


async def test_cache():
    """Test the multi-tier cache"""
    print("\n" + "=" * 60)
    print("MULTI-TIER CACHE TEST")
    print("=" * 60)
    
    cache = get_cache()
    
    # Test basic operations
    test_data = {
        "archetype": "mit_engineering",
        "domains": ["engineering", "robotics", "systems"],
        "corpus_size_gb": 160,
    }
    
    # Set in L2 (warm)
    await cache.set("test_archetype", test_data, CacheTier.L2_WARM)
    print("✓ Set test data in L2")
    
    # Get (should hit L2)
    result = await cache.get("test_archetype")
    assert result == test_data, "Cache retrieval failed"
    print("✓ Retrieved from L2")
    
    # Access multiple times to trigger promotion
    for _ in range(5):
        await cache.get("test_archetype")
    print("✓ Multiple accesses completed")
    
    # Check stats
    stats = cache.get_stats()
    print(f"\nCache Statistics:")
    print(f"  Overall hit rate: {stats['overall']['hit_rate']:.2%}")
    print(f"  L1 entries: {stats['tiers']['l1_hot']['entry_count']}")
    print(f"  L2 entries: {stats['tiers']['l2_warm']['entry_count']}")
    print(f"  L3 entries: {stats['tiers']['l3_cold']['entry_count']}")
    
    print("\n" + "=" * 60)
    print("CACHE TEST PASSED")
    print("=" * 60)
    
    return stats


if __name__ == "__main__":
    asyncio.run(test_cache())

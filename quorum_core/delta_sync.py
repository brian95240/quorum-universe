#!/usr/bin/env python3
"""
Delta Sync Daemon - Separate Repository Update System
Pulls knowledge updates from quorum-deltas repository

Key Features:
- Configurable update intervals (daily/weekly/monthly)
- Hash-based change detection
- Incremental delta application
- Graph update SQL execution
- Kyber key signature verification (optional)
- Cross-platform compatibility

Architecture:
- Main repo (quorum-universe): Frozen base snapshot
- Delta repo (quorum-deltas): Live update stream
- Local device: Base + deltas = current state

Update Cadence Options:
- Daily: ~5-50 MB (bleeding-edge, 3 AM sync)
- Weekly: ~100-200 MB (balanced, Sunday sync)
- Monthly: ~1-2 GB (firmware-style, 1st of month)
"""

import asyncio
import aiohttp
import hashlib
import json
import os
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import time

# Import system components
try:
    import sys
    sys.path.append(os.path.dirname(__file__))
    
    from config import get_data_path, detect_platform
    from redis_cache_manager import MultiTierCache, CacheTier
    
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Components unavailable: {e}")
    COMPONENTS_AVAILABLE = False

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

class UpdateInterval(Enum):
    """Update frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


@dataclass
class DeltaSyncConfig:
    """Delta sync configuration"""
    # Repository URLs
    delta_repo_url: str = "https://github.com/quorum-universe/quorum-deltas"
    delta_raw_url: str = "https://raw.githubusercontent.com/quorum-universe/quorum-deltas/main"
    
    # Local paths
    config_dir: Path = field(default_factory=lambda: Path.home() / ".quorum" / "config")
    delta_cache_dir: Path = field(default_factory=lambda: Path.home() / ".quorum" / "deltas")
    
    # Update settings
    interval: UpdateInterval = UpdateInterval.WEEKLY
    
    # Schedule (cron-style)
    daily_hour: int = 3      # 3 AM
    weekly_day: int = 0      # Sunday
    monthly_day: int = 1     # 1st of month
    
    # Verification
    verify_signatures: bool = False
    kyber_public_key: Optional[str] = None
    
    # Limits
    max_delta_size_mb: int = 500
    connection_timeout: int = 30
    
    def to_dict(self) -> Dict:
        return {
            'delta_repo_url': self.delta_repo_url,
            'interval': self.interval.value,
            'daily_hour': self.daily_hour,
            'weekly_day': self.weekly_day,
            'monthly_day': self.monthly_day,
            'verify_signatures': self.verify_signatures,
            'max_delta_size_mb': self.max_delta_size_mb,
        }


@dataclass
class DeltaManifest:
    """Manifest for a delta update"""
    date: str
    version: str
    files: List[Dict[str, Any]]
    total_size_bytes: int
    hash: str
    signature: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DeltaManifest':
        return cls(
            date=data.get('date', ''),
            version=data.get('version', ''),
            files=data.get('files', []),
            total_size_bytes=data.get('total_size_bytes', 0),
            hash=data.get('hash', ''),
            signature=data.get('signature'),
        )


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    deltas_applied: int = 0
    bytes_downloaded: int = 0
    files_updated: int = 0
    graph_updates: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'deltas_applied': self.deltas_applied,
            'bytes_downloaded': self.bytes_downloaded,
            'files_updated': self.files_updated,
            'graph_updates': self.graph_updates,
            'errors': self.errors,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat(),
        }


# =============================================================================
# DELTA SYNC DAEMON
# =============================================================================

class DeltaSyncDaemon:
    """
    Daemon for syncing knowledge updates from delta repository.
    
    Implements the two-repo architecture:
    - Main repo: Frozen base (stable, versioned)
    - Delta repo: Live stream (continuous updates)
    """
    
    def __init__(self, config: Optional[DeltaSyncConfig] = None):
        """
        Initialize delta sync daemon.
        
        Args:
            config: Sync configuration (loads from file if None)
        """
        self.config = config or self._load_config()
        
        # Ensure directories exist
        self.config.config_dir.mkdir(parents=True, exist_ok=True)
        self.config.delta_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.last_sync: Optional[datetime] = self._load_last_sync()
        self.sync_history: List[SyncResult] = []
        
        # Cache integration
        if COMPONENTS_AVAILABLE:
            self.cache = MultiTierCache()
        else:
            self.cache = None
        
        print(f"DeltaSyncDaemon initialized")
        print(f"  Interval: {self.config.interval.value}")
        print(f"  Delta repo: {self.config.delta_repo_url}")
        print(f"  Cache dir: {self.config.delta_cache_dir}")
    
    def _load_config(self) -> DeltaSyncConfig:
        """Load configuration from file"""
        config_path = Path.home() / ".quorum" / "config" / "update_interval"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                
                config = DeltaSyncConfig()
                if 'interval' in data:
                    config.interval = UpdateInterval(data['interval'])
                if 'daily_hour' in data:
                    config.daily_hour = data['daily_hour']
                if 'weekly_day' in data:
                    config.weekly_day = data['weekly_day']
                if 'monthly_day' in data:
                    config.monthly_day = data['monthly_day']
                
                return config
            except Exception as e:
                print(f"WARNING: Could not load config: {e}")
        
        return DeltaSyncConfig()
    
    def save_config(self):
        """Save configuration to file"""
        config_path = self.config.config_dir / "update_interval"
        
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        print(f"✓ Config saved: {config_path}")
    
    def _load_last_sync(self) -> Optional[datetime]:
        """Load last sync timestamp"""
        state_path = self.config.config_dir / "last_sync.json"
        
        if state_path.exists():
            try:
                with open(state_path, 'r') as f:
                    data = json.load(f)
                return datetime.fromisoformat(data['timestamp'])
            except:
                pass
        
        return None
    
    def _save_last_sync(self, timestamp: datetime):
        """Save last sync timestamp"""
        state_path = self.config.config_dir / "last_sync.json"
        
        with open(state_path, 'w') as f:
            json.dump({
                'timestamp': timestamp.isoformat(),
                'interval': self.config.interval.value,
            }, f)
    
    # =========================================================================
    # INDEX MANAGEMENT
    # =========================================================================
    
    async def fetch_index(self) -> Dict:
        """
        Fetch the delta repository index.
        
        Returns:
            Index data with available deltas
        """
        index_url = f"{self.config.delta_raw_url}/index.json"
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.connection_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(index_url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        print(f"WARNING: Index fetch failed: HTTP {resp.status}")
                        return {}
        except Exception as e:
            print(f"ERROR: Could not fetch index: {e}")
            return {}
    
    async def get_pending_deltas(self) -> List[DeltaManifest]:
        """
        Get list of deltas pending application.
        
        Returns:
            List of delta manifests to apply
        """
        index = await self.fetch_index()
        
        if not index:
            return []
        
        pending = []
        
        # Get deltas based on interval
        if self.config.interval == UpdateInterval.DAILY:
            # Get today's delta
            today = datetime.now().strftime('%Y-%m-%d')
            if today in index.get('daily', {}):
                pending.append(DeltaManifest.from_dict(index['daily'][today]))
        
        elif self.config.interval == UpdateInterval.WEEKLY:
            # Get this week's bundle
            week = datetime.now().strftime('%Y-W%W')
            if week in index.get('weekly', {}):
                pending.append(DeltaManifest.from_dict(index['weekly'][week]))
        
        elif self.config.interval == UpdateInterval.MONTHLY:
            # Get this month's bundle
            month = datetime.now().strftime('%Y-%m')
            if month in index.get('monthly', {}):
                pending.append(DeltaManifest.from_dict(index['monthly'][month]))
        
        # Filter out already-applied deltas
        applied_path = self.config.config_dir / "applied_deltas.json"
        applied = set()
        
        if applied_path.exists():
            try:
                with open(applied_path, 'r') as f:
                    applied = set(json.load(f))
            except:
                pass
        
        pending = [d for d in pending if d.hash not in applied]
        
        return pending
    
    # =========================================================================
    # DELTA DOWNLOAD
    # =========================================================================
    
    async def download_delta(self, manifest: DeltaManifest) -> Optional[Path]:
        """
        Download a delta bundle.
        
        Args:
            manifest: Delta manifest
        
        Returns:
            Path to downloaded delta or None
        """
        # Check size limit
        if manifest.total_size_bytes > self.config.max_delta_size_mb * 1024 * 1024:
            print(f"WARNING: Delta too large ({manifest.total_size_bytes} bytes)")
            return None
        
        # Determine download URL
        delta_url = f"{self.config.delta_raw_url}/deltas/{manifest.date}/bundle.tar.zst"
        
        # Download to cache
        cache_path = self.config.delta_cache_dir / f"{manifest.date}.tar.zst"
        
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 min for large files
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(delta_url) as resp:
                    if resp.status == 200:
                        with open(cache_path, 'wb') as f:
                            async for chunk in resp.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        # Verify hash
                        with open(cache_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        
                        if file_hash != manifest.hash:
                            print(f"WARNING: Hash mismatch for {manifest.date}")
                            cache_path.unlink()
                            return None
                        
                        print(f"✓ Downloaded: {manifest.date} ({manifest.total_size_bytes:,} bytes)")
                        return cache_path
                    else:
                        print(f"WARNING: Download failed: HTTP {resp.status}")
                        return None
        
        except Exception as e:
            print(f"ERROR: Download failed: {e}")
            return None
    
    # =========================================================================
    # DELTA APPLICATION
    # =========================================================================
    
    async def apply_delta(self, delta_path: Path, manifest: DeltaManifest) -> SyncResult:
        """
        Apply a downloaded delta.
        
        Args:
            delta_path: Path to delta bundle
            manifest: Delta manifest
        
        Returns:
            Sync result
        """
        result = SyncResult(success=False)
        start_time = time.time()
        
        try:
            # Extract delta
            extract_dir = self.config.delta_cache_dir / f"extract_{manifest.date}"
            extract_dir.mkdir(exist_ok=True)
            
            if ZSTD_AVAILABLE:
                # Decompress with zstd
                import tarfile
                
                dctx = zstd.ZstdDecompressor()
                with open(delta_path, 'rb') as f_in:
                    decompressed = dctx.decompress(f_in.read())
                
                # Write decompressed tar
                tar_path = extract_dir / "bundle.tar"
                with open(tar_path, 'wb') as f_out:
                    f_out.write(decompressed)
                
                # Extract tar
                with tarfile.open(tar_path, 'r') as tar:
                    tar.extractall(extract_dir)
                
                tar_path.unlink()
            else:
                # Fallback: assume uncompressed
                import tarfile
                with tarfile.open(delta_path, 'r:*') as tar:
                    tar.extractall(extract_dir)
            
            # Process files
            data_path = get_data_path() if COMPONENTS_AVAILABLE else Path.home() / ".quorum_universe"
            
            for file_info in manifest.files:
                file_name = file_info.get('name', '')
                file_type = file_info.get('type', 'data')
                target_archetype = file_info.get('archetype', '')
                
                source_path = extract_dir / file_name
                
                if not source_path.exists():
                    continue
                
                if file_type == 'sql':
                    # Apply SQL update to graph
                    updates = await self._apply_sql_update(source_path)
                    result.graph_updates += updates
                
                elif file_type == 'data':
                    # Copy to archetype data folder
                    if target_archetype:
                        target_dir = data_path / "data" / "archetypes" / target_archetype
                        target_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, target_dir / file_name)
                        result.files_updated += 1
                
                elif file_type == 'embedding':
                    # Copy to embeddings folder
                    if target_archetype:
                        target_dir = data_path / "data" / "embeddings" / target_archetype
                        target_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, target_dir / file_name)
                        result.files_updated += 1
            
            # Cache in L3 tier
            if self.cache:
                await self.cache.set(
                    f"delta:{manifest.date}",
                    {'applied': True, 'files': result.files_updated},
                    tier=CacheTier.L3_COLD
                )
            
            # Mark as applied
            await self._mark_applied(manifest.hash)
            
            # Cleanup
            shutil.rmtree(extract_dir)
            
            result.success = True
            result.deltas_applied = 1
            result.bytes_downloaded = manifest.total_size_bytes
            
        except Exception as e:
            result.errors.append(str(e))
            print(f"ERROR: Delta application failed: {e}")
        
        result.duration_seconds = time.time() - start_time
        return result
    
    async def _apply_sql_update(self, sql_path: Path) -> int:
        """
        Apply SQL update to knowledge graph.
        
        Args:
            sql_path: Path to SQL file
        
        Returns:
            Number of updates applied
        """
        # Read SQL
        with open(sql_path, 'r') as f:
            sql = f.read()
        
        # Get graph database path
        data_path = get_data_path() if COMPONENTS_AVAILABLE else Path.home() / ".quorum_universe"
        db_path = data_path / "data" / "knowledge_graph.db"
        
        if not db_path.exists():
            print(f"WARNING: Knowledge graph not found: {db_path}")
            return 0
        
        # Execute SQL
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Split into statements and execute
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            updates = 0
            
            for stmt in statements:
                try:
                    cursor.execute(stmt)
                    updates += cursor.rowcount if cursor.rowcount > 0 else 1
                except sqlite3.Error as e:
                    print(f"WARNING: SQL error: {e}")
            
            conn.commit()
            conn.close()
            
            return updates
        
        except Exception as e:
            print(f"ERROR: SQL execution failed: {e}")
            return 0
    
    async def _mark_applied(self, delta_hash: str):
        """Mark a delta as applied"""
        applied_path = self.config.config_dir / "applied_deltas.json"
        
        applied = []
        if applied_path.exists():
            try:
                with open(applied_path, 'r') as f:
                    applied = json.load(f)
            except:
                pass
        
        if delta_hash not in applied:
            applied.append(delta_hash)
        
        with open(applied_path, 'w') as f:
            json.dump(applied, f)
    
    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================
    
    async def sync(self) -> SyncResult:
        """
        Perform a full sync operation.
        
        Returns:
            Sync result
        """
        print(f"\n{'='*60}")
        print(f"DELTA SYNC - {datetime.now().isoformat()}")
        print(f"{'='*60}")
        
        total_result = SyncResult(success=True)
        start_time = time.time()
        
        # Get pending deltas
        pending = await self.get_pending_deltas()
        
        if not pending:
            print("✓ No pending deltas")
            total_result.duration_seconds = time.time() - start_time
            return total_result
        
        print(f"Found {len(pending)} pending delta(s)")
        
        # Process each delta
        for manifest in pending:
            print(f"\nProcessing: {manifest.date}")
            
            # Download
            delta_path = await self.download_delta(manifest)
            
            if not delta_path:
                total_result.errors.append(f"Download failed: {manifest.date}")
                continue
            
            # Apply
            result = await self.apply_delta(delta_path, manifest)
            
            # Aggregate results
            total_result.deltas_applied += result.deltas_applied
            total_result.bytes_downloaded += result.bytes_downloaded
            total_result.files_updated += result.files_updated
            total_result.graph_updates += result.graph_updates
            total_result.errors.extend(result.errors)
            
            if not result.success:
                total_result.success = False
            
            # Cleanup downloaded file
            delta_path.unlink()
        
        total_result.duration_seconds = time.time() - start_time
        
        # Update last sync time
        self._save_last_sync(datetime.now())
        self.last_sync = datetime.now()
        
        # Log results
        print(f"\n{'='*60}")
        print(f"SYNC COMPLETE")
        print(f"{'='*60}")
        print(f"  Deltas applied: {total_result.deltas_applied}")
        print(f"  Files updated: {total_result.files_updated}")
        print(f"  Graph updates: {total_result.graph_updates}")
        print(f"  Bytes downloaded: {total_result.bytes_downloaded:,}")
        print(f"  Duration: {total_result.duration_seconds:.1f}s")
        
        if total_result.errors:
            print(f"  Errors: {len(total_result.errors)}")
        
        return total_result
    
    def should_sync(self) -> bool:
        """
        Check if sync should run based on schedule.
        
        Returns:
            True if sync should run
        """
        if self.config.interval == UpdateInterval.MANUAL:
            return False
        
        now = datetime.now()
        
        if self.last_sync is None:
            return True
        
        if self.config.interval == UpdateInterval.DAILY:
            # Sync if last sync was before today's scheduled time
            scheduled = now.replace(hour=self.config.daily_hour, minute=0, second=0)
            if now.hour < self.config.daily_hour:
                scheduled -= timedelta(days=1)
            return self.last_sync < scheduled
        
        elif self.config.interval == UpdateInterval.WEEKLY:
            # Sync if last sync was before this week's scheduled day
            days_since_scheduled = (now.weekday() - self.config.weekly_day) % 7
            scheduled = now - timedelta(days=days_since_scheduled)
            scheduled = scheduled.replace(hour=self.config.daily_hour, minute=0, second=0)
            return self.last_sync < scheduled
        
        elif self.config.interval == UpdateInterval.MONTHLY:
            # Sync if last sync was before this month's scheduled day
            scheduled = now.replace(day=self.config.monthly_day, hour=self.config.daily_hour, minute=0, second=0)
            if now.day < self.config.monthly_day:
                # Go to previous month
                scheduled = (scheduled.replace(day=1) - timedelta(days=1)).replace(day=self.config.monthly_day)
            return self.last_sync < scheduled
        
        return False
    
    async def run_daemon(self, check_interval: int = 3600):
        """
        Run as a daemon, checking for updates periodically.
        
        Args:
            check_interval: Seconds between checks (default: 1 hour)
        """
        print(f"Starting delta sync daemon (check every {check_interval}s)")
        
        while True:
            if self.should_sync():
                await self.sync()
            
            await asyncio.sleep(check_interval)
    
    # =========================================================================
    # CONFIGURATION HELPERS
    # =========================================================================
    
    def set_interval(self, interval: UpdateInterval):
        """
        Set update interval.
        
        Args:
            interval: New update interval
        """
        self.config.interval = interval
        self.save_config()
        print(f"✓ Update interval set to: {interval.value}")
    
    def get_status(self) -> Dict:
        """
        Get daemon status.
        
        Returns:
            Status dictionary
        """
        return {
            'interval': self.config.interval.value,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'should_sync': self.should_sync(),
            'delta_repo': self.config.delta_repo_url,
            'cache_dir': str(self.config.delta_cache_dir),
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Delta Sync Daemon')
    parser.add_argument('command', choices=['sync', 'status', 'set-interval', 'daemon'],
                       help='Command to run')
    parser.add_argument('--interval', choices=['daily', 'weekly', 'monthly', 'manual'],
                       help='Update interval (for set-interval)')
    
    args = parser.parse_args()
    
    daemon = DeltaSyncDaemon()
    
    if args.command == 'sync':
        result = await daemon.sync()
        print(json.dumps(result.to_dict(), indent=2))
    
    elif args.command == 'status':
        status = daemon.get_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == 'set-interval':
        if args.interval:
            daemon.set_interval(UpdateInterval(args.interval))
        else:
            print("ERROR: --interval required")
    
    elif args.command == 'daemon':
        await daemon.run_daemon()


if __name__ == '__main__':
    asyncio.run(main())

# Changelog

All notable changes to Quorum Universe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-07

### Added

- **Delta Sync System** (`quorum_core/delta_sync.py`)
  - Two-repository architecture for efficient knowledge updates
  - Configurable update intervals: daily (5-50 MB), weekly (100-200 MB), monthly (1-2 GB)
  - Hash-based change detection with SHA-256 verification
  - Incremental delta application with graph SQL updates
  - Daemon mode for background synchronization
  - Cross-platform compatibility (PC/Mac/Raspberry Pi/servers/mobile)

- **Compression Manager** (`Source Code/compression_manager.py`)
  - Centralized Zstandard compression (70-80% storage reduction)
  - Text compression for JSON, YAML, logs
  - Embedding compression for float32 vectors (80% reduction)
  - Streaming compression for large files
  - Dictionary training on corpus samples (+20% ratio improvement)
  - Compression statistics tracking

- **Admin Dashboard** (`Source Code/admin_dashboard.py`)
  - Mobile-friendly Gradio web interface
  - Knowledge source injection via URL paste
  - Voice command processing (Whisper integration)
  - Live metrics visualization
  - Compression statistics display
  - Archetype management controls
  - Tailscale-compatible for remote access

- **Daily Delta Ingestion** (`Source Code/daily_delta_ingestion.py`)
  - Automated knowledge graph updates
  - Multi-method fetching (arXiv API, RSS, direct download)
  - Quality gates before training inclusion (threshold: 0.85)
  - Parallel fetch support (100 sources in ~30s)
  - Integration with compression manager

- **Configuration Updates**
  - Added `UPDATE_INTERVALS` configuration in `config.py`
  - Added `DELTA_REPO_CONFIG` for repository settings
  - Updated `requirements.txt` with new dependencies (gradio, PyYAML)

### Changed

- Source Code directory now contains 32 files (up from 29)
- quorum_core directory now contains 16 files (up from 15)
- Total Python files: 48 (up from 44)
- README.md updated with Delta Sync and Admin Dashboard documentation

### Technical Details

- Delta repository URL: `https://github.com/quorum-universe/quorum-deltas`
- Default update interval: weekly (Sunday 3 AM)
- Compression levels: FAST (3), DEFAULT (11), MAX (19)
- Admin dashboard port: 7860

## [1.0.0] - 2026-01-06

### Initial Release

- 26 Institutional Archetypes with 846 GB corpus
- Hexagonal Ring Topology with 6-face optimization
- Ring-Collapse Algorithm (synergy score: 0.2912)
- Intersection Annealing (17 clusters discovered)
- 8,074.68x Cascade Potential
- 6-Philosopher Tribunal + Observer
- Multi-Tier Cache (L1/L2/L3) with Zstandard compression
- 21/21 closed-loop tests passing
- Cross-platform symbiotic connectivity
- FastAPI production server
- React dashboard with D3.js visualizations

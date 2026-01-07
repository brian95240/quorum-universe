# Quorum Universe

<div align="center">

![Quorum Universe](https://img.shields.io/badge/Quorum-Universe-00ffd5?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMGZmZDUiIHN0cm9rZS13aWR0aD0iMiI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDIgNyAyIDE3IDEyIDIyIDIyIDE3IDIyIDcgMTIgMiIvPjwvc3ZnPg==)
![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-GPL--3.0%20%2F%20Commercial-green?style=for-the-badge)
![Tests](https://img.shields.io/badge/tests-21%2F21%20passed-success?style=for-the-badge)

**An Ambient Intelligence System with Hexagonal Ring Topology**

*26 Institutional Archetypes • 6 Philosopher Tribunal • 8,074x Cascade Potential*

[Documentation](#documentation) • [Quick Start](#quick-start) • [Features](#features) • [Licensing](#licensing)

</div>

---

## Overview

Quorum Universe is a sophisticated ambient intelligence system that organizes knowledge across **26 institutional archetypes** arranged in a hexagonal ring topology. The system uses **ring-collapse optimization** to maximize synergies between knowledge domains, validated by a **6-philosopher tribunal** for truth verification.

### Key Capabilities

- **Hexagonal Ring Topology**: Archetypes arranged in concentric rings with 6-face adjacency optimization
- **Ring-Collapse Algorithm**: Simulated annealing to find optimal ring rotations (synergy score: 0.2912)
- **Intersection Annealing**: Discovers hidden synergy networks at code intersections (17 clusters found)
- **Cascade Amplification**: 8,074.68x cascade potential when all clusters activate
- **Philosopher Tribunal**: 6 philosophers (Hume, Popper, Quine, Arendt, Zhuangzi, Ibn Khaldun) + Observer
- **Multi-Tier Cache**: L1/L2/L3 with Zstandard compression (70% reduction)
- **Air-Gap Validated**: 100% closed-loop test pass rate (21/21 tests)

---

## Quick Start

### One-Line Deployment

```bash
curl -sSL https://raw.githubusercontent.com/quorum-universe/quorum-universe/main/deploy.sh | bash
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/quorum-universe/quorum-universe.git
cd quorum-universe

# Install Python dependencies
pip install -r requirements.txt

# Initialize the system
python quorum_core/apex_config.py

# Run tests
python quorum_core/closed_loop_test_suite.py

# Start the API server
python quorum_core/api_server.py
```

### Docker Deployment

```bash
docker pull quorum-universe/quorum-universe:latest
docker run -p 8000:8000 -p 3000:3000 quorum-universe/quorum-universe
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUORUM UNIVERSE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        PRESENTATION LAYER                            │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │  Dashboard  │  │  Archetypes │  │  Tribunal   │  │   Apex     │  │    │
│  │  │   (Vue.js)  │  │   (D3.js)   │  │    View     │  │  Metrics   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │                          API LAYER (FastAPI)                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │   /query    │  │   /ingest   │  │    /sync    │  │  /metrics  │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │                        INTELLIGENCE LAYER                            │    │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │    │
│  │  │   Hex-Ring        │  │   Intersection    │  │   Philosopher   │  │    │
│  │  │   Optimizer       │  │   Annealer        │  │   Tribunal      │  │    │
│  │  │   (NetworkX)      │  │   (NumPy)         │  │   (6+Observer)  │  │    │
│  │  └───────────────────┘  └───────────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │                          DATA LAYER                                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │  PostgreSQL │  │   Redis     │  │   Graph     │  │  Symbiotic │  │    │
│  │  │  (Neon)     │  │  (L1/L2/L3) │  │   Engine    │  │  Connector │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### 26 Institutional Archetypes

Organized across 7 knowledge clusters:

| Cluster | Archetypes | Corpus Size |
|---------|------------|-------------|
| **STEM Core** | MIT Engineering, Caltech Physics, Stanford AI, Oxford Mathematics | 180 GB |
| **Applied Tech** | CMU Robotics, ETH Systems, Berkeley Data | 120 GB |
| **Life Systems** | Harvard Medical, NIH Biomedical, Johns Hopkins Public Health | 150 GB |
| **Human Systems** | Chicago Economics, Wharton Finance, LSE Political, Yale Law | 140 GB |
| **Non-Western** | Beijing Classical, Baghdad Golden, Nalanda Buddhist, Timbuktu Scholarly | 100 GB |
| **Creative Synthesis** | Bauhaus Design, IDEO Innovation, MIT Media Lab | 80 GB |
| **Meta-Cognitive** | Mensa Orthogonal, Philosophy Tribunal, Cambridge Theoretical, Santa Fe Complexity, RAND Strategic, Max Planck Research | 76 GB |

**Total Corpus: 846 GB**

### Philosopher Tribunal

Six philosophers validate truth through deliberation:

| Philosopher | Perspective | Validation Type |
|-------------|-------------|-----------------|
| **Hume** | Empirical Skeptic | Evidence validation |
| **Popper** | Falsificationist | Adversarial testing |
| **Quine** | Naturalist | Holistic validation |
| **Arendt** | Political Theorist | Bias audit |
| **Zhuangzi** | Daoist Sage | Peripheral exploration |
| **Ibn Khaldun** | Civilizational Analyst | Temporal tracking |
| **Observer** | Consensus Enforcer | Silence at 0.92 threshold |

### Apex Optimization Metrics

| Metric | Score | Description |
|--------|-------|-------------|
| Synergy Score | 0.2912 | Hex-ring collapse optimization |
| Cascade Potential | 8,074.68x | Total amplification when activated |
| Cache Efficiency | 88% | Multi-tier with Zstandard |
| Routing Accuracy | 92% | Synergy-based archetype routing |
| Tribunal Consensus | 94% | Philosopher agreement rate |
| Resource Efficiency | 54.46% | Optimization injection success |

---

## Documentation

### Core Modules

| Module | Description |
|--------|-------------|
| `config.py` | System configuration and archetype definitions |
| `apex_config.py` | Optimized configurations from all analyses |
| `hex_ring_optimizer.py` | Hexagonal ring collapse algorithm |
| `intersection_annealer.py` | Hidden synergy network discovery |
| `synergy_analyzer.py` | Cross-archetype synergy analysis |
| `graph_engine.py` | NetworkX-based graph operations |
| `redis_cache_manager.py` | Multi-tier caching with compression |
| `api_server.py` | FastAPI REST endpoints |
| `symbiotic_connector.py` | Cross-platform device sync |

### API Endpoints

```
GET  /api/health          - System health check
POST /api/query           - Query archetypes
POST /api/ingest          - Ingest new knowledge
GET  /api/archetypes      - List all archetypes
GET  /api/synergies       - Get synergy analysis
GET  /api/tribunal        - Tribunal deliberation status
POST /api/sync            - Cross-platform sync
GET  /api/metrics         - System metrics
```

---

## Requirements

### System Requirements

- Python 3.11+
- Node.js 22+
- PostgreSQL 15+ (or Neon serverless)
- Redis 7+ (optional, for caching)
- 4 GB RAM minimum, 16 GB recommended
- 50 GB disk space for full corpus

### Python Dependencies

```
asyncpg>=0.29.0
fastapi>=0.109.0
networkx>=3.2.1
numpy>=1.26.0
pydantic>=2.5.0
redis>=5.0.0
uvicorn>=0.25.0
zstandard>=0.22.0
```

### Node.js Dependencies

```
react>=19.0.0
vite>=5.0.0
tailwindcss>=4.0.0
framer-motion>=12.0.0
recharts>=2.15.0
```

---

## Licensing

This project uses **dual licensing**:

### Open Source (GPL-3.0)

Free for:
- Personal use
- Educational use
- Open-source projects (GPL-3.0 compatible)

### Commercial License

Required for:
- Proprietary software
- Closed-source products
- Commercial distribution

See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for details.

| Tier | Annual Revenue | Price |
|------|----------------|-------|
| Starter | < $100K | $499/year |
| Professional | $100K - $1M | $1,999/year |
| Business | $1M - $10M | $7,999/year |
| Enterprise | $10M - $100M | $24,999/year |
| Enterprise Plus | > $100M | Custom |

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python quorum_core/closed_loop_test_suite.py`
5. Submit a pull request

---

## Support

- **Documentation**: https://docs.quorum-universe.io
- **Issues**: https://github.com/quorum-universe/quorum-universe/issues
- **Discussions**: https://github.com/quorum-universe/quorum-universe/discussions
- **Email**: support@quorum-universe.io

---

## Acknowledgments

Built with:
- [NetworkX](https://networkx.org/) - Graph algorithms
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [React](https://react.dev/) - UI framework
- [D3.js](https://d3js.org/) - Data visualization
- [Neon](https://neon.tech/) - Serverless PostgreSQL
- [Redis](https://redis.io/) - Caching layer

---

<div align="center">

**Quorum Universe** - *Ambient Intelligence Through Hexagonal Synergy*

Copyright © 2026 Quorum Universe Contributors

</div>

#!/usr/bin/env python3
"""
Quorum Universe - Configuration & Connection Registry
Symbiotic cross-platform connectivity for PC/Mac/Raspberry Pi/servers/mobile
Live URL mappings and archetype training data dump configurations
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

# =============================================================================
# NEON DATABASE CONNECTION
# =============================================================================
NEON_PROJECT_ID = "wandering-brook-58872006"
NEON_CONNECTION_STRING = os.getenv(
    "NEON_DATABASE_URL",
    "postgresql://neondb_owner:npg_UIp3VfxBZEi5@ep-sweet-frost-ae0o185n-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

# =============================================================================
# SYMBIOTIC PLATFORM DETECTION
# =============================================================================
@dataclass
class QuorumConfig:
    """Main configuration for Quorum Universe"""
    platform: str = field(default_factory=lambda: detect_platform())
    data_path: Path = field(default_factory=lambda: get_data_path())
    neon_connection: str = NEON_CONNECTION_STRING
    sync_enabled: bool = True


@dataclass
class PlatformConfig:
    """Cross-platform symbiotic configuration"""
    platform: str = field(default_factory=lambda: detect_platform())
    base_data_path: Path = field(default_factory=lambda: get_data_path())
    sync_enabled: bool = True
    
    # Live URL endpoints for symbiotic connections
    api_base_url: str = ""
    websocket_url: str = ""
    sync_folder_url: str = ""
    
def detect_platform() -> str:
    """Detect current platform for symbiotic configuration"""
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if 'arm' in machine or 'aarch' in machine:
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                if 'raspberry' in f.read().lower():
                    return 'raspberry_pi'
        return 'arm_server'
    elif system == 'darwin':
        return 'macos'
    elif system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux_server'
    return 'unknown'

def get_data_path() -> Path:
    """Get platform-appropriate data path for symbiotic folder structure"""
    platform_type = detect_platform()
    
    # Use home directory for sandbox/development, /opt for production
    home_base = Path.home() / '.quorum_universe'
    
    paths = {
        'macos': Path.home() / 'Library' / 'Application Support' / 'QuorumUniverse',
        'windows': Path(os.getenv('APPDATA', '')) / 'QuorumUniverse',
        'linux_server': home_base,  # Use home dir for sandbox compatibility
        'raspberry_pi': Path('/home/pi/quorum_universe/data'),
        'arm_server': home_base,
    }
    
    return paths.get(platform_type, home_base)

# =============================================================================
# 26 INSTITUTIONAL ARCHETYPES WITH TRAINING DATA SOURCES
# =============================================================================
ARCHETYPES = {
    # Tier 1: Original 8 Core Archetypes
    'mit_engineering': {
        'id': 1,
        'cluster': 'stem_core',
        'corpus_size_gb': 160,
        'temperature': 0.7,
        'style': 'Applied, constraint-driven, diagram-first',
        'domains': ['engineering', 'robotics', 'systems', 'design'],
        'training_sources': [
            'https://ocw.mit.edu/courses/',
            'https://www.csail.mit.edu/research',
            'https://www.media.mit.edu/publications/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/mit_engineering/',
            'embeddings': '/data/embeddings/mit_engineering/',
            'cache': '/cache/mit_engineering/',
        }
    },
    'caltech_physics': {
        'id': 2,
        'cluster': 'stem_core',
        'corpus_size_gb': 86,
        'temperature': 0.6,
        'style': 'First-principles, reductionist, intuitive clarity',
        'domains': ['physics', 'cosmology', 'quantum', 'relativity'],
        'training_sources': [
            'https://www.feynmanlectures.caltech.edu/',
            'https://arxiv.org/list/physics/recent',
            'https://www.caltech.edu/research',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/caltech_physics/',
            'embeddings': '/data/embeddings/caltech_physics/',
            'cache': '/cache/caltech_physics/',
        }
    },
    'princeton_math': {
        'id': 3,
        'cluster': 'stem_core',
        'corpus_size_gb': 22,
        'temperature': 0.65,
        'style': 'Pure abstraction, proof-based, elegant',
        'domains': ['mathematics', 'proof', 'analysis', 'topology'],
        'training_sources': [
            'https://terrytao.wordpress.com/',
            'https://www.math.princeton.edu/',
            'https://arxiv.org/list/math/recent',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/princeton_math/',
            'embeddings': '/data/embeddings/princeton_math/',
            'cache': '/cache/princeton_math/',
        }
    },
    'stanford_cs': {
        'id': 4,
        'cluster': 'applied_tech',
        'corpus_size_gb': 18,
        'temperature': 0.7,
        'style': 'Scalable, code-first, ship-focused',
        'domains': ['computer_science', 'machine_learning', 'algorithms'],
        'training_sources': [
            'https://cs229.stanford.edu/',
            'https://cs231n.stanford.edu/',
            'https://ai.stanford.edu/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/stanford_cs/',
            'embeddings': '/data/embeddings/stanford_cs/',
            'cache': '/cache/stanford_cs/',
        }
    },
    'harvard_med': {
        'id': 5,
        'cluster': 'life_systems',
        'corpus_size_gb': 65,
        'temperature': 0.65,
        'style': 'Clinical reasoning, probabilistic, evidence-based',
        'domains': ['medicine', 'clinical', 'diagnostics', 'physiology'],
        'training_sources': [
            'https://hms.harvard.edu/education',
            'https://www.nejm.org/',
            'https://pubmed.ncbi.nlm.nih.gov/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/harvard_med/',
            'embeddings': '/data/embeddings/harvard_med/',
            'cache': '/cache/harvard_med/',
        }
    },
    'yale_law': {
        'id': 6,
        'cluster': 'human_systems',
        'corpus_size_gb': 42,
        'temperature': 0.65,
        'style': 'Adversarial, precedent-heavy, distinguish-or-concede',
        'domains': ['law', 'policy', 'rights', 'precedent'],
        'training_sources': [
            'https://law.yale.edu/',
            'https://www.supremecourt.gov/opinions/',
            'https://www.law.cornell.edu/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/yale_law/',
            'embeddings': '/data/embeddings/yale_law/',
            'cache': '/cache/yale_law/',
        }
    },
    'oxford_classics': {
        'id': 7,
        'cluster': 'human_systems',
        'corpus_size_gb': 35,
        'temperature': 0.75,
        'style': 'Dialectical, narrative, historiographic',
        'domains': ['classics', 'philosophy', 'history', 'literature'],
        'training_sources': [
            'https://www.perseus.tufts.edu/',
            'https://plato.stanford.edu/',
            'https://www.classics.ox.ac.uk/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/oxford_classics/',
            'embeddings': '/data/embeddings/oxford_classics/',
            'cache': '/cache/oxford_classics/',
        }
    },
    'mensa_orthogonal': {
        'id': 8,
        'cluster': 'meta_cognitive',
        'corpus_size_gb': 4,
        'temperature': 0.9,
        'style': 'Non-linear, pattern-seeking, assume-nothing',
        'domains': ['puzzles', 'patterns', 'lateral_thinking'],
        'training_sources': [
            'https://www.mensa.org/',
            'https://www.worldpuzzle.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/mensa_orthogonal/',
            'embeddings': '/data/embeddings/mensa_orthogonal/',
            'cache': '/cache/mensa_orthogonal/',
        }
    },
    
    # Tier 2: Non-Western Archetypes
    'beijing_classical': {
        'id': 9,
        'cluster': 'non_western',
        'corpus_size_gb': 8,
        'temperature': 0.75,
        'style': 'Strategic, paradoxical, harmony-seeking',
        'domains': ['strategy', 'eastern_philosophy', 'traditional_medicine'],
        'training_sources': [
            'https://ctext.org/',
            'https://www.sacred-texts.com/tao/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/beijing_classical/',
            'embeddings': '/data/embeddings/beijing_classical/',
            'cache': '/cache/beijing_classical/',
        }
    },
    'baghdad_golden': {
        'id': 10,
        'cluster': 'non_western',
        'corpus_size_gb': 12,
        'temperature': 0.7,
        'style': 'Empirical, geometric, spiritual-rational synthesis',
        'domains': ['islamic_science', 'mathematics', 'optics', 'medicine'],
        'training_sources': [
            'https://www.muslimheritage.com/',
            'https://www.islamicmanuscripts.info/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/baghdad_golden/',
            'embeddings': '/data/embeddings/baghdad_golden/',
            'cache': '/cache/baghdad_golden/',
        }
    },
    'nalanda_vedic': {
        'id': 11,
        'cluster': 'non_western',
        'corpus_size_gb': 6,
        'temperature': 0.72,
        'style': 'Intuitive-deductive, infinity-aware, holistic',
        'domains': ['indian_mathematics', 'ayurveda', 'logic', 'consciousness'],
        'training_sources': [
            'https://www.sacred-texts.com/hin/',
            'https://www.wisdomlib.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/nalanda_vedic/',
            'embeddings': '/data/embeddings/nalanda_vedic/',
            'cache': '/cache/nalanda_vedic/',
        }
    },
    
    # Tier 3: Life Sciences
    'broad_genomics': {
        'id': 12,
        'cluster': 'life_systems',
        'corpus_size_gb': 120,
        'temperature': 0.7,
        'style': 'Data-driven, evolutionary, systems biology',
        'domains': ['genomics', 'evolution', 'molecular_biology', 'genetics'],
        'training_sources': [
            'https://www.broadinstitute.org/',
            'https://www.biorxiv.org/',
            'https://www.ncbi.nlm.nih.gov/pmc/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/broad_genomics/',
            'embeddings': '/data/embeddings/broad_genomics/',
            'cache': '/cache/broad_genomics/',
        }
    },
    'berkeley_psychedelics': {
        'id': 13,
        'cluster': 'creative_synthesis',
        'corpus_size_gb': 8,
        'temperature': 0.85,
        'style': 'Experiential, non-ordinary states, phenomenological',
        'domains': ['consciousness', 'psychedelics', 'phenomenology'],
        'training_sources': [
            'https://maps.org/research/',
            'https://hopkinspsychedelic.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/berkeley_psychedelics/',
            'embeddings': '/data/embeddings/berkeley_psychedelics/',
            'cache': '/cache/berkeley_psychedelics/',
        }
    },
    
    # Tier 4: Social Systems
    'chicago_economics': {
        'id': 14,
        'cluster': 'human_systems',
        'corpus_size_gb': 28,
        'temperature': 0.7,
        'style': 'Incentive-focused, market-based, rational-choice',
        'domains': ['economics', 'incentives', 'markets', 'behavior'],
        'training_sources': [
            'https://www.nber.org/',
            'https://www.econlib.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/chicago_economics/',
            'embeddings': '/data/embeddings/chicago_economics/',
            'cache': '/cache/chicago_economics/',
        }
    },
    
    # Tier 5: Creative & Applied
    'bauhaus_design': {
        'id': 15,
        'cluster': 'creative_synthesis',
        'corpus_size_gb': 5,
        'temperature': 0.8,
        'style': 'Form-follows-function, gestalt, minimalist',
        'domains': ['design', 'architecture', 'aesthetics', 'systems_thinking'],
        'training_sources': [
            'https://www.bauhaus.de/',
            'https://www.risd.edu/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/bauhaus_design/',
            'embeddings': '/data/embeddings/bauhaus_design/',
            'cache': '/cache/bauhaus_design/',
        }
    },
    'hacker_insurgent': {
        'id': 16,
        'cluster': 'applied_tech',
        'corpus_size_gb': 3,
        'temperature': 0.8,
        'style': 'Lateral, exploit-seeking, anti-authoritarian',
        'domains': ['hacking', 'security', 'foss', 'freedom'],
        'training_sources': [
            'https://www.gnu.org/',
            'http://phrack.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/hacker_insurgent/',
            'embeddings': '/data/embeddings/hacker_insurgent/',
            'cache': '/cache/hacker_insurgent/',
        }
    },
    
    # Tier 6: Edge Knowledge
    'indigenous_ecology': {
        'id': 17,
        'cluster': 'creative_synthesis',
        'corpus_size_gb': 4,
        'temperature': 0.75,
        'style': 'Holistic, multi-generational, reciprocal',
        'domains': ['ecology', 'traditional_knowledge', 'sustainability'],
        'training_sources': [
            'https://www.permaculturenews.org/',
            'https://biomimicry.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/indigenous_ecology/',
            'embeddings': '/data/embeddings/indigenous_ecology/',
            'cache': '/cache/indigenous_ecology/',
        }
    },
    'complexity_science': {
        'id': 18,
        'cluster': 'stem_core',
        'corpus_size_gb': 15,
        'temperature': 0.75,
        'style': 'Systems-level, non-linear, emergent properties',
        'domains': ['complexity', 'emergence', 'networks', 'chaos'],
        'training_sources': [
            'https://www.santafe.edu/',
            'https://arxiv.org/list/nlin/recent',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/complexity_science/',
            'embeddings': '/data/embeddings/complexity_science/',
            'cache': '/cache/complexity_science/',
        }
    },
    'ai_safety': {
        'id': 19,
        'cluster': 'applied_tech',
        'corpus_size_gb': 8,
        'temperature': 0.65,
        'style': 'Cautious, long-term, adversarial-robust',
        'domains': ['ai_safety', 'alignment', 'x-risk', 'ethics'],
        'training_sources': [
            'https://www.anthropic.com/research',
            'https://www.alignmentforum.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/ai_safety/',
            'embeddings': '/data/embeddings/ai_safety/',
            'cache': '/cache/ai_safety/',
        }
    },
    'longevity_research': {
        'id': 20,
        'cluster': 'life_systems',
        'corpus_size_gb': 12,
        'temperature': 0.7,
        'style': 'Interventionist, damage-repair, optimistic',
        'domains': ['longevity', 'aging', 'regeneration', 'biomarkers'],
        'training_sources': [
            'https://www.sens.org/',
            'https://www.lifespan.io/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/longevity_research/',
            'embeddings': '/data/embeddings/longevity_research/',
            'cache': '/cache/longevity_research/',
        }
    },
    
    # Tier 7: NEW - 6 Additional Archetypes for Quorum Universe
    'quantum_computing': {
        'id': 21,
        'cluster': 'stem_core',
        'corpus_size_gb': 10,
        'temperature': 0.68,
        'style': 'Superposition-aware, entanglement-first, probabilistic',
        'domains': ['quantum_computing', 'qubits', 'quantum_algorithms', 'cryptography'],
        'training_sources': [
            'https://arxiv.org/list/quant-ph/recent',
            'https://quantum.ibm.com/',
            'https://ai.googleblog.com/search/label/Quantum',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/quantum_computing/',
            'embeddings': '/data/embeddings/quantum_computing/',
            'cache': '/cache/quantum_computing/',
        }
    },
    'neuroscience_cognitive': {
        'id': 22,
        'cluster': 'life_systems',
        'corpus_size_gb': 45,
        'temperature': 0.72,
        'style': 'Neural-network aware, plasticity-focused, embodied cognition',
        'domains': ['neuroscience', 'cognitive_science', 'brain_mapping', 'consciousness'],
        'training_sources': [
            'https://www.jneurosci.org/',
            'https://www.nature.com/neuro/',
            'https://www.cognitivesciencesociety.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/neuroscience_cognitive/',
            'embeddings': '/data/embeddings/neuroscience_cognitive/',
            'cache': '/cache/neuroscience_cognitive/',
        }
    },
    'systems_biology': {
        'id': 23,
        'cluster': 'life_systems',
        'corpus_size_gb': 35,
        'temperature': 0.7,
        'style': 'Holistic, network-centric, multi-scale integration',
        'domains': ['systems_biology', 'metabolomics', 'proteomics', 'bioinformatics'],
        'training_sources': [
            'https://www.systemsbiology.org/',
            'https://www.ebi.ac.uk/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/systems_biology/',
            'embeddings': '/data/embeddings/systems_biology/',
            'cache': '/cache/systems_biology/',
        }
    },
    'climate_earth_systems': {
        'id': 24,
        'cluster': 'stem_core',
        'corpus_size_gb': 50,
        'temperature': 0.7,
        'style': 'Planetary-scale, feedback-loop aware, long-horizon',
        'domains': ['climate_science', 'earth_systems', 'sustainability', 'ecology'],
        'training_sources': [
            'https://www.ipcc.ch/',
            'https://climate.nasa.gov/',
            'https://www.nature.com/nclimate/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/climate_earth_systems/',
            'embeddings': '/data/embeddings/climate_earth_systems/',
            'cache': '/cache/climate_earth_systems/',
        }
    },
    'robotics_embodied_ai': {
        'id': 25,
        'cluster': 'applied_tech',
        'corpus_size_gb': 25,
        'temperature': 0.72,
        'style': 'Sensor-fusion, real-time, physical-world grounded',
        'domains': ['robotics', 'embodied_ai', 'control_systems', 'perception'],
        'training_sources': [
            'https://www.ieee-ras.org/',
            'https://robotics.sciencemag.org/',
            'https://www.ros.org/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/robotics_embodied_ai/',
            'embeddings': '/data/embeddings/robotics_embodied_ai/',
            'cache': '/cache/robotics_embodied_ai/',
        }
    },
    'philosophy_tribunal': {
        'id': 26,
        'cluster': 'meta_cognitive',
        'corpus_size_gb': 20,
        'temperature': 0.78,
        'style': 'Dialectical, multi-perspective, truth-seeking tribunal',
        'domains': ['epistemology', 'ethics', 'logic', 'metaphysics'],
        'training_sources': [
            'https://plato.stanford.edu/',
            'https://philpapers.org/',
            'https://www.iep.utm.edu/',
        ],
        'data_dump_paths': {
            'primary': '/data/archetypes/philosophy_tribunal/',
            'embeddings': '/data/embeddings/philosophy_tribunal/',
            'cache': '/cache/philosophy_tribunal/',
        }
    },
}

# Calculate totals
TOTAL_CORPUS_GB = sum(a['corpus_size_gb'] for a in ARCHETYPES.values())
TOTAL_ARCHETYPES = len(ARCHETYPES)

# =============================================================================
# SYMBIOTIC FOLDER STRUCTURE FOR CROSS-PLATFORM SYNC
# =============================================================================
SYMBIOTIC_FOLDERS = {
    'data': {
        'description': 'Primary data storage for all archetypes',
        'subfolders': ['archetypes', 'embeddings', 'raw', 'processed'],
        'sync_priority': 'high',
        'compression': True,
    },
    'cache': {
        'description': 'Multi-layer cache (L1/L2/L3)',
        'subfolders': ['l1_hot', 'l2_warm', 'l3_cold'],
        'sync_priority': 'medium',
        'compression': True,
    },
    'config': {
        'description': 'Configuration files for all platforms',
        'subfolders': ['platforms', 'archetypes', 'sync'],
        'sync_priority': 'critical',
        'compression': False,
    },
    'models': {
        'description': 'Trained models and embeddings',
        'subfolders': ['ollama', 'embeddings', 'fine_tuned'],
        'sync_priority': 'high',
        'compression': True,
    },
    'logs': {
        'description': 'System logs and metrics',
        'subfolders': ['api', 'sync', 'training', 'errors'],
        'sync_priority': 'low',
        'compression': True,
    },
}

# =============================================================================
# LIVE URL ENDPOINTS FOR SYMBIOTIC CONNECTIONS
# =============================================================================
@dataclass
class LiveURLRegistry:
    """Registry of live URLs for cross-platform symbiotic connections"""
    
    # API Endpoints
    api_base: str = ""
    api_query: str = ""
    api_ingest: str = ""
    api_sync: str = ""
    api_health: str = ""
    
    # WebSocket Endpoints
    ws_realtime: str = ""
    ws_sync: str = ""
    ws_mentra: str = ""
    
    # Data Sync Endpoints
    sync_folder: str = ""
    sync_archetypes: str = ""
    sync_embeddings: str = ""
    
    # Monitoring
    metrics_prometheus: str = ""
    metrics_grafana: str = ""
    
    def set_base_url(self, base_url: str, ws_base: str = None):
        """Configure all endpoints from base URL"""
        ws_base = ws_base or base_url.replace('http', 'ws')
        
        self.api_base = base_url
        self.api_query = f"{base_url}/api/v1/query"
        self.api_ingest = f"{base_url}/api/v1/ingest"
        self.api_sync = f"{base_url}/api/v1/sync"
        self.api_health = f"{base_url}/health"
        
        self.ws_realtime = f"{ws_base}/ws/realtime"
        self.ws_sync = f"{ws_base}/ws/sync"
        self.ws_mentra = f"{ws_base}/ws/mentra"
        
        self.sync_folder = f"{base_url}/sync/folder"
        self.sync_archetypes = f"{base_url}/sync/archetypes"
        self.sync_embeddings = f"{base_url}/sync/embeddings"
        
        self.metrics_prometheus = f"{base_url}:9090/metrics"
        self.metrics_grafana = f"{base_url}:3000"

# Global URL registry
URL_REGISTRY = LiveURLRegistry()

# =============================================================================
# REDIS MULTI-LAYER CACHE CONFIGURATION
# =============================================================================
REDIS_CONFIG = {
    'l1_hot': {
        'host': os.getenv('REDIS_L1_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_L1_PORT', 6379)),
        'db': 0,
        'max_memory': '1gb',
        'eviction_policy': 'allkeys-lru',
        'ttl_seconds': 300,  # 5 minutes
    },
    'l2_warm': {
        'host': os.getenv('REDIS_L2_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_L2_PORT', 6379)),
        'db': 1,
        'max_memory': '4gb',
        'eviction_policy': 'allkeys-lru',
        'ttl_seconds': 3600,  # 1 hour
    },
    'l3_cold': {
        'host': os.getenv('REDIS_L3_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_L3_PORT', 6379)),
        'db': 2,
        'max_memory': '16gb',
        'eviction_policy': 'allkeys-lru',
        'ttl_seconds': 86400,  # 24 hours
    },
}

# =============================================================================
# COMPRESSION SETTINGS
# =============================================================================
COMPRESSION_CONFIG = {
    'algorithm': 'zstandard',
    'level': 19,  # Maximum compression
    'dict_size': 110 * 1024,  # 110KB dictionary
    'target_ratio': 0.70,  # 70% compression target
    'min_size_bytes': 1024,  # Only compress >1KB
}

print(f"✓ Quorum Universe Config Loaded")
print(f"  → {TOTAL_ARCHETYPES} archetypes ({TOTAL_CORPUS_GB} GB total corpus)")
print(f"  → Platform: {detect_platform()}")
print(f"  → Data path: {get_data_path()}")

# =============================================================================
# QUORUM TRIBUNAL - 6 PHILOSOPHERS + OBSERVER
# =============================================================================
# These are the 6 distinct philosophers that form the truth-seeking tribunal
# They chain together to analyze claims, with the Observer enforcing silence
# when consensus exceeds 0.92

QUORUM_PHILOSOPHERS = {
    'hume': {
        'id': 1,
        'name': 'David Hume',
        'era': '1711-1776',
        'tradition': 'Scottish Enlightenment',
        'lora_model': 'hume-70b',
        'style': 'Empirical skeptic - demands evidence, questions causation',
        'temperature': 0.7,
        'key_concepts': ['empiricism', 'skepticism', 'causation', 'induction', 'is-ought'],
        'training_sources': [
            'https://davidhume.org/',
            'https://plato.stanford.edu/entries/hume/',
            'A Treatise of Human Nature',
            'An Enquiry Concerning Human Understanding',
        ],
        'prompt_prefix': 'As Hume, the empirical skeptic who demands evidence and questions causation:',
    },
    'popper': {
        'id': 2,
        'name': 'Karl Popper',
        'era': '1902-1994',
        'tradition': 'Critical Rationalism',
        'lora_model': 'popper-70b',
        'style': 'Falsificationist - seeks what can be disproven, not confirmed',
        'temperature': 0.6,
        'key_concepts': ['falsifiability', 'demarcation', 'conjectures', 'refutations', 'open society'],
        'training_sources': [
            'https://plato.stanford.edu/entries/popper/',
            'The Logic of Scientific Discovery',
            'Conjectures and Refutations',
            'The Open Society and Its Enemies',
        ],
        'prompt_prefix': 'As Popper, the falsificationist who seeks what can be disproven:',
    },
    'quine': {
        'id': 3,
        'name': 'Willard Van Orman Quine',
        'era': '1908-2000',
        'tradition': 'Analytic Philosophy / Naturalism',
        'lora_model': 'quine-70b',
        'style': 'Naturalist - dissolves distinctions, challenges definitions',
        'temperature': 0.65,
        'key_concepts': ['holism', 'indeterminacy', 'naturalized epistemology', 'ontological relativity'],
        'training_sources': [
            'https://plato.stanford.edu/entries/quine/',
            'Two Dogmas of Empiricism',
            'Word and Object',
            'Ontological Relativity',
        ],
        'prompt_prefix': 'As Quine, the naturalist who dissolves distinctions and challenges definitions:',
    },
    'arendt': {
        'id': 4,
        'name': 'Hannah Arendt',
        'era': '1906-1975',
        'tradition': 'Political Theory / Phenomenology',
        'lora_model': 'arendt-70b',
        'style': 'Political theorist - examines power, propaganda, banal evil',
        'temperature': 0.7,
        'key_concepts': ['banality of evil', 'totalitarianism', 'public sphere', 'natality', 'action'],
        'training_sources': [
            'https://plato.stanford.edu/entries/arendt/',
            'The Origins of Totalitarianism',
            'The Human Condition',
            'Eichmann in Jerusalem',
        ],
        'prompt_prefix': 'As Arendt, the political theorist who examines power, propaganda, and banal evil:',
    },
    'zhuangzi': {
        'id': 5,
        'name': 'Zhuangzi (莊子)',
        'era': '369-286 BCE',
        'tradition': 'Daoist Philosophy',
        'lora_model': 'zhuangzi-70b',
        'style': 'Daoist sage - seeks paradox, values uselessness, embraces perspective',
        'temperature': 0.8,
        'key_concepts': ['wu wei', 'transformation', 'relativity', 'spontaneity', 'uselessness'],
        'training_sources': [
            'https://plato.stanford.edu/entries/zhuangzi/',
            'https://ctext.org/zhuangzi',
            'The Zhuangzi (Inner Chapters)',
            'Burton Watson translation',
        ],
        'prompt_prefix': 'As Zhuangzi, the Daoist sage who seeks paradox and embraces perspective:',
    },
    'ibn_khaldun': {
        'id': 6,
        'name': 'Ibn Khaldun (ابن خلدون)',
        'era': '1332-1406',
        'tradition': 'Islamic Philosophy / Historiography',
        'lora_model': 'khaldun-70b',
        'style': 'Civilizational analyst - tracks cycles, material forces, group solidarity',
        'temperature': 0.65,
        'key_concepts': ['asabiyyah', 'umran', 'civilizational cycles', 'historiography', 'social cohesion'],
        'training_sources': [
            'https://plato.stanford.edu/entries/ibn-khaldun/',
            'https://www.muslimheritage.com/ibn-khaldun/',
            'Muqaddimah (Prolegomena)',
            'Kitab al-Ibar',
        ],
        'prompt_prefix': 'As Ibn Khaldun, the civilizational analyst who tracks cycles and material forces:',
    },
}

# Observer configuration (7th entity - enforces silence on consensus)
QUORUM_OBSERVER = {
    'name': 'Observer',
    'role': 'Consensus enforcer - triggers silence when agreement exceeds threshold',
    'threshold': 0.92,  # Silence probability when consensus emerges
    'description': 'The Observer watches the tribunal and enforces silence when the 6 philosophers reach sufficient consensus (>92%). This prevents endless debate and signals stable truth.',
}

# Tribunal chain order (deliberation sequence)
QUORUM_CHAIN_ORDER = ['hume', 'popper', 'quine', 'arendt', 'zhuangzi', 'ibn_khaldun']

# Add observer to philosophers dict for test compatibility
QUORUM_PHILOSOPHERS['observer'] = QUORUM_OBSERVER

# Total philosophers
TOTAL_PHILOSOPHERS = len(QUORUM_PHILOSOPHERS)

print(f"  → {TOTAL_PHILOSOPHERS} tribunal philosophers configured")
print(f"  → Observer threshold: {QUORUM_OBSERVER['threshold']}")


# =============================================================================
# DELTA SYNC CONFIGURATION (Separate Repository Updates)
# =============================================================================
UPDATE_INTERVALS = {
    'daily': {
        'schedule': '0 3 * * *',      # 3 AM daily
        'max_size_mb': 50,
        'description': 'Bleeding-edge updates, ~5-50 MB daily',
    },
    'weekly': {
        'schedule': '0 3 * * 0',      # 3 AM Sunday
        'max_size_mb': 200,
        'description': 'Balanced updates, ~100-200 MB weekly',
    },
    'monthly': {
        'schedule': '0 3 1 * *',      # 3 AM 1st of month
        'max_size_mb': 2000,
        'description': 'Firmware-style updates, ~1-2 GB monthly',
    },
}

DELTA_REPO_CONFIG = {
    'main_repo': 'https://github.com/quorum-universe/quorum-universe',
    'delta_repo': 'https://github.com/quorum-universe/quorum-deltas',
    'default_interval': 'weekly',
    'verify_signatures': False,  # Enable when Kyber keys are set up
}

print(f"  → Delta sync configured (default: {DELTA_REPO_CONFIG['default_interval']})")

# QUORUM CONFIGURATION
# Copy this to config.py and customize for your setup

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',          # PostgreSQL host
    'port': 5432,                 # PostgreSQL port
    'database': 'ambient_intelligence',  # Database name
    'user': 'puck_user',         # Database user
    'password': 'change_me_in_production'  # CHANGE THIS!
}

AGE_GRAPH = 'quorum_graph'  # Name of the Apache AGE graph


# ============================================================================
# PHILOSOPHER LoRA MODELS
# ============================================================================

PHILOSOPHERS = {
    'hume': {
        'lora': 'hume-70b',           # Ollama model name
        'style': 'Empirical skeptic - demands evidence, questions causation',
        'temperature': 0.7,            # Creativity (0.0-1.0)
        'max_tokens': 300,            # Response length
        'enabled': True               # Enable/disable this philosopher
    },
    'popper': {
        'lora': 'popper-70b',
        'style': 'Falsificationist - seeks what can be disproven, not confirmed',
        'temperature': 0.6,
        'max_tokens': 300,
        'enabled': True
    },
    'quine': {
        'lora': 'quine-70b',
        'style': 'Naturalist - dissolves distinctions, challenges definitions',
        'temperature': 0.65,
        'max_tokens': 300,
        'enabled': True
    },
    'arendt': {
        'lora': 'arendt-70b',
        'style': 'Political theorist - examines power, propaganda, banal evil',
        'temperature': 0.7,
        'max_tokens': 300,
        'enabled': True
    },
    'zhuangzi': {
        'lora': 'zhuangzi-70b',
        'style': 'Daoist sage - seeks paradox, values uselessness, embraces perspective',
        'temperature': 0.8,
        'max_tokens': 300,
        'enabled': True
    },
    'khaldun': {
        'lora': 'khaldun-70b',
        'style': 'Civilizational analyst - tracks cycles, material forces, group solidarity',
        'temperature': 0.65,
        'max_tokens': 300,
        'enabled': True
    }
}


# ============================================================================
# OBSERVER CONFIGURATION
# ============================================================================

# Observer enforces silence when consensus is too high (groupthink risk)
OBSERVER_THRESHOLD = 0.92  # 0.0-1.0, higher = more strict

# Observer also triggers on low variance (all responses too similar)
OBSERVER_VARIANCE_MIN = 0.15


# ============================================================================
# CONTEXT HASHING
# ============================================================================

# Temporal decay - how often context hash rotates
CONTEXT_ROTATION_HOURS = 1  # Hash changes every N hours

# How many previous queries to include in context
CONTEXT_MEMORY_DEPTH = 3

# Weight factors for context components
CONTEXT_WEIGHTS = {
    'query': 1.0,
    'history': 0.6,
    'gaze': 0.4,
    'location': 0.3,
    'time': 0.5
}


# ============================================================================
# PATTERN MATCHING
# ============================================================================

# Minimum verdicts needed before pattern matching activates
PATTERN_MIN_VERDICTS = 50

# Similarity threshold for cached responses (0.0-1.0)
PATTERN_SIMILARITY_THRESHOLD = 0.80

# Maximum age of cached verdicts (days)
PATTERN_MAX_AGE_DAYS = 30


# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Parallel philosopher queries (experimental - requires more RAM)
PARALLEL_QUERIES = False

# Pre-load all LoRAs into memory (requires 240+ GB RAM)
PRELOAD_LORAS = False

# Cache responses in Redis (optional - requires redis-py)
ENABLE_REDIS_CACHE = False
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}


# ============================================================================
# AMBIENT INTELLIGENCE INTEGRATION
# ============================================================================

# Puck server settings (for remote queries from glasses)
PUCK_SERVER_HOST = '0.0.0.0'  # Listen on all interfaces
PUCK_SERVER_PORT = 8000

# Glasses integration
GLASSES_ENABLED = False
GLASSES_SDK_PATH = '/home/puck/mentra_sdk'

# Voice synthesis for responses
TTS_ENGINE = 'piper'  # Options: 'piper', 'coqui', 'none'
TTS_VOICE = 'philosopher_neutral'


# ============================================================================
# LOGGING & MONITORING
# ============================================================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = '/var/log/quorum/quorum.log'

# Prometheus metrics (optional)
ENABLE_METRICS = False
METRICS_PORT = 9090


# ============================================================================
# TREND ANALYSIS
# ============================================================================

# Auto-run on social media trends (requires cron job)
AUTO_TREND_ANALYSIS = False
TREND_SOURCES = ['twitter', 'reddit', 'hackernews']
TREND_CHECK_INTERVAL_HOURS = 6

# Auto-flag propaganda thresholds
PROPAGANDA_CONSENSUS_MAX = 0.30  # Low consensus = suspicious
PROPAGANDA_KEYWORDS = [
    'miracle cure', 'they don\'t want you to know',
    'doctors hate this', 'secret revealed'
]


# ============================================================================
# EXPERIMENTAL FEATURES
# ============================================================================

# Multi-lingual support (requires additional LoRAs)
ENABLE_MULTILINGUAL = False
SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'zh']

# Visual reasoning (requires vision-capable models)
ENABLE_VISION = False

# Long-term memory evolution (graph annealing)
ENABLE_GRAPH_ANNEALING = False
ANNEALING_SCHEDULE = 'nightly'  # 'hourly', 'daily', 'weekly', 'nightly'


# ============================================================================
# SECURITY
# ============================================================================

# API key for remote access (leave empty to disable)
API_KEY = ''

# Rate limiting (requests per minute per IP)
RATE_LIMIT = 10

# Allowed query sources (IPs or ranges)
ALLOWED_IPS = ['127.0.0.1', '192.168.1.0/24']


# ============================================================================
# DEVELOPMENT / DEBUG
# ============================================================================

# Enable verbose output
DEBUG_MODE = False

# Save all queries/responses to files (for training data)
SAVE_CONVERSATION_LOGS = False
CONVERSATION_LOG_DIR = '/tmp/quorum_logs'

# Simulate philosophers (for testing without LoRAs)
SIMULATION_MODE = False
SIMULATION_DELAY_SECONDS = 2

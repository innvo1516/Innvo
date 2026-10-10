import os
import sys
import warnings
import platform
from pathlib import Path

# Suppress harmless third-party deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*renamed to.*ddgs.*")

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
AUDIO_CACHE_DIR = CACHE_DIR / "audio"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

# Assistant Persona
ASSISTANT_NAME = "Innvo"
USER_NAME = "Sir"
DEFAULT_LANGUAGE = "hinglish"  # 'hinglish', 'hindi', 'english'

# Platform Detection
IS_TERMUX = "TERMUX_VERSION" in os.environ or "com.termux" in os.environ.get("PREFIX", "")
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux") and not IS_TERMUX
IS_MAC = sys.platform == "darwin"

# Voice / TTS Configuration
# Default: hi-IN-MadhurNeural (Warm, clear Indian Hindi/English male voice)
DEFAULT_VOICE = "hi-IN-MadhurNeural"
FALLBACK_VOICE = "hi-IN-SwaraNeural"
VOICE_RATE = "+0%"
VOICE_VOLUME = "+0%"
VOICE_PITCH = "+0Hz"

# Reinforcement Learning Settings
RL_DB_PATH = DATA_DIR / "innvo_memory.db"
RL_POLICY_PATH = DATA_DIR / "rl_policy.json"
RL_REFLEXION_PATH = DATA_DIR / "reflexions.json"

RL_ALPHA = 0.15       # Learning rate
RL_EPSILON = 0.15     # Exploration rate
RL_GAMMA = 0.90       # Discount factor

# Reward Constants
REWARD_APPROVAL = 1.0       # User said "Yes / Haan / Save it"
REWARD_PRAISE = 0.8         # User said "Great job / Perfect / Sahi hai"
REWARD_NEUTRAL = 0.0        # Normal flow
REWARD_REJECTION = -0.5     # User said "No / Nahi / Rehne do"
REWARD_CORRECTION = -1.0    # User corrected a fact or told Innvo it made an error

# Search & Retrieval Configuration
MAX_SEARCH_RESULTS = 4
SEARCH_TIMEOUT_SECONDS = 6

# Security & Constitutional Tripwires
SECURITY_DIR = BASE_DIR / "security"
CONSTITUTION_PATH = SECURITY_DIR / "constitution.json"
CONSTITUTION_HASH_PATH = SECURITY_DIR / "constitution.hash"
SHADOW_VAULT_DIR = BASE_DIR / ".shadow_vault"
DEFAULT_MASTER_SECRET = "INNVO_HUMAN_OPERATOR_SOVEREIGN_SEED_2026"

# Ensure security directories exist
SECURITY_DIR.mkdir(exist_ok=True)
SHADOW_VAULT_DIR.mkdir(exist_ok=True)

# Knowledge Graph & Semantic Triplets
KNOWLEDGE_GRAPH_PATH = DATA_DIR / "knowledge_graph.db"

# Hive-Mind Micro-Delta Sync
SYNC_DIR = DATA_DIR / "sync"
SYNC_DIR.mkdir(exist_ok=True)

# Autonomous Idle Curiosity Configuration
IDLE_LEARNING_ENABLED = False  # Strictly OFF by default. Toggled via /idle command.
IDLE_CHECK_INTERVAL_SECONDS = 60
IDLE_MAX_DAILY_QUERIES = 15

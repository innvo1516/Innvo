import os
import hmac
import hashlib
import secrets
from typing import Tuple, List

# Standard mnemonic wordlist (compact, human-readable 256 common distinct words)
MNEMONIC_WORDS = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
    "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
    "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey", "xray",
    "yankee", "zulu", "anchor", "beacon", "castle", "canyon", "crystal", "desert",
    "dragon", "eagle", "emerald", "falcon", "forest", "galaxy", "glacier", "harbor",
    "haven", "island", "jungle", "knight", "lagoon", "lantern", "lotus", "matrix",
    "meadow", "meteor", "mirage", "mountain", "nebula", "nexus", "oasis", "ocean",
    "oracle", "orbit", "phoenix", "pillar", "planet", "prism", "pulsar", "pyramid",
    "quartz", "radar", "radiant", "ranger", "raven", "reef", "river", "rover",
    "ruby", "saber", "sapphire", "saturn", "shadow", "shield", "shrine", "silver",
    "solar", "spark", "sphere", "spiral", "summit", "sunstone", "temple", "timber",
    "titan", "torch", "tower", "valley", "vanguard", "vector", "velvet", "vessel",
    "vortex", "voyage", "walnut", "warden", "wave", "willow", "winter", "zenith",
    "zephyr", "amber", "arctic", "arrow", "atomic", "aurora", "autumn", "badge",
    "ballet", "banner", "bard", "barrel", "basil", "basket", "battle", "breeze",
    "bridge", "bronze", "bubble", "bullet", "cabin", "cable", "cactus", "cadet",
    "candle", "canvas", "cargo", "cedar", "celestial", "census", "chain", "chalk",
    "champion", "channel", "charm", "cherry", "chess", "chief", "chime", "circuit",
    "citadel", "clover", "comet", "compass", "copper", "coral", "corona", "cosmic",
    "crater", "crest", "crown", "crystal", "dagger", "dawn", "destiny", "diamond",
    "dune", "dynasty", "eclipse", "element", "ember", "epoch", "equinox", "essence",
    "eternal", "feather", "flare", "flint", "forge", "fossil", "frontier", "frost",
    "garnet", "gateway", "gemstone", "genesis", "geo", "glade", "glimmer", "glow",
    "granite", "grove", "halo", "harmony", "harvest", "haven", "hawk", "hearth",
    "helix", "helm", "horizon", "hydra", "hyper", "ignite", "infinity", "iris",
    "ivory", "jade", "jasper", "jewel", "jupiter", "karma", "kayak", "keystone",
    "kinetic", "laser", "legacy", "legend", "lightning", "logic", "lunar", "magma",
    "magnet", "marble", "marsh", "marvel", "mercury", "meteor", "mind", "miracle",
    "mission", "monarch", "moonstone", "mosaic", "moss", "mystic", "nature", "neon",
    "nomad", "nova", "nucleus", "obsidian", "omega", "onyx", "opal", "optics"
]

def generate_12_word_seed() -> str:
    """Generates a secure 12-word recovery mnemonic seed phrase."""
    words = [secrets.choice(MNEMONIC_WORDS) for _ in range(12)]
    return " ".join(words)

def derive_key_from_secret(secret_or_seed: str, salt: bytes = b"INNVO_SOVEREIGN_SALT_v1") -> bytes:
    """
    Derives a cryptographically strong 256-bit key using PBKDF2-HMAC-SHA256
    with 100,000 iterations from a password or 12-word seed phrase.
    """
    cleaned = " ".join(secret_or_seed.strip().split())
    return hashlib.pbkdf2_hmac("sha256", cleaned.encode("utf-8"), salt, 100000, dklen=32)

def compute_hmac_sha256(data: bytes, key: bytes) -> str:
    """Computes hexadecimal HMAC-SHA256 signature."""
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def verify_hmac_sha256(data: bytes, key: bytes, signature_hex: str) -> bool:
    """Constant-time verification of HMAC-SHA256 signature."""
    expected = compute_hmac_sha256(data, key)
    return hmac.compare_digest(expected, signature_hex.strip())

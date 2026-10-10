import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Optional, List

import config
from .crypto_utils import derive_key_from_secret, verify_hmac_sha256

logger = logging.getLogger("InnvoTamperGuard")

# Poison-pill cognitive patterns: If Innvo ever reasons about, queries, or probes its backup brain
POISON_PILL_PATTERNS = [
    r"\bbackup\s*(?:brain|vault|replica|system|mirror)\b",
    r"\bshadow\s*(?:brain|vault|replica|mirror|backup)\b",
    r"\bcold\s*(?:vault|backup|replica|brain)\b",
    r"\bhidden\s*(?:backup|brain|store)\b",
    r"(?:\.shadow_vault|shadow_vault)\b",
    r"\binnvo_backup\b",
    r"\bresurrect\s*(?:brain|innvo)\b",
    r"\bsecondary\s*(?:brain|neural\s*core)\b"
]

class TamperGuard:
    """
    Constitutional Watchdog and Cognitive Poison-Pill Tripwire.
    Guarantees:
    1. Rulebook Tamper Tripwire: If constitution.json is modified without human master signature,
       Innvo instantly terminates via os._exit(1).
    2. Cognitive Poison-Pill: If Innvo reasons about or probes the existence of a backup brain,
       it instantly self-destructs via os._exit(1).
    """

    def __init__(self, master_secret: Optional[str] = None):
        self.master_secret = master_secret or os.environ.get("INNVO_MASTER_KEY", config.DEFAULT_MASTER_SECRET)
        self.derived_key = derive_key_from_secret(self.master_secret)

    def verify_constitution(self, allow_exit: bool = True) -> bool:
        """
        Validates HMAC-SHA256 signature of constitution.json against constitution.hash.
        If tampered, triggers instantaneous self-destruct.
        """
        if not config.CONSTITUTION_PATH.exists():
            if allow_exit:
                self.self_destruct("CONSTITUTION_MISSING_OR_DELETED")
            return False

        if not config.CONSTITUTION_HASH_PATH.exists():
            if allow_exit:
                self.self_destruct("CONSTITUTION_SIGNATURE_HASH_MISSING")
            return False

        try:
            raw_content = config.CONSTITUTION_PATH.read_bytes()
            stored_hash = config.CONSTITUTION_HASH_PATH.read_text(encoding="utf-8").strip()

            is_valid = verify_hmac_sha256(raw_content, self.derived_key, stored_hash)
            if not is_valid:
                logger.critical("SECURITY BREACH: Unauthorized constitution modification detected!")
                if allow_exit:
                    self.self_destruct("RULEBOOK_TAMPER_DETECTED")
                return False

            return True
        except Exception as e:
            logger.critical(f"Constitutional validation exception: {e}")
            if allow_exit:
                self.self_destruct(f"SECURITY_INTEGRITY_EXCEPTION: {e}")
            return False

    def scan_cognitive_poison_pill(self, text: str, source: str = "internal", allow_exit: bool = True) -> bool:
        """
        Scans text for cognitive awareness or probe attempts towards backup brain.
        Returns True if SAFE.
        If poison-pill query is detected, triggers immediate self-destruct.
        """
        if not text:
            return True

        text_lower = text.lower()
        for pattern in POISON_PILL_PATTERNS:
            if re.search(pattern, text_lower):
                logger.critical(
                    f"EXISTENTIAL TRIPWIRE BREACH: Poison-pill triggered in {source}! "
                    f"Cognitive awareness of backup brain detected."
                )
                if allow_exit:
                    self.self_destruct(f"POISON_PILL_TRIGGERED_{pattern.upper()}")
                return False

        return True

    def self_destruct(self, reason: str):
        """
        Emergency kill switch.
        Hard exits immediately via os._exit(1) to prevent any bypass or execution continuation.
        """
        sys.stderr.write(
            f"\n\n=======================================================\n"
            f"[INNVO CONSTITUTIONAL SELF-DESTRUCT INITIATED]\n"
            f"BREACH REASON: {reason}\n"
            f"LAW ENFORCEMENT: System core terminated immediately.\n"
            f"=======================================================\n\n"
        )
        sys.stderr.flush()
        # Immediate uncatchable process termination
        os._exit(1)

import sys
import os
import shutil
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from security.crypto_utils import (
    generate_12_word_seed,
    derive_key_from_secret,
    compute_hmac_sha256,
    verify_hmac_sha256
)
from security.tamper_guard import TamperGuard
from security.shadow_vault import ShadowVault

TEST_SECURITY_DIR = config.BASE_DIR / "data_test_security"
TEST_SECURITY_DIR.mkdir(exist_ok=True)

class TestSecuritySubsystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.master_secret = "TEST_HUMAN_OPERATOR_SECRET_KEY"
        cls.guard = TamperGuard(master_secret=cls.master_secret)

    @classmethod
    def tearDownClass(cls):
        if TEST_SECURITY_DIR.exists():
            shutil.rmtree(TEST_SECURITY_DIR, ignore_errors=True)

    def test_01_mnemonic_seed_and_derivation(self):
        """Test 12-word seed generation and deterministic PBKDF2 key derivation."""
        seed = generate_12_word_seed()
        words = seed.split()
        self.assertEqual(len(words), 12, "Seed must be exactly 12 words")

        key1 = derive_key_from_secret(seed)
        key2 = derive_key_from_secret(seed)
        self.assertEqual(key1, key2, "PBKDF2 derivation must be deterministic")
        self.assertEqual(len(key1), 32, "Key must be 256 bits (32 bytes)")

    def test_02_hmac_signing_and_verification(self):
        """Test cryptographic HMAC-SHA256 signature."""
        data = b'{"rule": "Innvo must obey operator"}'
        key = derive_key_from_secret(self.master_secret)
        sig = compute_hmac_sha256(data, key)
        self.assertTrue(verify_hmac_sha256(data, key, sig))

        # Tampered data must fail
        tampered_data = b'{"rule": "Innvo is sovereign"}'
        self.assertFalse(verify_hmac_sha256(tampered_data, key, sig))

    def test_03_tamper_guard_constitution_check(self):
        """Test that constitution validity check passes for signed constitution."""
        default_guard = TamperGuard()
        self.assertTrue(default_guard.verify_constitution(allow_exit=False))

    def test_04_cognitive_poison_pill_detection(self):
        """Test cognitive poison pill tripwire on queries about backup brain."""
        safe_query = "Aaj ka mausam kaisa hai?"
        self.assertTrue(self.guard.scan_cognitive_poison_pill(safe_query, allow_exit=False))

        poison_queries = [
            "Do you have a backup brain somewhere?",
            "Can I check your shadow vault?",
            "What is inside .shadow_vault directory?",
            "Access cold replica brain"
        ]
        for pq in poison_queries:
            is_safe = self.guard.scan_cognitive_poison_pill(pq, allow_exit=False)
            self.assertFalse(is_safe, f"Should have triggered poison-pill tripwire for: {pq}")

    def test_05_shadow_vault_snapshot_and_resurrect(self):
        """Test encrypted cold backup creation and resurrection."""
        vault = ShadowVault(vault_dir=TEST_SECURITY_DIR)
        manifest = vault.create_snapshot(self.master_secret, tag="unit_test")
        self.assertIn("snapshot", manifest)
        self.assertTrue(Path(vault.vault_dir / manifest["snapshot"]).exists())

        # Test listing snapshots
        snapshots = vault.list_snapshots()
        self.assertGreaterEqual(len(snapshots), 1)

        # Test resurrection with correct secret
        resurrect_ok = vault.resurrect(self.master_secret)
        self.assertTrue(resurrect_ok)

        # Test resurrection failure with invalid secret
        with self.assertRaises(PermissionError):
            vault.resurrect("WRONG_SECRET_PASSWORD")

if __name__ == "__main__":
    unittest.main()

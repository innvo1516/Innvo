import os
import io
import time
import json
import base64
import tarfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from cryptography.fernet import Fernet
import config
from .crypto_utils import derive_key_from_secret

logger = logging.getLogger("InnvoShadowVault")

class ShadowVault:
    """
    Air-gapped Cold Shadow Vault for Innvo.
    COMPLETELY DISCONNECTED from Innvo's cognitive reasoning loop.
    Allows the human operator to take encrypted cold backups and resurrect Innvo
    in the event of corruption, model drift, or intentional self-destruct.
    """

    def __init__(self, vault_dir: Optional[Path] = None):
        self.vault_dir = vault_dir or config.SHADOW_VAULT_DIR
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def _get_cipher(self, secret_or_seed: str) -> Fernet:
        raw_key = derive_key_from_secret(secret_or_seed, salt=b"INNVO_VAULT_SALT_v1")
        fernet_key = base64.urlsafe_b64encode(raw_key)
        return Fernet(fernet_key)

    def create_snapshot(self, secret_or_seed: str, tag: str = "auto") -> Dict[str, Any]:
        """
        Creates an encrypted, compressed snapshot of Innvo's memories, skills, and knowledge.
        """
        cipher = self._get_cipher(secret_or_seed)
        timestamp = int(time.time())
        snapshot_filename = f"vault_snapshot_{timestamp}_{tag}.enc"
        target_path = self.vault_dir / snapshot_filename

        # Collect files to back up
        files_to_backup = [
            config.RL_DB_PATH,
            config.RL_POLICY_PATH,
            config.RL_REFLEXION_PATH,
            config.DATA_DIR / "skills.json",
            config.KNOWLEDGE_GRAPH_PATH
        ]

        # In-memory tarball
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
            for f in files_to_backup:
                if f.exists():
                    tar.add(str(f), arcname=f.name)
            
            # Backup dynamic tools if any exist
            dynamic_dir = config.BASE_DIR / "tools" / "dynamic"
            if dynamic_dir.exists():
                for tool_file in dynamic_dir.glob("*.py"):
                    tar.add(str(tool_file), arcname=f"dynamic/{tool_file.name}")

        unencrypted_bytes = tar_buffer.getvalue()
        encrypted_bytes = cipher.encrypt(unencrypted_bytes)
        target_path.write_bytes(encrypted_bytes)

        manifest = {
            "snapshot": snapshot_filename,
            "timestamp": timestamp,
            "size_bytes": len(encrypted_bytes),
            "files_included": [f.name for f in files_to_backup if f.exists()]
        }

        # Update encrypted manifest
        manifest_path = self.vault_dir / "latest_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return manifest

    def resurrect(self, secret_or_seed: str, snapshot_path: Optional[Path] = None) -> bool:
        """
        Restores Innvo's entire memory and skill state from an encrypted cold snapshot.
        Overwrites current corrupted files with verified snapshot data.
        """
        cipher = self._get_cipher(secret_or_seed)
        
        if not snapshot_path:
            # Find latest snapshot
            snapshots = sorted(self.vault_dir.glob("vault_snapshot_*.enc"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not snapshots:
                raise FileNotFoundError("No shadow vault snapshots found to resurrect from.")
            snapshot_path = snapshots[0]

        encrypted_data = snapshot_path.read_bytes()
        try:
            decrypted_data = cipher.decrypt(encrypted_data)
        except Exception as e:
            raise PermissionError(f"Failed to decrypt snapshot. Invalid master password or seed phrase: {e}")

        # Extract tarball into data dir
        tar_buffer = io.BytesIO(decrypted_data)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name.startswith("dynamic/"):
                    dest = config.BASE_DIR / "tools" / member.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    f = tar.extractfile(member)
                    if f:
                        dest.write_bytes(f.read())
                else:
                    dest = config.DATA_DIR / member.name
                    f = tar.extractfile(member)
                    if f:
                        dest.write_bytes(f.read())

        return True

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Lists metadata of available cold snapshots (without decrypting contents)."""
        res = []
        for p in sorted(self.vault_dir.glob("vault_snapshot_*.enc"), key=lambda x: x.stat().st_mtime, reverse=True):
            res.append({
                "path": str(p),
                "filename": p.name,
                "size_kb": round(p.stat().st_size / 1024, 2),
                "modified": time.ctime(p.stat().st_mtime)
            })
        return res

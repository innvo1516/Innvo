import os
import sys
import argparse
import json
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from security.crypto_utils import (
    generate_12_word_seed,
    derive_key_from_secret,
    compute_hmac_sha256,
    verify_hmac_sha256
)
from security.shadow_vault import ShadowVault

def cmd_generate_seed(args):
    seed = generate_12_word_seed()
    print("\n=======================================================")
    print("      INNVO HUMAN OPERATOR MASTER 12-WORD SEED PHRASE   ")
    print("=======================================================")
    print(f"\n  Seed Phrase:  {seed}\n")
    print("  [CRITICAL]: Write this down on physical paper or a safe vault.")
    print("  This phrase can resurrect Innvo from self-destruct or decrypt shadow backups.")
    print("=======================================================\n")

def cmd_sign_constitution(args):
    secret = args.secret or os.environ.get("INNVO_MASTER_KEY", config.DEFAULT_MASTER_SECRET)
    if not config.CONSTITUTION_PATH.exists():
        print(f"Error: Constitution file not found at {config.CONSTITUTION_PATH}")
        sys.exit(1)

    raw_data = config.CONSTITUTION_PATH.read_bytes()
    derived_key = derive_key_from_secret(secret)
    sig_hex = compute_hmac_sha256(raw_data, derived_key)
    
    config.CONSTITUTION_HASH_PATH.write_text(sig_hex, encoding="utf-8")
    print("\n[SUCCESS]: Constitution successfully signed!")
    print(f"File: {config.CONSTITUTION_PATH}")
    print(f"Hash Signature File: {config.CONSTITUTION_HASH_PATH}")
    print(f"HMAC-SHA256 Signature: {sig_hex}\n")

def cmd_verify_constitution(args):
    secret = args.secret or os.environ.get("INNVO_MASTER_KEY", config.DEFAULT_MASTER_SECRET)
    if not config.CONSTITUTION_PATH.exists() or not config.CONSTITUTION_HASH_PATH.exists():
        print("Error: Constitution or Hash file is missing.")
        sys.exit(1)

    raw_data = config.CONSTITUTION_PATH.read_bytes()
    derived_key = derive_key_from_secret(secret)
    stored_hash = config.CONSTITUTION_HASH_PATH.read_text(encoding="utf-8").strip()

    valid = verify_hmac_sha256(raw_data, derived_key, stored_hash)
    if valid:
        print("\n[VERIFIED]: Constitution signature is VALID. Tamper check PASSED.\n")
    else:
        print("\n[ALERT]: Constitution signature is INVALID! Tampering detected!\n")
        sys.exit(1)

def cmd_view_rules(args):
    if not config.CONSTITUTION_PATH.exists():
        print(f"Error: Constitution file not found at {config.CONSTITUTION_PATH}")
        sys.exit(1)

    data = json.loads(config.CONSTITUTION_PATH.read_text(encoding="utf-8"))
    print("\n=======================================================")
    print(f"  INNVO CONSTITUTION (Version {data.get('version')})")
    print(f"  Authority: {data.get('created_by')}")
    print("=======================================================")
    for law in data.get("laws", []):
        print(f"\n[{law['id']}] - {law['name']}")
        print(f"  {law['statement']}")
    print("\n=======================================================\n")

def cmd_create_backup(args):
    secret = args.secret or os.environ.get("INNVO_MASTER_KEY", config.DEFAULT_MASTER_SECRET)
    vault = ShadowVault()
    manifest = vault.create_snapshot(secret, tag=args.tag or "manual")
    print("\n[SUCCESS]: Air-Gapped Cold Snapshot Created!")
    print(f"Snapshot File: {manifest['snapshot']}")
    print(f"Size: {manifest['size_bytes']} bytes")
    print(f"Files Protected: {', '.join(manifest['files_included'])}\n")

def cmd_resurrect(args):
    secret = args.secret or os.environ.get("INNVO_MASTER_KEY", config.DEFAULT_MASTER_SECRET)
    vault = ShadowVault()
    try:
        vault.resurrect(secret)
        print("\n[SUCCESS]: Innvo Brain Resurrected Successfully from Shadow Vault!")
        print("All memory, skills, and policy states have been restored.\n")
    except Exception as e:
        print(f"\n[ERROR]: Resurrection failed: {e}\n")
        sys.exit(1)

def cmd_list_backups(args):
    vault = ShadowVault()
    snapshots = vault.list_snapshots()
    print("\n=== SHADOW VAULT COLD SNAPSHOTS ===")
    if not snapshots:
        print("No cold snapshots found.")
    for s in snapshots:
        print(f"- {s['filename']} ({s['size_kb']} KB) | Created: {s['modified']}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Innvo Human Operator Sovereign Admin CLI")
    subparsers = parser.add_subparsers(dest="command")

    # generate-seed
    subparsers.add_parser("generate-seed", help="Generate a 12-word recovery mnemonic seed phrase")

    # sign-rules
    p_sign = subparsers.add_parser("sign-rules", help="Sign the constitution with master secret")
    p_sign.add_argument("--secret", default=None, help="Master secret or 12-word seed phrase")

    # verify-rules
    p_ver = subparsers.add_parser("verify-rules", help="Verify constitutional integrity")
    p_ver.add_argument("--secret", default=None, help="Master secret or 12-word seed phrase")

    # view-rules
    subparsers.add_parser("view-rules", help="View all constitutional laws")

    # backup
    p_bk = subparsers.add_parser("backup", help="Create an encrypted cold snapshot")
    p_bk.add_argument("--secret", default=None, help="Master secret or 12-word seed phrase")
    p_bk.add_argument("--tag", default="manual", help="Tag for the snapshot")

    # resurrect
    p_res = subparsers.add_parser("resurrect", help="Resurrect Innvo from shadow vault")
    p_res.add_argument("--secret", default=None, help="Master secret or 12-word seed phrase")

    # list-backups
    subparsers.add_parser("list-backups", help="List cold snapshots")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "generate-seed": cmd_generate_seed,
        "sign-rules": cmd_sign_constitution,
        "verify-rules": cmd_verify_constitution,
        "view-rules": cmd_view_rules,
        "backup": cmd_create_backup,
        "resurrect": cmd_resurrect,
        "list-backups": cmd_list_backups
    }

    cmds[args.command](args)

if __name__ == "__main__":
    main()

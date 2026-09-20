import os
import sys
import warnings

# Suppress harmless third-party deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*renamed to.*ddgs.*")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import argparse
import config
from brain.orchestrator import InnvoOrchestrator
from ui.terminal_ui import TerminalUI

def parse_args():
    parser = argparse.ArgumentParser(description="Innvo - Cross-Platform Local RL AI Assistant")
    parser.add_argument("--no-voice", action="store_true", help="Start Innvo in text-only mode without speech output")
    parser.add_argument("--continuous", action="store_true", help="Start immediately in continuous hands-free voice mode")
    parser.add_argument("--voice", type=str, default=config.DEFAULT_VOICE, help=f"TTS Voice name (default: {config.DEFAULT_VOICE})")
    return parser.parse_args()

def main():
    args = parse_args()
    voice_enabled = not args.no_voice

    # Initialize Innvo Core Orchestrator
    orchestrator = InnvoOrchestrator(voice_enabled=voice_enabled)
    if args.voice:
        orchestrator.audio.voice_name = args.voice

    # Launch Terminal UI
    ui = TerminalUI(orchestrator)
    if args.continuous:
        ui.continuous_voice = True

    try:
        ui.run_loop()
    except Exception as e:
        print(f"\n[Innvo System Error]: {e}")

if __name__ == "__main__":
    main()

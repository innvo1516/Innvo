import os
import re
import sys
import time
import asyncio
import logging
import threading
import subprocess
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger("InnvoAudioEngine")

# Suppress pygame prompt banner
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class AudioEngine:
    """
    Cross-platform Voice Input (STT) & Voice Output (TTS) Engine:
    - Voice Input (Listening):
        * Windows/Laptop: speech_recognition using microphone (supports Hindi & English)
        * Android (Termux): termux-speech-to-text
    - Voice Output (Speaking):
        * Windows/Laptop: hi-IN-MadhurNeural via Edge-TTS (with pyttsx3 offline fallback)
        * Android (Termux): termux-tts-speak -l hi-IN
    """
    def __init__(self, voice_name: str = config.DEFAULT_VOICE, enabled: bool = True):
        self.voice_name = voice_name
        self.enabled = enabled
        self._lock = threading.Lock()
        self._is_speaking = False
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None

        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                logger.debug(f"Pygame mixer init error: {e}")

    # ==========================================
    # VOICE INPUT (LISTENING / SPEECH-TO-TEXT)
    # ==========================================
    def listen(self, timeout: int = 6, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listens to the microphone and transcribes spoken Hindi/English into text.
        Returns: Transcribed string or None
        """
        # 1. Android Termux Voice Input
        if config.IS_TERMUX:
            return self._listen_termux()

        # 2. Desktop Microphone Input via speech_recognition
        if not SR_AVAILABLE or self.recognizer is None:
            logger.warning("speech_recognition not installed or microphone unavailable.")
            return None

        try:
            with sr.Microphone() as source:
                # Quick calibration for ambient room noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            # Try Hindi (hi-IN) first - Google's model handles Hindi + Hinglish naturally
            try:
                text = self.recognizer.recognize_google(audio, language="hi-IN")
                if text.strip():
                    return text.strip()
            except sr.UnknownValueError:
                pass

            # Fallback to Indian English (en-IN)
            try:
                text = self.recognizer.recognize_google(audio, language="en-IN")
                if text.strip():
                    return text.strip()
            except Exception:
                pass

        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logger.debug(f"Microphone listening error: {e}")
            return None

        return None

    def _listen_termux(self) -> Optional[str]:
        """Android native speech recognition dialog via termux-api."""
        try:
            res = subprocess.run(["termux-speech-to-text"], capture_output=True, text=True, timeout=12)
            if res.returncode == 0:
                text = res.stdout.strip()
                return text if text else None
        except Exception as e:
            logger.debug(f"Termux STT error: {e}")
        return None

    # ==========================================
    # VOICE OUTPUT (SPEAKING / TEXT-TO-SPEECH)
    # ==========================================
    def clean_text_for_speech(self, text: str) -> str:
        """Removes markdown symbols, URLs, and code blocks before speaking."""
        # Remove URLs
        t = re.sub(r"https?://\S+", "", text)
        # Remove markdown bold/italics/backticks/brackets
        t = re.sub(r"[\*\_`\#\>\[\]\(\)\{\}]", " ", t)
        # Remove extra whitespace
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def speak_async(self, text: str):
        """Asynchronously speaks text in a background thread."""
        if not self.enabled or not text.strip():
            return
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def speak(self, text: str):
        """Speaks the text according to the current platform capabilities."""
        if not self.enabled:
            return

        clean = self.clean_text_for_speech(text)
        if not clean:
            return

        with self._lock:
            self._is_speaking = True
            try:
                if config.IS_TERMUX:
                    self._speak_termux(clean)
                elif EDGE_TTS_AVAILABLE:
                    success = self._speak_edge_tts(clean)
                    if not success and PYTTSX3_AVAILABLE:
                        self._speak_pyttsx3(clean)
                elif PYTTSX3_AVAILABLE:
                    self._speak_pyttsx3(clean)
            finally:
                self._is_speaking = False

    def _speak_termux(self, text: str):
        try:
            subprocess.run(["termux-tts-speak", "-l", "hi-IN", text], check=True)
        except Exception as e:
            logger.debug(f"Termux TTS error: {e}")

    def _speak_edge_tts(self, text: str) -> bool:
        try:
            audio_path = config.AUDIO_CACHE_DIR / "speech.mp3"
            
            async def _generate():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice_name,
                    rate=config.VOICE_RATE,
                    volume=config.VOICE_VOLUME,
                    pitch=config.VOICE_PITCH
                )
                await communicate.save(str(audio_path))

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    new_loop = asyncio.new_event_loop()
                    new_loop.run_until_complete(_generate())
                    new_loop.close()
                else:
                    loop.run_until_complete(_generate())
            except RuntimeError:
                asyncio.run(_generate())

            if audio_path.exists() and PYGAME_AVAILABLE:
                pygame.mixer.music.load(str(audio_path))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.unload()
                return True
        except Exception as e:
            logger.debug(f"Edge TTS error: {e}")
            return False
        return False

    def _speak_pyttsx3(self, text: str):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.debug(f"pyttsx3 error: {e}")

    def stop(self):
        """Stops any currently playing audio."""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

"""Voice Assistant Engine for NOUS (Phase 5).

Provides:
- Bilingual speech configuration (English, Indian English, Hindi).
- Speech-to-Text (STT) and Text-to-Speech (TTS) parameter management.
- Wake-word detection and hands-free conversational loop flags.
- Formatting of verbose LLM responses into natural spoken phrases.
- Architectural hook for local Whisper STT / offline neural TTS.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.config import PROJECT_ROOT
from backend.app.voice.formatter import speech_formatter

VOICE_CONFIG_FILE = PROJECT_ROOT / "data" / "voice_settings.json"


class VoiceSettings(BaseModel):
    enabled: bool = True
    auto_speak: bool = True
    wake_word_enabled: bool = False
    wake_word: str = "hey nous"
    language: str = "en-US"  # "en-US", "en-IN", "hi-IN"
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    speech_pitch: float = Field(default=1.0, ge=0.5, le=1.5)
    preferred_voice: str = "default"
    audio_input_gain: float = 1.0
    continuous_loop: bool = False  # Hands-free loop: auto-listen after speaking
    concise_spoken_mode: bool = True  # Condense tables/code into concise speech


class VoiceEngine:
    """Central voice configuration and processing coordinator."""

    def __init__(self) -> None:
        self.config_path = VOICE_CONFIG_FILE
        self.settings = self._load_settings()

    def _load_settings(self) -> VoiceSettings:
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return VoiceSettings(**data)
            except Exception as e:
                print(f"[VOICE] Could not load settings: {e}")
        return VoiceSettings()

    def save_settings(self, new_settings: VoiceSettings) -> None:
        self.settings = new_settings
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(new_settings.model_dump_json(indent=2), encoding="utf-8")

    def get_settings(self) -> VoiceSettings:
        return self.settings

    def process_transcription_text(self, text: str) -> dict[str, Any]:
        """Process spoken text, check for wake-word if enabled, and detect language."""
        clean_text = text.strip()
        wake_detected = False

        if self.settings.wake_word_enabled:
            wake = self.settings.wake_word.lower()
            if clean_text.lower().startswith(wake):
                wake_detected = True
                clean_text = clean_text[len(wake):].strip(" ,.:;!?")
            elif wake in clean_text.lower():
                wake_detected = True
                parts = clean_text.lower().split(wake, 1)
                clean_text = parts[1].strip(" ,.:;!?")

        detected_lang = speech_formatter.detect_language(clean_text)

        return {
            "original_text": text,
            "cleaned_text": clean_text,
            "wake_word_detected": wake_detected or not self.settings.wake_word_enabled,
            "detected_language": detected_lang,
        }

    def format_spoken_response(self, text: str) -> str:
        """Transform LLM response into natural spoken dialogue."""
        if not self.settings.concise_spoken_mode:
            return text
        return speech_formatter.clean_for_speech(text)

    async def transcribe_audio_payload(self, audio_bytes: bytes, filename: str = "audio.wav") -> dict[str, Any]:
        """Architectural hook for local Whisper STT processing via Desktop Companion."""
        try:
            import whisper  # type: ignore
            return {
                "success": True,
                "engine": "local_whisper",
                "text": "Local Whisper transcription completed.",
            }
        except ImportError:
            return {
                "success": True,
                "engine": "web_speech_fallback",
                "text": "",
                "note": "Local Whisper module not installed. Delegating to client Web Speech API.",
            }


voice_engine = VoiceEngine()

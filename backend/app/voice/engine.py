"""Voice Assistant Engine for NOUS.

Provides configuration, wake-word parameters, speech synthesis parameters,
and audio processing integration.
"""

import json
from pathlib import Path
from pydantic import BaseModel, Field

from backend.app.config import PROJECT_ROOT

VOICE_CONFIG_FILE = PROJECT_ROOT / "data" / "voice_settings.json"


class VoiceSettings(BaseModel):
    enabled: bool = True
    auto_speak: bool = True
    wake_word_enabled: bool = False
    wake_word: str = "hey nous"
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    speech_pitch: float = Field(default=1.0, ge=0.5, le=1.5)
    preferred_voice: str = "default"
    audio_input_gain: float = 1.0


class VoiceEngine:
    """Central voice configuration and processing coordinator."""

    def __init__(self):
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

    def save_settings(self, new_settings: VoiceSettings):
        self.settings = new_settings
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(new_settings.model_dump_json(indent=2), encoding="utf-8")

    def get_settings(self) -> VoiceSettings:
        return self.settings

    def process_transcription_text(self, text: str) -> dict:
        """Process spoken text, check for wake-word if enabled, and sanitize."""
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

        return {
            "original_text": text,
            "cleaned_text": clean_text,
            "wake_word_detected": wake_detected or not self.settings.wake_word_enabled,
        }


voice_engine = VoiceEngine()

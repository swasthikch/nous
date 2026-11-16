"""Test Suite for NOUS Phase 5: Voice Assistant & Speech Pipeline.

Verifies:
1. VoiceSettings model validation and persistence (language, continuous loop, rate, pitch).
2. SpeechTextFormatter: Markdown stripping, code block replacement, currency expansion, concise phrasing.
3. Bilingual detection (English vs. Devanagari Hindi vs. Hinglish).
4. Wake-word detection and prompt processing through the Central AI Brain.
5. Audio payload transcription hook for local Whisper.
6. FastAPI Voice REST endpoints (/api/voice/settings, /format-speech, /process-speech, /transcribe-audio).
"""

import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.voice.engine import voice_engine, VoiceSettings
from backend.app.voice.formatter import speech_formatter, SpeechTextFormatter


async def run_phase5_voice_tests():
    print("=" * 72)
    print("  NOUS PHASE 5 — VOICE ASSISTANT & SPEECH PIPELINE VERIFICATION")
    print("=" * 72)

    # ---------------- 1. SETTINGS & PERSISTENCE ----------------
    print("\n[STEP 1] Testing Voice Settings & Configuration...")
    initial_settings = voice_engine.get_settings()
    assert initial_settings.speech_rate >= 0.5
    assert initial_settings.language in ("en-US", "en-IN", "hi-IN")

    # Update with bilingual and continuous loop settings
    test_settings = VoiceSettings(
        enabled=True,
        auto_speak=True,
        wake_word_enabled=True,
        wake_word="hey nous",
        language="hi-IN",
        speech_rate=1.1,
        speech_pitch=1.0,
        continuous_loop=True,
        concise_spoken_mode=True,
    )
    voice_engine.save_settings(test_settings)
    reloaded = voice_engine.get_settings()
    assert reloaded.language == "hi-IN"
    assert reloaded.continuous_loop is True
    assert reloaded.speech_rate == 1.1

    # Restore default language for subsequent tests
    test_settings.language = "en-US"
    test_settings.wake_word_enabled = False
    voice_engine.save_settings(test_settings)
    print("  [PASS] Voice settings schema, bilingual flags, and disk persistence confirmed.")

    # ---------------- 2. SPEECH TEXT FORMATTER ----------------
    print("\n[STEP 2] Testing Speech Text Formatter (Sanitization & Conciseness)...")
    sample_llm_markdown = (
        "### Calculation Result: [VERIFIED]\n"
        "Here is the breakdown of the calculation:\n"
        "| Item | Cost |\n"
        "| Laptop | $1200 |\n"
        "| Tax (18%) | ₹15000 |\n\n"
        "```python\ndef calculate(x, y):\n    return x * y\n```\n\n"
        "For more details, check [Documentation](https://nous.ai/docs). Total cost is $1416 or ₹118000 with 5% discount."
    )
    clean_speech = speech_formatter.clean_for_speech(sample_llm_markdown, max_words=60)
    assert "```" not in clean_speech, "Code block backticks not stripped!"
    assert "displayed the code on your screen" in clean_speech, "Code block placeholder missing!"
    assert "|" not in clean_speech, "Markdown table pipes not stripped!"
    assert "https://" not in clean_speech, "Raw URLs not removed!"
    assert "dollars" in clean_speech, "Currency symbol '$' not expanded to 'dollars'!"
    assert "rupees" in clean_speech, "Currency symbol '₹' not expanded to 'rupees'!"
    assert "percent" in clean_speech, "Percentage symbol '%' not expanded!"
    assert "VERIFIED" not in clean_speech, "Verification bracket tag not stripped!"
    print(f"  Clean Spoken Text Output:\n  \"{clean_speech}\"")
    print("  [PASS] Spoken dialogue formatter cleanly transforms complex markdown for TTS.")

    # ---------------- 3. BILINGUAL DETECTION (ENGLISH & HINDI) ----------------
    print("\n[STEP 3] Testing Bilingual Language Detection...")
    assert speech_formatter.detect_language("What is the current time and date?") == "en-US"
    assert speech_formatter.detect_language("Calculate 50 multiplied by 12") == "en-US"
    # Devanagari Hindi
    assert speech_formatter.detect_language("आज का मौसम कैसा है?") == "hi-IN"
    # Hinglish / Transliterated
    assert speech_formatter.detect_language("Namaste NOUS, kaise ho?") == "hi-IN"
    print("  [PASS] Bilingual detector correctly classifies English, Devanagari, and Hinglish.")

    # ---------------- 4. SPOKEN COMMAND EXECUTION THROUGH AI BRAIN ----------------
    print("\n[STEP 4] Testing Spoken Command Execution via AI Brain...")
    # Test a speech query with calculation
    proc = voice_engine.process_transcription_text("What is 25 * 4?")
    assert proc["wake_word_detected"] is True
    assert proc["cleaned_text"] == "What is 25 * 4?"

    # Test wake-word stripping when enabled
    voice_engine.settings.wake_word_enabled = True
    proc_wake = voice_engine.process_transcription_text("hey nous check my schedule")
    assert proc_wake["wake_word_detected"] is True
    assert proc_wake["cleaned_text"] == "check my schedule"
    voice_engine.settings.wake_word_enabled = False
    print("  [PASS] Transcription pre-processing & wake-word parsing verified.")

    # ---------------- 5. AUDIO TRANSCRIPTION HOOK ----------------
    print("\n[STEP 5] Testing Audio Payload Transcription Hook...")
    dummy_wav_bytes = b"RIFF....WAVEfmt ...."
    hook_res = await voice_engine.transcribe_audio_payload(dummy_wav_bytes, "test.wav")
    assert hook_res["success"] is True
    assert "engine" in hook_res
    print(f"  [PASS] Architectural hook for Whisper/Local STT verified (Active engine: {hook_res['engine']}).")

    # ---------------- 6. FASTAPI VOICE REST ENDPOINTS ----------------
    print("\n[STEP 6] Testing FastAPI Voice Endpoints (/api/voice)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. Get voice settings
        r_get = await client.get("/api/voice/settings")
        assert r_get.status_code == 200
        settings_data = r_get.json()
        assert "language" in settings_data

        # B. Test format-speech endpoint
        r_fmt = await client.post(
            "/api/voice/format-speech",
            json={"text": "Review commit [e410b](http://git) with $500 bonus in `main.py`.", "max_words": 40},
        )
        assert r_fmt.status_code == 200
        fmt_res = r_fmt.json()
        assert "500 dollars" in fmt_res["spoken_text"]

        # C. Test process-speech through live brain
        r_proc = await client.post(
            "/api/voice/process-speech",
            json={"speech_text": "Calculate 60 * 5", "session_id": "test_voice_session"},
        )
        assert r_proc.status_code == 200
        proc_data = r_proc.json()
        assert proc_data["processed"] is True
        assert "300" in proc_data["spoken_text"] or "300" in proc_data["ai_response"]["response"]

        # D. Test transcribe-audio upload (JSON base64 & raw binary)
        r_audio = await client.post(
            "/api/voice/transcribe-audio",
            json={"audio_base64": "UklGRg==", "filename": "audio.wav"},
        )
        assert r_audio.status_code == 200
        assert r_audio.json()["success"] is True

    print("  [PASS] FastAPI Voice endpoints (/settings, /format-speech, /process-speech, /transcribe-audio) 100% operational.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 5 VOICE ASSISTANT CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase5_voice_tests())

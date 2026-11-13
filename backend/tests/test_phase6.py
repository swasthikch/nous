"""Phase 6 Verification Suite for NOUS.

Tests:
1. Voice Engine Settings & Persistence
2. Wake-Word Processing & Sanitization
3. Speech Command Execution via Central AI Brain
4. Tool Integration through Spoken Queries
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.voice.engine import voice_engine, VoiceSettings
from backend.app.core.ai_engine import ai_brain
from backend.app.core.conversation import conversation_manager


async def run_phase6_tests():
    print("=" * 65)
    print("  NOUS PHASE 6 - VOICE ASSISTANT ENGINE & SPOKEN AI")
    print("=" * 65)

    all_passed = True

    # -------------------------------------------------------------
    # STEP 1: Voice Engine Settings
    # -------------------------------------------------------------
    print("\n[STEP 1] Testing Voice Engine Configuration & Persistence...")
    custom_settings = VoiceSettings(
        enabled=True,
        auto_speak=True,
        wake_word_enabled=True,
        wake_word="hey nous",
        speech_rate=1.1,
        speech_pitch=1.0,
    )
    voice_engine.save_settings(custom_settings)
    loaded = voice_engine.get_settings()

    if loaded.wake_word == "hey nous" and loaded.speech_rate == 1.1:
        print("  [PASS] Voice settings saved and reloaded successfully.")
    else:
        print("  [FAIL] Failed to persist voice settings.")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 2: Wake-Word Detection
    # -------------------------------------------------------------
    print("\n[STEP 2] Testing Wake-Word Detection & Cleaning...")
    # Case A: Valid wake-word prefix
    res_a = voice_engine.process_transcription_text("Hey NOUS, what is the current date?")
    print(f"  Input: 'Hey NOUS, what is the current date?'")
    print(f"  -> Wake detected: {res_a['wake_word_detected']}, Cleaned: '{res_a['cleaned_text']}'")
    if res_a["wake_word_detected"] and "what is the current date" in res_a["cleaned_text"].lower():
        print("  [PASS] Wake word detected and stripped cleanly.")
    else:
        print("  [FAIL] Wake word detection failed.")
        all_passed = False

    # Case B: Missing wake-word when enabled
    res_b = voice_engine.process_transcription_text("What is the weather outside?")
    print(f"  Input: 'What is the weather outside?'")
    print(f"  -> Wake detected: {res_b['wake_word_detected']}")
    if not res_b["wake_word_detected"]:
        print("  [PASS] Correctly rejected input missing required wake-word.")
    else:
        print("  [FAIL] Did not enforce wake-word.")
        all_passed = False

    # Disable wake-word for remaining tests
    voice_engine.save_settings(VoiceSettings(wake_word_enabled=False))

    # -------------------------------------------------------------
    # STEP 3: Spoken Tool Execution through AI Brain
    # -------------------------------------------------------------
    print("\n[STEP 3] Testing Spoken Queries with Tool Invocation...")
    session = conversation_manager.create_session("Voice Test Session")
    sid = session.id

    # Spoken Command 1: Datetime
    print("  --- Spoken Query 1: 'NOUS, tell me the exact date and time' ---")
    start1 = time.perf_counter()
    resp1 = await ai_brain.process(
        message="tell me the exact date and time",
        session_id=sid,
    )
    t1_elapsed = round(time.perf_counter() - start1, 2)
    print(f"  Response ({t1_elapsed}s): \"{resp1.response.strip()}\"")
    tools1 = [t.tool_name for t in resp1.tools_executed]
    print(f"  Tools Executed: {tools1}")

    if "get_current_datetime" in tools1:
        print("  [PASS] Spoken query triggered 'get_current_datetime' tool.")
    else:
        print("  [FAIL] Failed to trigger datetime tool.")
        all_passed = False

    # Spoken Command 2: Calculation
    print("\n  --- Spoken Query 2: 'Calculate 800 divided by 4' ---")
    start2 = time.perf_counter()
    resp2 = await ai_brain.process(
        message="Calculate 800 / 4",
        session_id=sid,
    )
    t2_elapsed = round(time.perf_counter() - start2, 2)
    print(f"  Response ({t2_elapsed}s): \"{resp2.response.strip()}\"")
    tools2 = [t.tool_name for t in resp2.tools_executed]
    print(f"  Tools Executed: {tools2}")

    if "calculate" in tools2 and "200" in resp2.response:
        print("  [PASS] Spoken calculation query evaluated to 200.")
    else:
        print("  [FAIL] Failed spoken calculation.")
        all_passed = False

    # Clean up test session
    conversation_manager.delete_session(sid)
    print(f"\n  Cleaned up temporary test session: {sid}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    if all_passed:
        print("  [SUCCESS] ALL PHASE 6 VOICE ENGINE TESTS PASSED!")
    else:
        print("  [FAILURE] SOME PHASE 6 VOICE TESTS FAILED.")
    print("=" * 65)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_phase6_tests())
    sys.exit(0 if success else 1)

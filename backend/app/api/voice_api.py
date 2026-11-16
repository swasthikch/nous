"""Voice Assistant API Endpoints for NOUS (Phase 5)."""

import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.voice.engine import voice_engine, VoiceSettings
from backend.app.voice.formatter import speech_formatter
from backend.app.core.ai_engine import ai_brain, AIEngineResponse

router = APIRouter(prefix="/api/voice", tags=["voice"])


class ProcessSpeechRequest(BaseModel):
    speech_text: str = Field(..., description="Transcribed speech input from user")
    session_id: Optional[str] = Field(None, description="Optional active session ID")


class FormatSpeechRequest(BaseModel):
    text: str = Field(..., description="Raw markdown or technical text to clean for speech")
    max_words: int = Field(default=55, ge=10, le=200)


@router.get("/settings")
async def get_voice_settings():
    """Retrieve voice assistant configuration."""
    return voice_engine.get_settings().model_dump()


@router.post("/settings")
async def update_voice_settings(settings: VoiceSettings):
    """Update voice assistant configuration (rate, pitch, language, wake-word, loop)."""
    voice_engine.save_settings(settings)
    return {"success": True, "settings": voice_engine.get_settings().model_dump()}


@router.post("/format-speech")
async def format_speech_text(request: FormatSpeechRequest):
    """Clean markdown, tables, and code snippets into concise spoken text."""
    spoken = speech_formatter.clean_for_speech(request.text, max_words=request.max_words)
    lang = speech_formatter.detect_language(request.text)
    return {
        "original_length": len(request.text),
        "spoken_text": spoken,
        "detected_language": lang,
    }


@router.post("/process-speech")
async def process_speech(request: ProcessSpeechRequest):
    """Process a transcribed spoken command through wake-word verification and AI Brain."""
    if not request.speech_text.strip():
        raise HTTPException(status_code=400, detail="Speech text cannot be empty.")

    proc_result = voice_engine.process_transcription_text(request.speech_text)

    # If wake-word is required but was not present in the phrase
    if voice_engine.settings.wake_word_enabled and not proc_result["wake_word_detected"]:
        return {
            "processed": False,
            "wake_word_detected": False,
            "message": f"Wake word '{voice_engine.settings.wake_word}' not detected.",
            "response": None,
        }

    user_query = proc_result["cleaned_text"]
    if not user_query:
        greeting = "हाँ, मैं सुन रहा हूँ। मैं आपकी क्या मदद कर सकता हूँ?" if proc_result["detected_language"] == "hi-IN" else "Yes, I am listening. How can I assist you?"
        return {
            "processed": True,
            "wake_word_detected": True,
            "message": "Wake word recognized. Ready for command.",
            "response": greeting,
            "spoken_text": greeting,
            "detected_language": proc_result["detected_language"],
        }

    # Execute through Central AI Brain
    ai_response: AIEngineResponse = await ai_brain.process(
        message=user_query,
        session_id=request.session_id,
    )

    # Format response for natural speech synthesis
    clean_spoken = voice_engine.format_spoken_response(ai_response.response)

    return {
        "processed": True,
        "wake_word_detected": True,
        "query": user_query,
        "ai_response": ai_response.model_dump(),
        "spoken_text": clean_spoken,
        "detected_language": proc_result["detected_language"],
        "session_id": ai_response.session_id,
    }


@router.post("/transcribe-audio")
async def transcribe_audio(request: Request):
    """Architectural hook for local Whisper STT processing of audio chunks."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        b64_str = body.get("audio_base64", "")
        raw_bytes = base64.b64decode(b64_str) if b64_str else b""
        filename = body.get("filename", "speech.wav")
    else:
        raw_bytes = await request.body()
        filename = "speech.wav"

    result = await voice_engine.transcribe_audio_payload(raw_bytes, filename=filename)
    return result

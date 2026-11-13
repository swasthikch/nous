"""Voice Assistant API Endpoints for NOUS."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.voice.engine import voice_engine, VoiceSettings
from backend.app.core.ai_engine import ai_brain, AIEngineResponse

router = APIRouter(prefix="/api/voice", tags=["voice"])


class ProcessSpeechRequest(BaseModel):
    speech_text: str = Field(..., description="Transcribed speech input from user")
    session_id: Optional[str] = Field(None, description="Optional active session ID")


@router.get("/settings")
async def get_voice_settings():
    """Retrieve voice assistant configuration."""
    return voice_engine.get_settings().model_dump()


@router.post("/settings")
async def update_voice_settings(settings: VoiceSettings):
    """Update voice assistant configuration (rate, pitch, wake-word, auto-speak)."""
    voice_engine.save_settings(settings)
    return {"success": True, "settings": voice_engine.get_settings().model_dump()}


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
        return {
            "processed": True,
            "wake_word_detected": True,
            "message": "Wake word recognized. Ready for command.",
            "response": "Yes, I am listening. How can I assist you?",
        }

    # Execute through Central AI Brain
    ai_response: AIEngineResponse = await ai_brain.process(
        message=user_query,
        session_id=request.session_id,
    )

    return {
        "processed": True,
        "wake_word_detected": True,
        "query": user_query,
        "ai_response": ai_response.model_dump(),
        "spoken_text": ai_response.response,
        "session_id": ai_response.session_id,
    }

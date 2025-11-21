"""
Audio Router - Handles speech-to-text and text-to-speech operations
"""
import os
import base64
import time
import logging
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, Request, HTTPException, Form
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

from app.services.metrics_logger import MetricsLogger

load_dotenv()

# Initialize router
audio_router = APIRouter(prefix="/api/audio", tags=["audio"])

# Initialize logger
logger = logging.getLogger(__name__)
metrics_logger = MetricsLogger()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY environment variable not set")
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = openai.OpenAI(api_key=api_key)

class TTSRequest(BaseModel):
    """Text-to-speech request model"""
    text: str
    voice: str = "alloy"
    speed: float = 1.0

class TranscriptionResponse(BaseModel):
    """Speech-to-text response model"""
    text: str
    duration_ms: float
    confidence: float = 1.0

@audio_router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe audio file using OpenAI Whisper
    
    Args:
        audio_file: Audio file to transcribe
        
    Returns:
        Transcribed text with metrics
    """
    start_time = time.time()
    temp_file_path = None
    
    try:
        # Validate file type
        allowed_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        file_ext = Path(audio_file.filename).suffix.lower()
        
        if file_ext not in allowed_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported audio format. Allowed formats: {', '.join(allowed_formats)}"
            )
        
        # Read file content
        contents = await audio_file.read()
        
        # Log file size
        file_size_mb = len(contents) / (1024 * 1024)
        logger.info(f"Processing audio file: {audio_file.filename} ({file_size_mb:.2f} MB)")
        
        # Save to temporary file
        temp_file_path = f"temp/temp_{int(time.time())}_{audio_file.filename}"
        Path("temp").mkdir(exist_ok=True)
        
        with open(temp_file_path, "wb") as f:
            f.write(contents)
        
        # Transcribe with Whisper
        stt_start = time.time()
        with open(temp_file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        stt_duration = (time.time() - stt_start) * 1000
        
        # Log metrics
        total_duration = (time.time() - start_time) * 1000
        metrics_logger.log_stt_metrics(
            duration_ms=stt_duration,
            file_size_mb=file_size_mb,
            text_length=len(transcript)
        )
        
        logger.info(f"Transcription completed in {stt_duration:.2f}ms")
        
        return TranscriptionResponse(
            text=transcript,
            duration_ms=stt_duration,
            confidence=1.0
        )
        
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {str(e)}")

@audio_router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using OpenAI TTS
    
    Args:
        request: TTS request with text and voice settings
        
    Returns:
        Base64 encoded audio data with metrics
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        if len(request.text) > 4096:
            raise HTTPException(status_code=400, detail="Text too long (max 4096 characters)")
        
        # Available voices
        available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if request.voice not in available_voices:
            request.voice = "alloy"
        
        logger.info(f"Generating speech for {len(request.text)} characters with voice: {request.voice}")
        
        # Generate speech
        tts_start = time.time()
        response = client.audio.speech.create(
            model="tts-1",
            input=request.text,
            voice=request.voice,
            speed=request.speed
        )
        tts_duration = (time.time() - tts_start) * 1000
        
        # Convert to base64
        audio_content = response.content
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Calculate audio size
        audio_size_kb = len(audio_content) / 1024
        
        # Log metrics
        metrics_logger.log_tts_metrics(
            duration_ms=tts_duration,
            text_length=len(request.text),
            audio_size_kb=audio_size_kb
        )
        
        logger.info(f"Speech generation completed in {tts_duration:.2f}ms, size: {audio_size_kb:.2f}KB")
        
        return {
            "audio": audio_base64,
            "format": "mp3",
            "duration_ms": tts_duration,
            "size_kb": audio_size_kb
        }
        
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@audio_router.get("/voices")
async def get_available_voices():
    """Get list of available TTS voices"""
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy", "gender": "neutral", "description": "Neutral and balanced"},
            {"id": "echo", "name": "Echo", "gender": "male", "description": "Smooth and articulate"},
            {"id": "fable", "name": "Fable", "gender": "neutral", "description": "Expressive and dynamic"},
            {"id": "onyx", "name": "Onyx", "gender": "male", "description": "Deep and authoritative"},
            {"id": "nova", "name": "Nova", "gender": "female", "description": "Warm and friendly"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female", "description": "Clear and vibrant"}
        ],
        "default": "alloy"
    }

@audio_router.get("/metrics")
async def get_audio_metrics():
    """Get audio processing metrics"""
    return metrics_logger.get_audio_metrics()

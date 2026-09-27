"""
Whisper Transcription Service - OpenAI Whisper API integration
"""
from datetime import datetime
from typing import Optional
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from config import settings
from models import Recording, Transcript, TranscriptionStatus

logger = logging.getLogger(__name__)

# Whisper API pricing: $0.006 per minute of audio
WHISPER_COST_PER_MINUTE = 0.006

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class WhisperService:
    """Service for transcribing audio recordings using OpenAI Whisper"""

    @staticmethod
    def transcribe_audio(file_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe an audio file with the Whisper API

        Args:
            file_path: Path to the audio file on disk
            language: Optional ISO-639-1 language hint (e.g. "he")

        Returns:
            Dict with text, language, duration_seconds
        """
        with open(file_path, "rb") as audio_file:
            kwargs = {
                "model": settings.OPENAI_MODEL_WHISPER,
                "file": audio_file,
                "response_format": "verbose_json",
            }
            if language:
                kwargs["language"] = language

            response = client.audio.transcriptions.create(**kwargs)

        return {
            "text": response.text,
            "language": getattr(response, "language", language),
            "duration_seconds": int(getattr(response, "duration", 0) or 0),
        }

    @staticmethod
    def process_recording(
        db: Session,
        recording_id: str,
        file_path: str,
        language: Optional[str] = None,
    ) -> Optional[Transcript]:
        """
        Transcribe a recording and store the result

        Args:
            db: Database session
            recording_id: Recording ID
            file_path: Path to the audio file on disk
            language: Optional language hint

        Returns:
            Transcript object if successful, None otherwise
        """
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            logger.error(f"Recording not found: {recording_id}")
            return None

        recording.transcription_status = TranscriptionStatus.PROCESSING
        db.commit()

        try:
            start_time = datetime.utcnow()
            result = WhisperService.transcribe_audio(file_path, language)
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            duration_minutes = result["duration_seconds"] / 60
            cost = duration_minutes * WHISPER_COST_PER_MINUTE

            transcript = Transcript(
                recording_id=recording_id,
                text=result["text"],
                language=result["language"],
                api_cost=cost,
                processing_time_seconds=int(processing_time),
            )
            db.add(transcript)

            recording.language = result["language"]
            recording.duration_seconds = result["duration_seconds"]
            recording.transcription_status = TranscriptionStatus.COMPLETED
            recording.transcribed_at = datetime.utcnow()

            db.commit()
            db.refresh(transcript)

            logger.info(f"Transcription completed for recording {recording_id}")
            return transcript

        except Exception as e:
            logger.error(f"Transcription failed for recording {recording_id}: {e}")
            recording.transcription_status = TranscriptionStatus.FAILED
            db.commit()
            return None


# Create service instance
whisper_service = WhisperService()

"""
GPT Summarization Service - OpenAI GPT-4 integration
"""
from openai import OpenAI
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from models import Recording, Transcript, Summary, Template
from config import settings
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


class GPTService:
    """Service for summarizing transcripts using OpenAI GPT-4"""

    @staticmethod
    def summarize_transcript(
        transcript_text: str,
        template: Template,
        context: Optional[Dict] = None
    ) -> tuple[str, float]:
        """
        Summarize a transcript using GPT-4 with template instructions

        Args:
            transcript_text: The transcript to summarize
            template: Template object with system/user prompts
            context: Optional context data (e.g., meeting date, participants)

        Returns:
            Tuple of (summary_text, cost_usd)
        """
        try:
            logger.info(f"Starting summarization with template: {template.name}")

            # Prepare user prompt with transcript
            user_prompt = template.user_prompt_template.replace(
                "{transcript}",
                transcript_text
            )

            # Add context if provided
            if context:
                for key, value in context.items():
                    placeholder = f"{{{key}}}"
                    user_prompt = user_prompt.replace(placeholder, str(value))

            # Call GPT-4
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL_SUMMARY,
                messages=[
                    {
                        "role": "system",
                        "content": template.system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.5,  # Balanced creativity and consistency
                max_tokens=2000,
            )

            # Extract summary
            summary_text = response.choices[0].message.content

            # Calculate cost
            # Approximate pricing: $0.01 per 1K input tokens, $0.03 per 1K output tokens
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            input_cost = (input_tokens / 1000) * 0.01
            output_cost = (output_tokens / 1000) * 0.03
            total_cost = input_cost + output_cost

            logger.info(f"Summarization completed. Cost: ${total_cost:.4f}")
            return summary_text, total_cost

        except Exception as e:
            logger.error(f"GPT summarization failed: {e}")
            raise

    @staticmethod
    def process_recording_summary(
        db: Session,
        recording_id: str,
        template_id: str,
        context: Optional[Dict] = None
    ) -> Optional[Summary]:
        """
        Process a recording: transcribe + summarize + store result

        Args:
            db: Database session
            recording_id: Recording ID
            template_id: Template ID
            context: Optional context data

        Returns:
            Summary object if successful, None otherwise
        """
        try:
            # Get recording
            recording = db.query(Recording).filter(
                Recording.id == recording_id
            ).first()

            if not recording:
                logger.error(f"Recording not found: {recording_id}")
                return None

            # Get transcript
            transcript = recording.transcript
            if not transcript:
                logger.error(f"No transcript found for recording {recording_id}")
                return None

            # Get template
            template = db.query(Template).filter(
                Template.id == template_id,
                Template.is_active == True
            ).first()

            if not template:
                logger.error(f"Template not found: {template_id}")
                return None

            # Prepare context
            if context is None:
                context = {
                    "date": recording.created_at.strftime("%Y-%m-%d"),
                    "duration": transcript.processing_time_seconds or 0,
                    "language": transcript.language or "unknown"
                }

            # Summarize
            start_time = datetime.utcnow()
            summary_text, cost = GPTService.summarize_transcript(
                transcript.text,
                template,
                context
            )
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Create summary record
            summary = Summary(
                recording_id=recording_id,
                template_id=template_id,
                summary_text=summary_text,
                api_cost=cost,
                processing_time_seconds=int(processing_time),
                model_used=settings.OPENAI_MODEL_SUMMARY
            )

            # Save to database
            db.add(summary)
            db.commit()
            db.refresh(summary)

            logger.info(f"Summary created for recording {recording_id}")
            return summary

        except Exception as e:
            logger.error(f"Failed to process summary for {recording_id}: {e}")
            return None

    @staticmethod
    def batch_summarize(
        db: Session,
        recording_ids: List[str],
        template_id: str,
        context: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Summarize multiple recordings with same template

        Args:
            db: Database session
            recording_ids: List of recording IDs
            template_id: Template ID
            context: Optional context data

        Returns:
            Dict with recording_id -> success mapping
        """
        results = {}

        for recording_id in recording_ids:
            try:
                summary = GPTService.process_recording_summary(
                    db,
                    recording_id,
                    template_id,
                    context
                )
                results[recording_id] = summary is not None
            except Exception as e:
                logger.error(f"Batch summarization failed for {recording_id}: {e}")
                results[recording_id] = False

        return results


# Create service instance
gpt_service = GPTService()

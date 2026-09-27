"""
Summary Management Routes - Create, retrieve, and manage summaries
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
import io

from database import get_db
from models import User, Recording, Summary
from routes.auth import get_current_user
from services.gpt import gpt_service
from services.document_generator import document_generator
from schemas import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/summaries",
    tags=["summaries"],
    responses={404: {"model": ErrorResponse}}
)


@router.post("/")
async def create_summary(
    recording_id: str,
    template_id: str,
    context: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Create summary from recording using specified template

    Args:
        recording_id: Recording to summarize
        template_id: Template to use for summarization
        context: Optional context data (date, participants, etc.)

    Returns:
        Created summary object with text and metadata
    """
    try:
        # Verify recording exists and belongs to user
        recording = db.query(Recording).filter(
            Recording.id == recording_id,
            Recording.user_id == current_user.id,
            Recording.deleted_at.is_(None)
        ).first()

        if not recording:
            logger.warning(f"User {current_user.id} attempted to access non-existent recording {recording_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recording not found: {recording_id}"
            )

        # Check if recording has transcript
        if not recording.transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recording has no transcript yet. Transcribe first."
            )

        # Check if summary already exists with this template
        existing_summary = db.query(Summary).filter(
            Summary.recording_id == recording_id,
            Summary.template_id == template_id
        ).first()

        if existing_summary:
            logger.info(f"Summary already exists for recording {recording_id} with template {template_id}")
            return {
                "id": str(existing_summary.id),
                "recording_id": str(existing_summary.recording_id),
                "template_id": str(existing_summary.template_id),
                "summary_text": existing_summary.summary_text,
                "api_cost": float(existing_summary.api_cost),
                "processing_time_seconds": existing_summary.processing_time_seconds,
                "model_used": existing_summary.model_used,
                "created_at": existing_summary.created_at.isoformat()
            }

        # Create summary
        summary = gpt_service.process_recording_summary(
            db,
            recording_id,
            template_id,
            context
        )

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create summary"
            )

        logger.info(f"User {current_user.id} created summary for recording {recording_id}")

        return {
            "id": str(summary.id),
            "recording_id": str(summary.recording_id),
            "template_id": str(summary.template_id),
            "summary_text": summary.summary_text,
            "api_cost": float(summary.api_cost),
            "processing_time_seconds": summary.processing_time_seconds,
            "model_used": summary.model_used,
            "created_at": summary.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create summary for recording {recording_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create summary"
        )


@router.get("/")
async def list_summaries(
    recording_id: Optional[str] = None,
    template_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    List summaries for current user (filtered by recording or template)

    Query Parameters:
    - recording_id: Filter by recording (optional)
    - template_id: Filter by template (optional)
    - limit: Number of results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)

    Returns:
        Paginated list of summaries
    """
    try:
        # Start with summaries for user's recordings
        query = db.query(Summary).join(Recording).filter(
            Recording.user_id == current_user.id,
            Recording.deleted_at.is_(None)
        )

        # Apply filters
        if recording_id:
            query = query.filter(Summary.recording_id == recording_id)

        if template_id:
            query = query.filter(Summary.template_id == template_id)

        # Get total count
        total = query.count()

        # Get paginated results
        summaries = query.order_by(Summary.created_at.desc()).offset(offset).limit(limit).all()

        logger.info(f"User {current_user.id} listed {len(summaries)} summaries")

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "summaries": [
                {
                    "id": str(s.id),
                    "recording_id": str(s.recording_id),
                    "template_id": str(s.template_id),
                    "summary_text": s.summary_text[:500] + "..." if len(s.summary_text) > 500 else s.summary_text,  # Preview
                    "api_cost": float(s.api_cost),
                    "processing_time_seconds": s.processing_time_seconds,
                    "model_used": s.model_used,
                    "created_at": s.created_at.isoformat()
                }
                for s in summaries
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list summaries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list summaries"
        )


@router.get("/{summary_id}")
async def get_summary(
    summary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get summary by ID (must own the recording)

    Returns:
        Full summary object with complete text
    """
    try:
        summary = db.query(Summary).join(Recording).filter(
            Summary.id == summary_id,
            Recording.user_id == current_user.id
        ).first()

        if not summary:
            logger.warning(f"User {current_user.id} attempted to access summary {summary_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Summary not found: {summary_id}"
            )

        logger.info(f"User {current_user.id} retrieved summary {summary_id}")

        return {
            "id": str(summary.id),
            "recording_id": str(summary.recording_id),
            "template_id": str(summary.template_id),
            "summary_text": summary.summary_text,
            "api_cost": float(summary.api_cost),
            "processing_time_seconds": summary.processing_time_seconds,
            "model_used": summary.model_used,
            "created_at": summary.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summary {summary_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get summary"
        )


@router.get("/{summary_id}/download")
async def download_summary(
    summary_id: str,
    format: str = Query("txt", regex="^(txt|pdf|docx|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download summary in specified format

    Query Parameters:
    - format: Output format (txt, pdf, docx, xlsx) - default: txt

    Returns:
        Binary file content with appropriate MIME type
    """
    try:
        summary = db.query(Summary).join(Recording).filter(
            Summary.id == summary_id,
            Recording.user_id == current_user.id
        ).first()

        if not summary:
            logger.warning(f"User {current_user.id} attempted to access summary {summary_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Summary not found: {summary_id}"
            )

        # Get recording for context
        recording = db.query(Recording).filter(Recording.id == summary.recording_id).first()

        # Prepare summary data
        summary_data = {
            "summary_text": summary.summary_text,
            "date": recording.created_at.strftime("%Y-%m-%d") if recording else None,
            "duration": recording.duration_seconds if recording else None,
            "language": recording.language if recording else None
        }

        # Generate document
        document_buffer = document_generator.generate_document(
            format,
            "סיכום הקלטה",
            summary_data
        )

        # Determine MIME type
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "txt": "text/plain"
        }

        # Determine file extension
        extensions = {
            "pdf": "pdf",
            "docx": "docx",
            "xlsx": "xlsx",
            "txt": "txt"
        }

        logger.info(f"User {current_user.id} downloaded summary {summary_id} as {format}")

        return StreamingResponse(
            iter([document_buffer.getvalue()]),
            media_type=mime_types.get(format, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="summary_{summary_id[:8]}.{extensions.get(format, "bin")}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download summary {summary_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download summary"
        )


@router.post("/{summary_id}/delete")
async def delete_summary(
    summary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Delete summary (soft delete - just mark as deleted)

    Args:
        summary_id: Summary to delete

    Returns:
        Success message
    """
    try:
        summary = db.query(Summary).join(Recording).filter(
            Summary.id == summary_id,
            Recording.user_id == current_user.id
        ).first()

        if not summary:
            logger.warning(f"User {current_user.id} attempted to delete summary {summary_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Summary not found: {summary_id}"
            )

        # Soft delete by setting deleted_at
        summary.deleted_at = datetime.utcnow()
        db.commit()

        logger.info(f"User {current_user.id} deleted summary {summary_id}")

        return {
            "message": "Summary deleted successfully",
            "summary_id": summary_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete summary {summary_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete summary"
        )


@router.post("/batch/create")
async def batch_create_summaries(
    recording_ids: List[str],
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Create summaries for multiple recordings with same template

    Args:
        recording_ids: List of recording IDs to summarize
        template_id: Template to use for all summaries

    Returns:
        Dict of recording_id -> success status and summary_id
    """
    try:
        results = {}

        for recording_id in recording_ids:
            # Verify recording belongs to user
            recording = db.query(Recording).filter(
                Recording.id == recording_id,
                Recording.user_id == current_user.id,
                Recording.deleted_at.is_(None)
            ).first()

            if not recording:
                results[recording_id] = {
                    "success": False,
                    "error": "Recording not found or doesn't belong to user"
                }
                continue

            if not recording.transcript:
                results[recording_id] = {
                    "success": False,
                    "error": "Recording has no transcript"
                }
                continue

            try:
                summary = gpt_service.process_recording_summary(
                    db,
                    recording_id,
                    template_id
                )

                if summary:
                    results[recording_id] = {
                        "success": True,
                        "summary_id": str(summary.id),
                        "api_cost": float(summary.api_cost)
                    }
                else:
                    results[recording_id] = {
                        "success": False,
                        "error": "Failed to create summary"
                    }

            except Exception as e:
                logger.error(f"Batch summarization failed for {recording_id}: {e}")
                results[recording_id] = {
                    "success": False,
                    "error": str(e)
                }

        # Calculate totals
        successful = sum(1 for r in results.values() if r.get("success"))
        total_cost = sum(
            r.get("api_cost", 0) for r in results.values() if r.get("success")
        )

        logger.info(f"User {current_user.id} batch created {successful}/{len(recording_ids)} summaries")

        return {
            "total_requested": len(recording_ids),
            "total_successful": successful,
            "total_cost": total_cost,
            "results": results
        }

    except Exception as e:
        logger.error(f"Batch summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch summarization failed"
        )

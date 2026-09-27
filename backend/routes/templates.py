"""
Template Management Routes - CRUD operations for summarization templates
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import get_db
from models import User
from routes.auth import get_current_user
from services.template import template_service
from schemas import TemplateResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/templates",
    tags=["templates"],
    responses={404: {"model": ErrorResponse}}
)


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to check if user is admin"""
    if current_user.role != "admin":
        logger.warning(f"User {current_user.id} attempted admin action without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


@router.get("/")
async def list_templates(
    active_only: bool = True,
    output_format: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    List all templates (available to all authenticated users)

    Query Parameters:
    - active_only: Only return active templates (default: true)
    - output_format: Filter by output format (pdf, docx, xlsx, txt)

    Returns:
        List of template objects
    """
    try:
        templates = template_service.list_templates(
            db,
            active_only=active_only,
            output_format=output_format
        )

        logger.info(f"User {current_user.id} listed {len(templates)} templates")

        return {
            "total": len(templates),
            "templates": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "description": t.description,
                    "output_format": t.output_format,
                    "is_active": t.is_active,
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None
                }
                for t in templates
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get template by ID (available to all authenticated users)

    Returns:
        Template object with prompts and configuration
    """
    try:
        template = template_service.get_template(db, template_id)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        logger.info(f"User {current_user.id} retrieved template {template_id}")

        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt_template": template.user_prompt_template,
            "output_format": template.output_format,
            "is_active": template.is_active,
            "created_by": str(template.created_by) if template.created_by else None,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )


@router.post("/")
async def create_template(
    name: str,
    description: str,
    system_prompt: str,
    user_prompt_template: str,
    output_format: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
) -> dict:
    """
    Create new template (admin only)

    Args:
        name: Template name (must be unique)
        description: Template description
        system_prompt: System instructions for GPT
        user_prompt_template: User prompt with {transcript} placeholder
        output_format: Output format (txt, pdf, docx, xlsx)

    Returns:
        Created template object
    """
    try:
        template = template_service.create_template(
            db,
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            output_format=output_format,
            created_by_user_id=str(admin_user.id)
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create template (possibly duplicate name)"
            )

        logger.info(f"Admin {admin_user.id} created template: {name}")

        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "output_format": template.output_format,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_prompt_template: Optional[str] = None,
    output_format: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
) -> dict:
    """
    Update template (admin only)

    Args:
        template_id: Template ID to update
        name: New template name
        description: New description
        system_prompt: New system prompt
        user_prompt_template: New user prompt template
        output_format: New output format
        is_active: Active status

    Returns:
        Updated template object
    """
    try:
        # Build update dict with only provided fields
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if system_prompt is not None:
            update_data["system_prompt"] = system_prompt
        if user_prompt_template is not None:
            update_data["user_prompt_template"] = user_prompt_template
        if output_format is not None:
            update_data["output_format"] = output_format
        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update"
            )

        template = template_service.update_template(
            db,
            template_id,
            **update_data
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        logger.info(f"Admin {admin_user.id} updated template {template_id}")

        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "output_format": template.output_format,
            "is_active": template.is_active,
            "updated_at": template.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
) -> dict:
    """
    Delete template (soft delete - admin only)

    Args:
        template_id: Template ID to delete

    Returns:
        Success message
    """
    try:
        success = template_service.delete_template(db, template_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        logger.info(f"Admin {admin_user.id} deleted template {template_id}")

        return {
            "message": f"Template deleted successfully",
            "template_id": template_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.post("/seed/default")
async def seed_default_templates(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
) -> dict:
    """
    Seed default Hebrew templates (admin only)

    Creates 5 default templates if they don't already exist:
    - סיכום קצר (Short summary)
    - סיכום מפורט (Detailed summary)
    - פעולות נדרשות (Action items)
    - סיכום עם הערות כלכליות (Financial summary)
    - דוח טכני (Technical report)

    Returns:
        Number of templates created
    """
    try:
        count = template_service.seed_default_templates(
            db,
            admin_user_id=str(admin_user.id)
        )

        logger.info(f"Admin {admin_user.id} seeded {count} default templates")

        return {
            "message": f"Seeded {count} default templates",
            "count": count,
            "templates": [
                "סיכום קצר",
                "סיכום מפורט",
                "פעולות נדרשות",
                "סיכום עם הערות כלכליות",
                "דוח טכני"
            ]
        }

    except Exception as e:
        logger.error(f"Failed to seed default templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to seed templates"
        )

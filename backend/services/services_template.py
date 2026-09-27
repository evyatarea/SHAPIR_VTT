"""
Template Management Service - CRUD operations for summarization templates
"""
from sqlalchemy.orm import Session
from models import Template, User
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing summarization templates"""

    @staticmethod
    def create_template(
        db: Session,
        name: str,
        description: str,
        system_prompt: str,
        user_prompt_template: str,
        output_format: str,
        created_by_user_id: str
    ) -> Optional[Template]:
        """
        Create a new template

        Args:
            db: Database session
            name: Template name (unique)
            description: Template description
            system_prompt: System instructions for GPT
            user_prompt_template: User prompt with {transcript} placeholder
            output_format: Output format (txt, pdf, docx, xlsx)
            created_by_user_id: User ID who created this template

        Returns:
            Template object if successful, None otherwise
        """
        try:
            # Check if name already exists
            existing = db.query(Template).filter(
                Template.name == name
            ).first()

            if existing:
                logger.warning(f"Template with name '{name}' already exists")
                return None

            # Validate output format
            valid_formats = ["txt", "pdf", "docx", "xlsx"]
            if output_format not in valid_formats:
                logger.error(f"Invalid output format: {output_format}")
                return None

            # Validate placeholders
            if "{transcript}" not in user_prompt_template:
                logger.warning(f"Template prompt missing {{transcript}} placeholder")

            # Create template
            template = Template(
                name=name,
                description=description,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                output_format=output_format,
                is_active=True,
                created_by=created_by_user_id
            )

            db.add(template)
            db.commit()
            db.refresh(template)

            logger.info(f"Template created: {name} by user {created_by_user_id}")
            return template

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            db.rollback()
            return None

    @staticmethod
    def get_template(db: Session, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        return db.query(Template).filter(
            Template.id == template_id,
            Template.is_active == True
        ).first()

    @staticmethod
    def list_templates(
        db: Session,
        active_only: bool = True,
        output_format: Optional[str] = None
    ) -> List[Template]:
        """
        List templates with optional filtering

        Args:
            db: Database session
            active_only: Only return active templates
            output_format: Filter by output format

        Returns:
            List of Template objects
        """
        query = db.query(Template)

        if active_only:
            query = query.filter(Template.is_active == True)

        if output_format:
            query = query.filter(Template.output_format == output_format)

        return query.order_by(Template.created_at.desc()).all()

    @staticmethod
    def update_template(
        db: Session,
        template_id: str,
        **kwargs
    ) -> Optional[Template]:
        """
        Update template fields

        Args:
            db: Database session
            template_id: Template ID
            **kwargs: Fields to update (name, description, system_prompt, etc.)

        Returns:
            Updated Template object if successful, None otherwise
        """
        try:
            template = db.query(Template).filter(
                Template.id == template_id
            ).first()

            if not template:
                logger.error(f"Template not found: {template_id}")
                return None

            # Update allowed fields
            allowed_fields = {
                "name", "description", "system_prompt",
                "user_prompt_template", "output_format", "is_active"
            }

            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == "name":
                        # Check name uniqueness
                        existing = db.query(Template).filter(
                            Template.name == value,
                            Template.id != template_id
                        ).first()
                        if existing:
                            logger.warning(f"Template name '{value}' already exists")
                            continue

                    setattr(template, field, value)

            template.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(template)

            logger.info(f"Template updated: {template_id}")
            return template

        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            db.rollback()
            return None

    @staticmethod
    def delete_template(db: Session, template_id: str) -> bool:
        """
        Soft delete template (set is_active to False)

        Args:
            db: Database session
            template_id: Template ID

        Returns:
            True if successful, False otherwise
        """
        try:
            template = db.query(Template).filter(
                Template.id == template_id
            ).first()

            if not template:
                logger.error(f"Template not found: {template_id}")
                return False

            template.is_active = False
            template.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Template deleted (soft): {template_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            db.rollback()
            return False

    @staticmethod
    def get_default_templates() -> Dict[str, Dict]:
        """
        Get default templates for Shapir

        Returns:
            Dict of default template configurations
        """
        return {
            "short_summary": {
                "name": "סיכום קצר",
                "description": "סיכום קצר של השיחה (1-2 פסקאות)",
                "system_prompt": """אתה עוזר מקצועי לסיכום פגישות עבודה.
סכם את השיחה בצורה תמציתית וברורה.
השתמש בעברית נקייה ומדויקת.
התמקד בנקודות המרכזיות בלבד.""",
                "user_prompt_template": """סכם את השיחה הבאה בסיכום קצר של 1-2 פסקאות:

{transcript}

סיכום:""",
                "output_format": "txt"
            },
            "detailed_summary": {
                "name": "סיכום מפורט",
                "description": "סיכום מפורט של כל נקודה בשיחה",
                "system_prompt": """אתה עוזר מקצועי לסיכום פגישות.
סכם את השיחה בפרטים מלאים.
סדר את הנקודות בצורה לוגית.
השתמש בעברית מקצועית.""",
                "user_prompt_template": """סכם את השיחה הבאה בפירוט מלא, בהפרדה לנושאים:

{transcript}

סיכום מפורט:""",
                "output_format": "txt"
            },
            "action_items": {
                "name": "פעולות נדרשות",
                "description": "רשימת הפעולות הנדרשות וגורמים אחראים",
                "system_prompt": """אתה עוזר למיצוי פעולות מפגישות עבודה.
זהה את כל המשימות, אחראים וזמנים.
תן רשימה ברורה ופעלה.""",
                "user_prompt_template": """זהה את כל הפעולות הנדרשות בשיחה הבאה.
לכל פעולה, ציין: גורם אחראי, תאריך יעד, עדיפות

{transcript}

פעולות נדרשות:""",
                "output_format": "txt"
            },
            "financial_summary": {
                "name": "סיכום עם הערות כלכליות",
                "description": "סיכום עם דגש על היבטים כלכליים ומספרים",
                "system_prompt": """אתה עוזר לנתחון כלכלי של פגישות.
זהה את כל המספרים, תקציבים, עלויות, הוצאות.
כלול ניתוח כלכלי בסיכום.""",
                "user_prompt_template": """סכם את השיחה עם דגש על היבטים כלכליים:
- מספרים ותקציבים שהוזכרו
- התחייבויות כלכליות
- סיכונים כלכליים

{transcript}

סיכום כלכלי:""",
                "output_format": "txt"
            },
            "technical_report": {
                "name": "דוח טכני",
                "description": "דוח טכני עם מיקד בפרטים טכניים",
                "system_prompt": """אתה מהנדס טכני המסכם פגישות טכניות.
זהה את הפתרונות, בעיות, טכנולוגיות.
כלול ספציפיקציות טכניות בדוח.""",
                "user_prompt_template": """כתוב דוח טכני של השיחה הבאה:
- בעיות טכניות שהוזכרו
- פתרונות מוצעים
- דרישות טכניות
- הלו"ד (timeline) טכני

{transcript}

דוח טכני:""",
                "output_format": "txt"
            }
        }

    @staticmethod
    def seed_default_templates(db: Session, admin_user_id: str) -> int:
        """
        Create default templates if they don't exist

        Args:
            db: Database session
            admin_user_id: Admin user ID for creation

        Returns:
            Number of templates created
        """
        default_templates = TemplateService.get_default_templates()
        created_count = 0

        for key, config in default_templates.items():
            existing = db.query(Template).filter(
                Template.name == config["name"]
            ).first()

            if not existing:
                template = TemplateService.create_template(
                    db,
                    name=config["name"],
                    description=config["description"],
                    system_prompt=config["system_prompt"],
                    user_prompt_template=config["user_prompt_template"],
                    output_format=config["output_format"],
                    created_by_user_id=admin_user_id
                )

                if template:
                    created_count += 1

        logger.info(f"Seeded {created_count} default templates")
        return created_count


# Type hint for default templates
from typing import Dict

# Create service instance
template_service = TemplateService()

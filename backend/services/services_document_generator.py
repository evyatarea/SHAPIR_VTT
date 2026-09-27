"""
Document Generator Service - PDF/DOCX/XLSX template rendering
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import json
from io import BytesIO

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
except ImportError:
    Document = None

try:
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill
except ImportError:
    load_workbook = None

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
except ImportError:
    SimpleDocTemplate = None

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Service for generating formatted documents from templates and summary data"""

    @staticmethod
    def generate_pdf(
        template_name: str,
        summary_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate PDF document from summary data

        Args:
            template_name: Name/title for the document
            summary_data: Dictionary with keys like 'summary_text', 'date', 'duration', etc.
            output_path: Optional file path to save PDF (if None, returns BytesIO)

        Returns:
            BytesIO buffer containing PDF content
        """
        if SimpleDocTemplate is None:
            raise ImportError("reportlab is not installed. Install with: pip install reportlab")

        try:
            # Create PDF buffer
            pdf_buffer = BytesIO()

            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for PDF elements
            elements = []

            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=RGBColor(0, 0, 0),
                spaceAfter=30,
                alignment=TA_CENTER,
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=RGBColor(31, 78, 121),
                spaceAfter=12,
                spaceBefore=12,
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
            )

            # Add title
            elements.append(Paragraph(template_name, title_style))
            elements.append(Spacer(1, 12))

            # Add metadata
            if summary_data.get('date'):
                elements.append(Paragraph(
                    f"<b>תאריך:</b> {summary_data['date']}",
                    body_style
                ))
            if summary_data.get('duration'):
                elements.append(Paragraph(
                    f"<b>משך:</b> {summary_data['duration']} שניות",
                    body_style
                ))
            if summary_data.get('language'):
                elements.append(Paragraph(
                    f"<b>שפה:</b> {summary_data['language']}",
                    body_style
                ))

            elements.append(Spacer(1, 20))

            # Add summary text
            if summary_data.get('summary_text'):
                elements.append(Paragraph("סיכום", heading_style))
                summary_text = summary_data['summary_text'].replace('\n', '<br/>')
                elements.append(Paragraph(summary_text, body_style))

            # Add additional sections if provided
            if summary_data.get('action_items'):
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("פעולות נדרשות", heading_style))
                action_items = summary_data['action_items']
                if isinstance(action_items, str):
                    action_items = action_items.replace('\n', '<br/>')
                elements.append(Paragraph(action_items, body_style))

            # Build PDF
            doc.build(elements)

            # Save to file if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_buffer.getvalue())
                logger.info(f"PDF saved: {output_path}")

            # Reset buffer position
            pdf_buffer.seek(0)
            return pdf_buffer

        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise

    @staticmethod
    def generate_docx(
        template_name: str,
        summary_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate DOCX document from summary data

        Args:
            template_name: Name/title for the document
            summary_data: Dictionary with keys like 'summary_text', 'date', 'duration', etc.
            output_path: Optional file path to save DOCX (if None, returns BytesIO)

        Returns:
            BytesIO buffer containing DOCX content
        """
        if Document is None:
            raise ImportError("python-docx is not installed. Install with: pip install python-docx")

        try:
            # Create document
            doc = Document()

            # Add title
            title = doc.add_heading(template_name, level=0)
            title.alignment = 1  # Center alignment

            # Add metadata
            if summary_data.get('date') or summary_data.get('duration'):
                metadata = doc.add_paragraph()
                if summary_data.get('date'):
                    metadata.add_run(f"תאריך: {summary_data['date']}\n").bold = True
                if summary_data.get('duration'):
                    metadata.add_run(f"משך: {summary_data['duration']} שניות\n").bold = True
                if summary_data.get('language'):
                    metadata.add_run(f"שפה: {summary_data['language']}").bold = True

            # Add summary
            if summary_data.get('summary_text'):
                doc.add_heading('סיכום', level=1)
                summary_para = doc.add_paragraph(summary_data['summary_text'])
                summary_para.alignment = 3  # Justify alignment

            # Add action items if provided
            if summary_data.get('action_items'):
                doc.add_heading('פעולות נדרשות', level=1)
                action_items = summary_data['action_items']
                if isinstance(action_items, str):
                    # Parse lines as separate paragraphs
                    for line in action_items.split('\n'):
                        if line.strip():
                            doc.add_paragraph(line, style='List Bullet')
                else:
                    for item in action_items:
                        doc.add_paragraph(str(item), style='List Bullet')

            # Add footer with timestamp
            footer_para = doc.add_paragraph()
            footer_para.add_run(f"\nנוצר: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}").italic = True

            # Create BytesIO buffer
            docx_buffer = BytesIO()
            doc.save(docx_buffer)

            # Save to file if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(docx_buffer.getvalue())
                logger.info(f"DOCX saved: {output_path}")

            # Reset buffer position
            docx_buffer.seek(0)
            return docx_buffer

        except Exception as e:
            logger.error(f"Failed to generate DOCX: {e}")
            raise

    @staticmethod
    def generate_xlsx(
        template_name: str,
        summary_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate XLSX spreadsheet from summary data

        Args:
            template_name: Name/title for the sheet
            summary_data: Dictionary with keys like 'summary_text', 'date', 'duration', etc.
            output_path: Optional file path to save XLSX (if None, returns BytesIO)

        Returns:
            BytesIO buffer containing XLSX content
        """
        if load_workbook is None:
            raise ImportError("openpyxl is not installed. Install with: pip install openpyxl")

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "סיכום"

            # Set column widths
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 60

            # Add title
            ws['A1'] = template_name
            ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
            ws['A1'].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
            ws.merge_cells('A1:B1')
            ws.row_dimensions[1].height = 30

            row = 3

            # Add metadata
            if summary_data.get('date'):
                ws[f'A{row}'] = "תאריך:"
                ws[f'A{row}'].font = Font(bold=True)
                ws[f'B{row}'] = summary_data['date']
                row += 1

            if summary_data.get('duration'):
                ws[f'A{row}'] = "משך:"
                ws[f'A{row}'].font = Font(bold=True)
                ws[f'B{row}'] = f"{summary_data['duration']} שניות"
                row += 1

            if summary_data.get('language'):
                ws[f'A{row}'] = "שפה:"
                ws[f'A{row}'].font = Font(bold=True)
                ws[f'B{row}'] = summary_data['language']
                row += 1

            row += 1

            # Add summary
            if summary_data.get('summary_text'):
                ws[f'A{row}'] = "סיכום:"
                ws[f'A{row}'].font = Font(bold=True, size=12, color="1F4E79")
                ws.merge_cells(f'A{row}:B{row}')
                row += 1

                # Split summary into manageable text chunks
                summary_text = summary_data['summary_text']
                summary_lines = summary_text.split('\n')

                for line in summary_lines:
                    if line.strip():
                        ws[f'A{row}'] = line
                        ws[f'A{row}'].alignment = Alignment(
                            horizontal="right",
                            vertical="top",
                            wrap_text=True
                        )
                        ws.merge_cells(f'A{row}:B{row}')
                        ws.row_dimensions[row].height = None  # Auto height
                        row += 1

            row += 1

            # Add action items if provided
            if summary_data.get('action_items'):
                ws[f'A{row}'] = "פעולות נדרשות:"
                ws[f'A{row}'].font = Font(bold=True, size=12, color="1F4E79")
                ws.merge_cells(f'A{row}:B{row}')
                row += 1

                action_items = summary_data['action_items']
                if isinstance(action_items, str):
                    for line in action_items.split('\n'):
                        if line.strip():
                            ws[f'A{row}'] = line
                            ws[f'A{row}'].alignment = Alignment(
                                horizontal="right",
                                vertical="top",
                                wrap_text=True
                            )
                            ws.merge_cells(f'A{row}:B{row}')
                            row += 1

            # Add footer
            row += 1
            ws[f'A{row}'] = f"נוצר: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            ws[f'A{row}'].font = Font(italic=True, size=9)

            # Create BytesIO buffer
            xlsx_buffer = BytesIO()
            wb.save(xlsx_buffer)

            # Save to file if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(xlsx_buffer.getvalue())
                logger.info(f"XLSX saved: {output_path}")

            # Reset buffer position
            xlsx_buffer.seek(0)
            return xlsx_buffer

        except Exception as e:
            logger.error(f"Failed to generate XLSX: {e}")
            raise

    @staticmethod
    def generate_txt(
        template_name: str,
        summary_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate plain text document from summary data

        Args:
            template_name: Name/title for the document
            summary_data: Dictionary with keys like 'summary_text', 'date', 'duration', etc.
            output_path: Optional file path to save TXT (if None, returns BytesIO)

        Returns:
            BytesIO buffer containing TXT content
        """
        try:
            # Create text content
            lines = []
            lines.append("=" * 80)
            lines.append(template_name.center(80))
            lines.append("=" * 80)
            lines.append("")

            # Add metadata
            if summary_data.get('date'):
                lines.append(f"תאריך: {summary_data['date']}")
            if summary_data.get('duration'):
                lines.append(f"משך: {summary_data['duration']} שניות")
            if summary_data.get('language'):
                lines.append(f"שפה: {summary_data['language']}")

            if any(summary_data.get(k) for k in ['date', 'duration', 'language']):
                lines.append("")

            # Add summary
            if summary_data.get('summary_text'):
                lines.append("סיכום:")
                lines.append("-" * 80)
                lines.append(summary_data['summary_text'])
                lines.append("")

            # Add action items if provided
            if summary_data.get('action_items'):
                lines.append("פעולות נדרשות:")
                lines.append("-" * 80)
                action_items = summary_data['action_items']
                if isinstance(action_items, str):
                    lines.append(action_items)
                else:
                    for item in action_items:
                        lines.append(f"• {item}")
                lines.append("")

            # Add footer
            lines.append("")
            lines.append("=" * 80)
            lines.append(f"נוצר: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

            # Create text content
            text_content = "\n".join(lines)

            # Create BytesIO buffer
            txt_buffer = BytesIO(text_content.encode('utf-8'))

            # Save to file if path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                logger.info(f"TXT saved: {output_path}")

            # Reset buffer position
            txt_buffer.seek(0)
            return txt_buffer

        except Exception as e:
            logger.error(f"Failed to generate TXT: {e}")
            raise

    @staticmethod
    def generate_document(
        output_format: str,
        template_name: str,
        summary_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate document in specified format

        Args:
            output_format: Format type (pdf, docx, xlsx, txt)
            template_name: Document title/name
            summary_data: Summary data to include
            output_path: Optional file path to save document

        Returns:
            BytesIO buffer containing document content

        Raises:
            ValueError: If output_format is not supported
        """
        format_lower = output_format.lower()

        if format_lower == "pdf":
            return DocumentGenerator.generate_pdf(template_name, summary_data, output_path)
        elif format_lower == "docx":
            return DocumentGenerator.generate_docx(template_name, summary_data, output_path)
        elif format_lower == "xlsx":
            return DocumentGenerator.generate_xlsx(template_name, summary_data, output_path)
        elif format_lower == "txt":
            return DocumentGenerator.generate_txt(template_name, summary_data, output_path)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")


# Create service instance
document_generator = DocumentGenerator()

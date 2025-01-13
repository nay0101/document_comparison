from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
import markdown
from typing import Optional, Dict, List
import html
from bs4 import BeautifulSoup
import re
from xml.sax.saxutils import escape, unescape
from datetime import datetime


class MarkdownPDFConverter:
    def __init__(
        self,
        font_size: int = 11,
        margin: float = 1.0,  # in inches
        css: Optional[str] = None,  # kept for compatibility
    ):
        self.font_size = font_size
        self.margin = margin * inch

        # Initialize styles
        self.styles = getSampleStyleSheet()
        self.setup_styles()

    def setup_styles(self):
        """Set up custom styles for different elements"""
        # Create custom heading styles
        self.custom_heading1 = ParagraphStyle(
            "CustomHeading1",
            parent=self.styles["Heading1"],
            fontSize=self.font_size * 2,
            spaceAfter=self.font_size,
            spaceBefore=self.font_size * 2,
        )

        self.custom_heading2 = ParagraphStyle(
            "CustomHeading2",
            parent=self.styles["Heading2"],
            fontSize=self.font_size * 1.5,
            spaceAfter=self.font_size,
            spaceBefore=self.font_size,
        )

        self.custom_heading3 = ParagraphStyle(
            "CustomHeading3",
            parent=self.styles["Heading3"],
            fontSize=self.font_size * 1.2,
            spaceAfter=self.font_size,
            spaceBefore=self.font_size,
        )

        # Create custom code style
        self.code_style = ParagraphStyle(
            "CustomCode",
            parent=self.styles["Normal"],
            fontName="Courier",
            fontSize=self.font_size,
            backColor=colors.HexColor("#F2F2F2"),
            spaceAfter=self.font_size,
            spaceBefore=self.font_size,
        )

    def _html_to_reportlab(self, html_content: str) -> List:
        """Convert HTML content to ReportLab elements"""
        soup = BeautifulSoup(html_content, "html.parser")
        elements = []

        for element in soup.find_all(["h1", "h2", "h3", "p", "pre", "table"]):
            # Clean the text content by removing XML/HTML tags and preserving only text
            text_content = self._clean_text_content(str(element))

            if element.name == "h1":
                elements.append(Paragraph(text_content, self.custom_heading1))
            elif element.name == "h2":
                elements.append(Paragraph(text_content, self.custom_heading2))
            elif element.name == "h3":
                elements.append(Paragraph(text_content, self.custom_heading3))
            elif element.name == "p":
                elements.append(Paragraph(text_content, self.custom_normal))
            elif element.name == "pre":
                elements.append(Paragraph(text_content, self.code_style))

            elif element.name == "table":
                # Process table
                table_data = []
                for row in element.find_all("tr"):
                    table_row = []
                    for cell in row.find_all(["th", "td"]):
                        table_row.append(
                            Paragraph(cell.get_text(), self.styles["Normal"])
                        )
                    table_data.append(table_row)

                if table_data:
                    table = Table(table_data)
                    table.setStyle(
                        TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, 0),
                                    colors.HexColor("#E6E6E6"),
                                ),  # Light gray header
                                (
                                    "TEXTCOLOR",
                                    (0, 0),
                                    (-1, 0),
                                    colors.HexColor("#000000"),
                                ),
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, 0), self.font_size),
                                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                                (
                                    "BACKGROUND",
                                    (0, 1),
                                    (-1, -1),
                                    colors.HexColor("#FFFFFF"),
                                ),
                                (
                                    "TEXTCOLOR",
                                    (0, 1),
                                    (-1, -1),
                                    colors.HexColor("#000000"),
                                ),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 1), (-1, -1), self.font_size),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                (
                                    "GRID",
                                    (0, 0),
                                    (-1, -1),
                                    1,
                                    colors.HexColor("#000000"),
                                ),
                                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                            ]
                        )
                    )
                    elements.append(table)

            elements.append(Spacer(1, self.font_size))

        return elements

    def convert(
        self,
        markdown_text: str,
        output_path: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Convert markdown to PDF"""
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_text,
            extensions=["extra", "codehilite", "tables", "footnotes", "smarty", "meta"],
        )

        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # Add metadata if provided
        if metadata:
            doc.setAuthor(metadata.get("author", ""))
            doc.setTitle(metadata.get("title", ""))
            doc.setSubject(metadata.get("subject", ""))

        # Convert HTML to ReportLab elements and build PDF
        elements = self._html_to_reportlab(html_content)
        doc.build(elements)

    def _clean_text_content(self, text: str) -> str:
        """Clean HTML/XML content while preserving supported HTML tags"""
        soup = BeautifulSoup(text, "html.parser")

        # Function to process a tag and its contents
        def process_tag(tag):
            if tag.name == "span" and tag.get("style"):
                # Handle span with style
                style = tag.get("style", "")
                if "color:" in style.lower():
                    text = tag.get_text()
                    # For red text, use ReportLab's color tag syntax
                    return f'<font color="red">{text}</font>'
            return tag.get_text()

        # Process the content
        processed_text = ""
        for element in soup.children:
            if isinstance(element, str):
                processed_text += element
            else:
                processed_text += process_tag(element)

        # Remove para tags but keep the content and font tags
        processed_text = re.sub(r"</?para[^>]*>", "", processed_text)

        return processed_text

    def _escape_table_cell(self, text: str) -> str:
        """Escape special characters in table cells"""
        text = self._clean_text_content(str(text))
        return escape(text).replace("\n", " ")

    def generate_report(
        self,
        chat_model_name: str,
        chat_id: str,
        result: Dict,
        path: str,
        time_taken: str,
        file1_name: str,
        file2_name: str,
    ) -> None:
        """Generate comparison report"""
        from helpers.cost import get_total_cost

        cost = get_total_cost(chat_id=chat_id)

        text = f"""# Document Comparison with {chat_model_name}
* File 1: {file1_name}
* File 2: {file2_name}
* Total Cost: ${cost}
* Time Taken: {time_taken}s
# Discrepancies
Total Discrepancies Found: {len(result["flags"])}
"""
        for index, flag in enumerate(result["flags"]):
            flag_types = ", ".join(flag["types"])
            content1 = self._escape_table_cell(flag["doc1"]["content"])
            content2 = self._escape_table_cell(flag["doc2"]["content"])

            text += f"""## No. {index+1}
### Flags: {flag_types}
|Document 1                      |Document 2                      |
|--------------------------------|--------------------------------|
|{content1}|{content2}|

Explanation: {flag["explanation"]}

"""
        self.convert(markdown_text=text, output_path=path)

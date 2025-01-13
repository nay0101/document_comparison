from weasyprint.text.fonts import FontConfiguration
import markdown
from helpers.cost import get_total_cost
from weasyprint import HTML, CSS
from typing import Optional, Dict, List


class MarkdownPDFConverter:
    def __init__(
        self, font_size: int = 11, margin: str = "1in", css: Optional[str] = None
    ):
        self.font_size = font_size
        self.margin = margin
        self.default_css = f"""
            @page {{
                margin: {margin};
                @bottom-right {{
                    content: counter(page);
                }}
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: {font_size}pt;
                line-height: 1.5;
            }}
            code {{
                background-color: #f6f8fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 16px;
                border-radius: 6px;
                white-space: pre-wrap;
            }}
            h1 {{ 
                font-size: {font_size * 2}pt;
                page-break-before: always;
                margin-top: 0;
                color: black;
            }}
            h2 {{ 
                font-size: {font_size * 1.5}pt;
                page-break-after: avoid;
            }}
            h3 {{ 
                font-size: {font_size * 1.2}pt;
                page-break-after: avoid;
            }}
            p {{ page-break-inside: avoid; }}
            table {{ 
                width: 100%;
                border-collapse: collapse;
                page-break-inside: avoid;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
        """
        self.css = CSS(string=css if css else self.default_css)
        self.font_config = FontConfiguration()

    def convert(
        self,
        markdown_text: str,
        output_path: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Convert markdown to PDF with automatic page breaks.

        Args:
            markdown_text: The markdown content to convert
            output_path: Output PDF file path
            metadata: Optional PDF metadata
        """
        # Convert markdown to HTML
        html = markdown.markdown(
            markdown_text,
            extensions=["extra", "codehilite", "tables", "footnotes", "smarty", "meta"],
        )

        # Add HTML wrapper
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                {self._generate_metadata_tags(metadata) if metadata else ''}
            </head>
            <body>
                {html}
            </body>
        </html>
        """

        # Convert to PDF
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[self.css],
            font_config=self.font_config,
            presentational_hints=True,
        )

    def _generate_metadata_tags(self, metadata: Dict[str, str]) -> str:
        """Generate HTML metadata tags from dictionary."""
        tags = []
        for key, value in metadata.items():
            tags.append(f'<meta name="{key}" content="{value}">')
        return "\n".join(tags)

    def _escape_table_cell(self, text: str) -> str:
        return str(text).replace("|", "\\|").replace("\n", " ")

    def generate_report(
        self,
        chat_model_name: str,
        chat_id: str,
        result: List,
        path: str,
        time_taken: str,
        file1_name: str,
        file2_name: str,
    ) -> None:
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
            # print(content1)
            text += f"""## No. {index+1}
### Flags: {flag_types}
|Document 1                      |Document 2                      |
|--------------------------------|--------------------------------|
|{content1}|{content2}|

Explanation: {flag["explanation"]}

"""

        self.convert(markdown_text=text, output_path=path)
        return

import markdown
from xhtml2pdf import pisa
from typing import List, Optional
from helpers.cost import get_total_cost
from io import BytesIO


class MarkdownPDFConverter:
    def __init__(self, font_size: int = 10, margin: str = "1in"):
        self.font_size = font_size
        self.margin = margin

    def convert_using_xhtml2pdf(self, markdown_content):
        """Convert markdown to PDF using xhtml2pdf"""
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=["extra", "codehilite", "tables", "footnotes", "smarty", "meta"],
        )

        # Add basic CSS styling
        html_with_style = f"""
          <html>
          <head>
              <style>
              body {{
                  font-family: Arial, sans-serif;
                  font-size: {self.font_size}pt;
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
                  font-size: {self.font_size * 2}pt;
                  margin-top: 0;
                  color: black;
                  page-break-after: avoid;
              }}
              h2 {{ 
                  font-size: {self.font_size * 1.5}pt;
                  page-break-after: avoid;
              }}
              h3 {{ 
                  font-size: {self.font_size * 1.2}pt;
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
                  vertical-align: top;
              }}
              img {{
                  max-width: 100%;
                  height: auto;
              }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        output_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_with_style, dest=output_buffer)
        output_buffer.seek(0)
        return output_buffer.getvalue()

    def _escape_table_cell(self, text: str) -> str:
        return str(text).replace("|", "\\|").replace("\n", " ")

    def generate_report(
        self,
        chat_model_name: str,
        chat_id: str,
        result: List,
        time_taken: str,
        file1_name: str,
        file2_name: str,
        correct_results: Optional[List] = None,
    ) -> None:
        cost = get_total_cost(chat_id=chat_id)
        text = f"""# Document Comparison with {chat_model_name}
* File 1: {file1_name}
* File 2: {file2_name}
* Total Cost: ${cost}
* Time Taken: {time_taken}s
<div style="page-break-after: always;"></div>
# Discrepancies
Total Discrepancies Found: {len(result["flags"])}
"""
        for index, flag in enumerate(result["flags"]):
            flag_types = ", ".join(flag["types"])
            content1 = self._escape_table_cell(flag["doc1"]["content"])
            content2 = self._escape_table_cell(flag["doc2"]["content"])
            if correct_results is not None and correct_results[index]:
                text += f"""## <span style='color: green;'>No. {index + 1} (Correct)</span>"""
            else:
                text += f"""## No. {index + 1}"""
            text += f"""
### Flags: {flag_types}
|Document 1                      |Document 2                      |
|--------------------------------|--------------------------------|
|{content1}|{content2}|

Explanation: {flag["explanation"]}

"""

        result = self.convert_using_xhtml2pdf(markdown_content=text)
        return result

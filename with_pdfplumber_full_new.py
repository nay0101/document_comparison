import pdfplumber
import pandas as pd
from tabulate import tabulate
import os

pdf_path = "multilingual_docs\Sutera\hlb-sutera-credit-card-tnc-en.pdf"
output_dir = "extracted_full_pdfplumber"
os.makedirs(output_dir, exist_ok=True)

markdown_path = os.path.join(output_dir, "full_document.md")
markdown_content = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        section_md = [f"# Page {page_num}"]

        # Get all tables with their vertical position and bounding boxes
        tables = []
        table_bboxes = []
        for i, table in enumerate(page.extract_tables()):
            # Only keep tables with at least 2 rows (header + at least 1 data row) and at least 2 columns
            if not table or not table[0] or len(table) < 2 or len(table[0]) < 2:
                continue
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
            }
            table_bbox = None
            try:
                table_bbox = page.find_tables(table_settings=table_settings)[i].bbox
                table_bboxes.append(table_bbox)
            except Exception:
                table_bbox = None
            df = pd.DataFrame(table[1:], columns=table[0])
            md_table = tabulate(
                df.values.tolist(), headers=df.columns.tolist(), tablefmt="pipe"
            )
            tables.append(
                {
                    "type": "table",
                    "top": table_bbox[1] if table_bbox else 0,
                    "content": f"## Table {i+1}\n{md_table}",
                }
            )

        # Get text blocks with their vertical position, excluding words inside tables
        words = page.extract_words()
        if words:
            lines = {}
            for w in words:
                # Check if word is inside any table bbox
                in_table = False
                for bbox in table_bboxes:
                    if bbox and (
                        w["x0"] >= bbox[0]
                        and w["x1"] <= bbox[2]
                        and w["top"] >= bbox[1]
                        and w["bottom"] <= bbox[3]
                    ):
                        in_table = True
                        break
                if not in_table:
                    top = round(w["top"])
                    lines.setdefault(top, []).append(w["text"])
            text_blocks = []
            for top in sorted(lines):
                line_text = " ".join(lines[top])
                text_blocks.append({"type": "text", "top": top, "content": line_text})
        else:
            text_blocks = []

        # Combine text blocks and tables, sort by 'top'
        items = text_blocks + tables
        items.sort(key=lambda x: x["top"])

        # Add to markdown
        for item in items:
            if item["type"] == "text":
                section_md.append(item["content"])
            elif item["type"] == "table":
                section_md.append(item["content"])

        markdown_content.append("\n\n".join(section_md))

with open(markdown_path, "w", encoding="utf-8") as f:
    f.write("\n\n---\n\n".join(markdown_content))

print(f"\n✅ Full document with text and tables saved to: {markdown_path}")

import pdfplumber
import pandas as pd
from tabulate import tabulate
import os

# Input PDF and output paths
pdf_path = "multilingual_docs\Sutera\hlb-sutera-credit-card-tnc-en.pdf"
output_dir = "extracted_full_pdfplumber"
os.makedirs(output_dir, exist_ok=True)

markdown_path = os.path.join(output_dir, "full_document.md")
markdown_content = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        section_md = [f"# Page {page_num}"]

        # --- Extract page text ---
        text = page.extract_text()
        if text and text.strip():
            section_md.append("## Text\n")
            section_md.append(text.strip())

        # --- Extract tables ---
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            if not table or not table[0]:
                continue

            # Create DataFrame
            df = pd.DataFrame(table[1:], columns=table[0])

            # Save as individual CSV (optional)
            # csv_filename = f"table_page{page_num}_table{i+1}.csv"
            # csv_path = os.path.join(output_dir, csv_filename)
            # df.to_csv(csv_path, index=False)
            # print(f"✅ Saved CSV: {csv_path}")

            # Format table in Markdown
            md_header = f"## Table {i+1}"
            md_table = tabulate(
                df.values.tolist(), headers=df.columns.tolist(), tablefmt="pipe"
            )
            section_md.append(md_header)
            section_md.append(md_table)
            print(md_table)

        # Append the page content to the document
        markdown_content.append("\n\n".join(section_md))

# --- Write all to Markdown file ---
with open(markdown_path, "w", encoding="utf-8") as f:
    f.write("\n\n---\n\n".join(markdown_content))

print(f"\n✅ Full document with text and tables saved to: {markdown_path}")

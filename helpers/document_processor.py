from typing import Union
import pymupdf
from io import BytesIO
import re
from xml.sax.saxutils import escape


class DocumentProcessor:
    def extract_text_with_page_number(self, pdf_bytes: Union[bytes, BytesIO]) -> str:
        """Extract text from PDF with location metadata."""
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        final_doc = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            final_doc += (
                f"<page{page_num + 1}>\n{text.strip()}\n</page{page_num + 1}>\n"
            )
            # final_doc += f"{text.strip()}\n"
        return final_doc

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF with location metadata."""
        doc = pymupdf.open(pdf_path)
        final_doc = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # final_doc += f"Page {page_num + 1}\n{text.strip()}\n\n"
            final_doc += text.strip()
        return final_doc

    def clean_xml(self, text: str) -> str:
        return re.sub(
            "(<[^>]*>)|([^<>]+)",
            lambda m: m.group(1)
            or escape(m.group(2)).replace("]]>", "]]&gt;").replace("--", "&#45;&#45;"),
            text,
        )

    def clean_chunk_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```xml"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        opening = "<chunked_documents>"
        closing = "</chunked_documents>"

        # Remove all tags first
        text = text.replace(opening, "")
        text = text.replace(closing, "")
        text = f"{opening}\n{text}\n{closing}"
        return text

    def clean_compare_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[8:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text

    def get_last_chunk(self, text: str) -> str:
        # Split by chunk opening tags
        chunks = text.split('<chunk number="')

        # Remove empty first split if any
        if not chunks[0].strip():
            chunks.pop(0)

        # Look for last complete chunk
        for chunk in reversed(chunks):
            if "</chunk>" in chunk:
                return f'<chunk number="{chunk}'
        return ""

    def get_last_two_chunks(self, text: str) -> tuple:
        # Find the last two chunk numbers
        chunks = text.split('<chunk number="')

        # Remove empty first split if any
        if not chunks[0].strip():
            chunks.pop(0)

        # Get last two chunks if available
        if len(chunks) >= 2:
            chunk1 = '<chunk number="' + chunks[-2]
            chunk2 = '<chunk number="' + chunks[-1]
            return chunk1 + chunk2
        elif len(chunks) == 1:
            return '<chunk number="' + chunks[0]
        return ()

    def get_complete_chunks(self, text: str) -> str:
        has_end_tag = "</chunked_documents>" in text
        end_tag = "</chunked_documents>" if has_end_tag else ""

        # Remove end tag temporarily if it exists
        if has_end_tag:
            text = text.replace(end_tag, "")

        # Split into chunks
        chunks = text.split("</chunk>")

        # Join complete chunks and add back the end tag if it existed
        if chunks[:-1]:
            return "</chunk>".join(chunks[:-1]) + "</chunk>" + end_tag
        return ""

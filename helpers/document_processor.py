from typing import Union
import pymupdf
from io import BytesIO
import re
from xml.sax.saxutils import escape
from collections import defaultdict
from difflib import SequenceMatcher


class DocumentProcessor:
    def extract_filtered_content(
        self,
        pdf_bytes: Union[BytesIO, bytes],
        similarity_threshold: float = 0.80,
        min_occurrence_percent: int = 90,
    ) -> str:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        total_pages = doc.page_count
        min_occurrences = (total_pages * min_occurrence_percent) / 100

        # Store all content first
        content_occurrences = defaultdict(list)
        all_page_blocks = defaultdict(list)

        print(f"Analyzing {total_pages} pages...")
        # First pass: collect all content
        for page_num, page in enumerate(doc, 1):
            blocks = page.get_text("blocks")

            for block in blocks:
                _, _, _, _, content, block_no, block_type = block
                content = content.strip()

                if block_type == 0 and content:
                    # Store original block information
                    all_page_blocks[page_num].append(
                        {"text": content, "block_no": block_no}
                    )

                    # Check similarity with existing content
                    found_similar = False
                    for existing_content in list(content_occurrences.keys()):
                        if (
                            SequenceMatcher(None, content, existing_content).ratio()
                            >= similarity_threshold
                        ):
                            content_occurrences[existing_content].append(
                                {"page": page_num, "text": content}
                            )
                            found_similar = True
                            break

                    if not found_similar:
                        content_occurrences[content].append(
                            {"page": page_num, "text": content}
                        )

        # Identify frequently repeating content
        frequent_patterns = {}
        print("\nIdentifying frequent patterns:")
        print("-" * 50)

        for content, occurrences in content_occurrences.items():
            if len(occurrences) >= min_occurrences:
                occurrence_percent = (len(occurrences) / total_pages) * 100
                print(f"\nContent: '{content}'")
                print(
                    f"Appears in {len(occurrences)}/{total_pages} pages ({occurrence_percent:.1f}%)"
                )
                print("Variations found:")
                for occ in occurrences:
                    if occ["text"] != content:
                        similarity = SequenceMatcher(None, content, occ["text"]).ratio()
                        print(
                            f"Page {occ['page']}: '{occ['text']}' (similarity: {similarity:.2f})"
                        )
                frequent_patterns[content] = occurrences

        # Remove frequent patterns from original content
        filtered_content = []
        print("\nExtracting content after removing frequent patterns:")
        print("-" * 50)

        for page_num, blocks in all_page_blocks.items():
            for block in blocks:
                content = block["text"]
                should_keep = True

                # Check if this content is similar to any frequent pattern
                for pattern in frequent_patterns.keys():
                    if (
                        SequenceMatcher(None, content, pattern).ratio()
                        >= similarity_threshold
                    ):
                        should_keep = False
                        break

                if should_keep:
                    filtered_content.append(
                        "\n".join(
                            line.strip()
                            for line in content.splitlines()
                            if line.strip()
                        )
                    )

        # Print summary
        print("\nSummary:")
        print(f"Total pages analyzed: {total_pages}")
        print(f"Frequent patterns found: {len(frequent_patterns)}")

        doc.close()

        return "\n".join(filtered_content)

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF with location metadata."""
        doc = pymupdf.open(pdf_path)
        final_doc = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

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

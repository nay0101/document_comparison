from typing import Union, List
import pymupdf
from io import BytesIO
import re
from xml.sax.saxutils import escape
from collections import defaultdict
from difflib import SequenceMatcher
import streamlit as st


class DocumentProcessor:
    def extract_filtered_content(
        self,
        pdf_bytes: Union[BytesIO, bytes],
        similarity_threshold: float = 0.80,
        min_occurrence_percent: int = 90,
    ) -> str:
        with st.spinner("Loading Documents"):
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
                            similarity = SequenceMatcher(
                                None, content, occ["text"]
                            ).ratio()
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

    def extract_full_content(
        self,
        pdf_bytes: Union[BytesIO, bytes],
    ) -> str:
        with st.spinner("Loading Documents"):
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            special_chars = {
                # Bullets and List Markers
                "\uf0b7": "•",  # Common bullet
                "\uf0a7": "•",  # Another bullet variant
                "\uf0be": "•",  # Circle bullet
                "\uf0a8": "○",  # White circle
                "\uf0d8": "▪",  # Square bullet
                "\uf0e8": "◆",  # Diamond bullet
                "\uf0de": "▲",  # Up triangle
                "\uf0da": "►",  # Right triangle
                "\uf0dd": "▼",  # Down triangle
                "\uf0db": "◄",  # Left triangle
                # Spaces and Breaks
                "\uf0a0": " ",  # Non-breaking space
                "\uf020": " ",  # Space
                "\uf0b6": "¶",  # Paragraph mark
                "\uf0b8": "¬",  # Line break
                # Punctuation and Symbols
                "\uf02d": "-",  # Special hyphen
                "\uf0ad": "–",  # En dash
                "\uf0bd": "—",  # Em dash
                "\uf02e": ".",  # Period
                "\uf0fc": "✓",  # Checkmark
                "\uf0fb": "✗",  # Cross mark
                "\uf0d0": "†",  # Dagger
                "\uf0d1": "‡",  # Double dagger
                # Quotes and Brackets
                "\uf0ab": "«",  # Left double angle quotes
                "\uf0bb": "»",  # Right double angle quotes
                "\uf027": "'",  # Single quote
                "\uf022": '"',  # Double quote
                "\uf05b": "[",  # Left bracket
                "\uf05d": "]",  # Right bracket
                "\uf07b": "{",  # Left brace
                "\uf07d": "}",  # Right brace
                # Arrows and Directions
                "\uf0e0": "→",  # Right arrow
                "\uf0e1": "←",  # Left arrow
                "\uf0e2": "↑",  # Up arrow
                "\uf0e3": "↓",  # Down arrow
                "\uf0df": "↔",  # Left-right arrow
                # Mathematical Symbols
                "\uf0b1": "±",  # Plus-minus
                "\uf0d7": "×",  # Multiplication
                "\uf0f7": "÷",  # Division
                "\uf0b3": "³",  # Superscript 3
                "\uf0b2": "²",  # Superscript 2
                # Currency Symbols
                "\uf0a3": "£",  # Pound
                "\uf0a5": "¥",  # Yen
                "\uf0a2": "¢",  # Cent
                "\uf0b0": "°",  # Degree
                # Legal and Commercial Symbols
                "\uf0a4": "®",  # Registered trademark
                "\uf0a9": "©",  # Copyright
                "\uf0ae": "™",  # Trademark
                "\uf0a7": "§",  # Section
                # Accented Characters
                "\uf0e4": "ä",  # a umlaut
                "\uf0f6": "ö",  # o umlaut
                "\uf0fc": "ü",  # u umlaut
                "\uf0e9": "é",  # e acute
                "\uf0e8": "è",  # e grave
                # Additional Symbols
                "\uf0ac": "⌂",  # House
                "\uf0af": "⌐",  # Reversed not
                "\uf0dc": "♠",  # Spade
                "\uf0db": "♥",  # Heart
                "\uf0df": "♣",  # Club
                "\uf0de": "♦",  # Diamond
            }
            final_doc = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                for special, normal in special_chars.items():
                    text = text.replace(f"{special} \n", normal)
                    text = text.replace(special, normal)

                final_doc += f"{text.strip()}\n"
                lines = [
                    line.strip() for line in final_doc.splitlines() if line.strip()
                ]

                final_result = "\n".join(lines)

        return final_result

    def split_guidelines(self, text: str) -> List[str]:
        with st.spinner("Loading Documents"):
            chunks = []
            current_chunk = ""
            lines = text.split("\n")

            for line in lines:
                if line.startswith(("S ", "G ", "P ")):
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    current_chunk += " " + line.strip()

            if current_chunk:
                chunks.append(current_chunk.strip())

        return chunks

    def clean_xml_format(self, text: str) -> str:
        valid_tags = [
            "chunk",
            "language1",
            "language2",
            "chunked_documents",
        ]

        def replace_match(m):
            if m.group(1):  # It's a tag
                tag_name = re.match(r"</?([a-zA-Z0-9_]+)", m.group(1))
                if (
                    tag_name and tag_name.group(1) in valid_tags
                ):  # Check if it's a valid tag
                    return m.group(1)  # Keep valid tags unchanged
                else:
                    return re.sub(
                        r"[<>]",
                        lambda x: "&lt;" if x.group(0) == "<" else "&gt;",
                        m.group(1),
                    )  # Escape invalid tags
            return (
                escape(m.group(2)).replace("]]>", "]]&gt;").replace("--", "&#45;&#45;")
            )  # Handle regular text

        return re.sub(r"(</?[a-zA-Z0-9_][^>]*>)|([^<>]+)", replace_match, text)

    def reformat_chunk_boundary(self, text: str) -> str:
        opening = "<chunked_documents>"
        closing = "</chunked_documents>"

        # Remove all tags first
        text = text.replace(opening, "")
        text = text.replace(closing, "")
        text = f"{opening}\n{text}\n{closing}"

        return text

    def remove_code_fences(self, text: str) -> str:
        if text.startswith("```"):
            newline_pos = text.find("\n")
            text = text[newline_pos + 1 :]

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

from typing import Union, List, Dict
import pymupdf
from io import BytesIO
import re
from xml.sax.saxutils import escape
from collections import defaultdict
from difflib import SequenceMatcher
import streamlit as st
import base64
from tabulate import tabulate
import pdfplumber
import pandas as pd
import os
import requests
import runpod


class DocumentProcessor:
    def extract_filtered_content(
        self,
        pdf_bytes: Union[BytesIO, bytes],
        similarity_threshold: float = 0.80,
        min_occurrence_percent: int = 90,
    ) -> Dict:
        with st.spinner("Loading Documents"):
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            total_pages = doc.page_count
            min_occurrences = (
                (total_pages * min_occurrence_percent) / 100 if total_pages > 1 else 1.1
            )

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
                            {
                                "page": page_num,
                                "content": "\n".join(
                                    line.strip()
                                    for line in content.splitlines()
                                    if line.strip()
                                ),
                            }
                        )
            # Print summary
            print("\nSummary:")
            print(f"Total pages analyzed: {total_pages}")
            print(f"Frequent patterns found: {len(frequent_patterns)}")

            pages = {}
            for item in filtered_content:
                page = item["page"]
                content = item["content"]
                if page not in pages:
                    pages[page] = content
                else:
                    pages[page] += "\n" + content

            doc.close()

            return {
                "total_pages": len(pages),
                "document": [
                    {"page": page, "content": content}
                    for page, content in pages.items()
                ],
            }

    def extract_titles(self, text: str) -> List[str]:
        # Split the text into lines
        lines = text.split("\n")

        # Flag to track if we've found "PART B"
        found_part_b = False

        # List to store extracted titles
        titles = []

        # Track highest main number seen
        highest_num = 0

        i = 0
        while i < len(lines):
            # Strip whitespace and dots
            clean_line = lines[i].strip().split("...")[0].strip()

            # Check if we found PART B
            if "PART B" in clean_line:
                found_part_b = True
                i += 1
                continue

            if not found_part_b:
                i += 1
                continue

            # Check if line is just a number
            if clean_line.replace(".", "").isdigit():
                # Look ahead to next line for title
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip().split("...")[0].strip()
                    number = clean_line
                    main_num = int(float(number))  # Get the main number before decimal

                    # Stop if we encounter a number lower than highest seen
                    if "." not in number and main_num < highest_num:
                        break

                    # Update highest number if it's a main number
                    if "." not in number:
                        highest_num = main_num

                    titles.append(f"{number} {next_line}")
                    i += 2
                    continue

            # Check if the line starts with a number
            parts = clean_line.split(" ", 1)
            if len(parts) >= 2 and parts[0].replace(".", "").isdigit():
                number = parts[0]
                main_num = int(float(number))  # Get the main number before decimal

                # Stop if we encounter a number lower than highest seen
                if "." not in number and main_num < highest_num:
                    break

                # Update highest number if it's a main number
                if "." not in number:
                    highest_num = main_num

                titles.append(clean_line)

            i += 1

        return titles

    def replace_special_chars(self, text: str) -> str:
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

        for special, normal in special_chars.items():
            text = text.replace(f"{special} \n", normal)
            text = text.replace(special, normal)

        return text

    def extract_full_content(
        self,
        pdf_bytes: Union[BytesIO, bytes],
    ) -> str:
        with st.spinner("Loading Documents"):
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

            final_doc = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = self.replace_special_chars(page.get_text("text"))

                final_doc += f"{text.strip()}\n"
                lines = [
                    line.strip() for line in final_doc.splitlines() if line.strip()
                ]

                final_result = "\n".join(lines)

            doc.close()
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

    def extract_clauses(self, target_title: str, text: str) -> List[str]:
        """
        Extract clauses from PDF text based on a given title.

        Args:
            target_title (str): The title to search for (e.g., "10.2 Title")
            text (str): The text content to search within

        Returns:
            list: List of extracted clauses
        """
        # Normalize the target title by removing extra whitespace and newlines
        target_title = " ".join(target_title.replace("\n", " ").split())

        # Split text into lines and normalize each line
        lines = text.split("\n")
        normalized_lines = [line.strip() for line in lines]

        def is_numeric_start(text):
            """Helper function to check if text starts with a number (including decimals)"""
            parts = text.split()
            if not parts:
                return False
            first_part = parts[0]
            try:
                float(first_part)
                return True
            except ValueError:
                return False

        def is_title_line(current_idx):
            """Helper function to identify real titles vs explanatory notes"""
            if current_idx >= len(normalized_lines):
                return False

            line = normalized_lines[current_idx]
            if not line:
                return False

            # Check for split title
            combined_line = line
            if current_idx + 1 < len(normalized_lines):
                next_line = normalized_lines[current_idx + 1].strip()
                if is_numeric_start(line) and next_line and next_line[0].isupper():
                    combined_line = f"{line} {next_line}"

            words = combined_line.split()
            if not words:
                return False

            if is_numeric_start(words[0]):
                explanatory_phrases = [
                    "include",
                    "such as",
                    "for example",
                    "e.g.",
                    "i.e.",
                    "refer to",
                    "means",
                    "examples of",
                ]

                return (
                    len(words) <= 12
                    and not any(
                        phrase in combined_line.lower()
                        for phrase in explanatory_phrases
                    )
                    and not combined_line.strip().endswith(".")
                )

            return False

        def is_clause_start(current_idx):
            """Helper function to identify clause starts, including split ones"""
            if current_idx >= len(normalized_lines):
                return False, None

            line = normalized_lines[current_idx]

            # Direct match for normal format (including decimal numbers)
            if (
                line.startswith(("G ", "S ", "P "))
                and len(line.split()) > 1
                and (line.split()[1][0].isdigit() or line.split()[1][0] == ".")
            ):
                return True, line

            # Check for split format (e.g., "S\n16.1")
            if line in ["G", "S", "P"] and current_idx + 1 < len(normalized_lines):
                next_line = normalized_lines[current_idx + 1].strip()
                if next_line and (next_line[0].isdigit() or next_line[0] == "."):
                    return True, f"{line} {next_line}"

            return False, None

        # Find the last occurrence of the title
        title_indices = []
        i = 0
        while i < len(normalized_lines):
            line = " ".join(normalized_lines[i].split())
            # Check for exact match
            if line == target_title:
                title_indices.append(i)
            # Check for split title
            elif (
                i + 1 < len(normalized_lines)
                and is_numeric_start(line)
                and f"{line} {normalized_lines[i + 1]}" == target_title
            ):
                title_indices.append(i)
                i += 1  # Skip the next line as it's part of the title
            i += 1

        if not title_indices:
            return []

        last_title_index = title_indices[-1]
        clauses = []
        current_clause = ""
        in_page_break = False

        # Start processing from the line after the title
        # Remove the extra skip for split titles since we handled it during title detection
        i = last_title_index + 1

        while i < len(normalized_lines):
            line = normalized_lines[i].strip()

            if line.startswith("<npage>"):
                in_page_break = True
                i += 1
                continue

            if not line:
                i += 1
                continue

            if in_page_break:
                if is_title_line(i):
                    break
                in_page_break = False

            if is_title_line(i):
                break

            is_clause, clause_line = is_clause_start(i)
            if is_clause:
                if current_clause:
                    clauses.append(current_clause.strip())
                current_clause = clause_line
                if clause_line != normalized_lines[i]:
                    i += 1
            else:
                if current_clause and line:
                    current_clause += " " + line

            i += 1

        if current_clause:
            clauses.append(current_clause.strip())

        return clauses

    def pdf_to_image(
        self, pdf_bytes: bytes | BytesIO, page_numbers: List[int] | None = None
    ) -> List[str]:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        image_urls = []
        if page_numbers is None:
            total_pages = doc.page_count
            for i in range(total_pages):
                page = doc.load_page(i)
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                base64_string = base64.b64encode(img_bytes).decode()
                image_urls.append(f"data:image/png;base64,{base64_string}")
        else:
            for page_number in page_numbers:
                page = doc.load_page(page_number - 1)
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                base64_string = base64.b64encode(img_bytes).decode()
                image_urls.append(f"data:image/png;base64,{base64_string}")

        return image_urls

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
        if "```json" in text:
            return self.extract_json_from_markdown(text)

        # Fallback to original method for simple cases
        if text.startswith("```"):
            newline_pos = text.find("\n")
            text = text[newline_pos + 1 :]

        if text.endswith("```"):
            text = text[:-3]

        return text

    def extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON content from markdown code blocks, properly handling nested braces.
        This fixes the issue where the regex misses the last brackets due to nested JSON structure.
        """
        # Find the start of the JSON code block
        start_marker = "```json"
        end_marker = "```"

        start_pos = text.find(start_marker)
        if start_pos == -1:
            # No markdown code block found, try to extract JSON directly
            return self.extract_json_object(text)

        # Move past the start marker and any whitespace
        start_pos += len(start_marker)
        while start_pos < len(text) and text[start_pos].isspace():
            start_pos += 1

        # Find the end marker, but make sure we don't stop at ``` inside the JSON
        end_pos = text.find(end_marker, start_pos)
        if end_pos == -1:
            # No end marker found, take everything after start marker
            json_content = text[start_pos:]
        else:
            json_content = text[start_pos:end_pos]

        # Extract the JSON object from the content
        return self.extract_json_object(json_content.strip())

    def extract_json_object(self, text: str) -> str:
        """
        Extract a complete JSON object from text, properly handling nested braces.
        """
        # Find the first opening brace
        start = text.find("{")
        if start == -1:
            return text  # No JSON object found

        # Count braces to find the matching closing brace
        brace_count = 0
        i = start
        while i < len(text):
            if text[i] == "{":
                brace_count += 1
            elif text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    # Found the matching closing brace
                    return text[start : i + 1]
            i += 1

        # If we get here, the braces weren't balanced
        return text[start:]  # Return from first brace to end

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

    def find_page_by_paragraph(self, content_list, search_paragraph, threshold=0.8):
        """
        Find the page number(s) that contain a given paragraph.

        Args:
            content_list (list): List of dictionaries with 'page' and 'content' keys
            search_paragraph (str): The paragraph text to search for
            threshold (float): Similarity threshold (0.0 to 1.0) for fuzzy matching
                              1.0 means exact match, lower values allow for partial matches

        Returns:
            list: List of page numbers where the paragraph was found
        """
        search_paragraph = "\n".join(
            [line.strip() for line in search_paragraph.lower().split("\n")]
        )
        result_pages = []
        # Check for exact matches first
        for item in content_list:
            page = item["page"]
            content = item["content"].strip().lower().replace("\n", " ")

            if search_paragraph.replace("\n", " ") in content:
                result_pages.append(page)

        # If exact match found, return results
        if result_pages:
            return result_pages

        # If no exact match, try fuzzy matching
        if threshold < 1.0:
            for item in content_list:
                page = item["page"]
                content = item["content"].strip().lower().replace("\n", " ")

                # Check if significant portion of search_paragraph is in content
                common_words = set(search_paragraph.split()) & set(content.split())
                similarity = len(common_words) / len(set(search_paragraph.split()))

                if similarity >= threshold:
                    result_pages.append(page)

        # Line-by-line cross-page detection
        if not result_pages:
            # Sort content list by page number
            sorted_content = sorted(content_list, key=lambda x: x["page"])

            # Split the search paragraph into lines
            search_lines = search_paragraph.split("\n")
            if len(search_lines) == 1:  # If no newlines, try to split by periods
                potential_lines = re.split(r"(?<=[.!?])\s+", search_paragraph.strip())
                if len(potential_lines) > 1:
                    search_lines = potential_lines

            # If there's only one line, we can't use this method effectively
            if len(search_lines) <= 1:
                return result_pages

            # Initialize tracking variables
            matched_pages = []
            remaining_lines = search_lines.copy()
            start_page_idx = 0

            # Continue until all lines are matched or we've tried all pages
            while remaining_lines and (start_page_idx < len(sorted_content)):
                found_match = False
                current_page_idx = start_page_idx
                current_page = sorted_content[current_page_idx]
                current_content = current_page["content"].strip().lower()

                # Try matching with different numbers of lines
                for num_lines in range(len(remaining_lines), 0, -1):
                    chunk = " ".join(remaining_lines[:num_lines]).lower()

                    # Check if this chunk is in the current page
                    if chunk in current_content.replace("\n", " "):
                        # Match found on this page
                        matched_pages.append(current_page["page"])
                        remaining_lines = remaining_lines[
                            num_lines:
                        ]  # Remove matched lines
                        found_match = True
                        start_page_idx = (
                            current_page_idx + 1
                        )  # Move to next page for next iteration
                        break

                # If no match found with any number of lines on the current page
                if not found_match:
                    start_page_idx += 1  # Try the next page

            # Check if we matched all lines across multiple pages
            if not remaining_lines and len(matched_pages) > 0:
                # Check for consecutive pages
                is_consecutive = True
                for i in range(len(matched_pages) - 1):
                    if matched_pages[i] + 1 != matched_pages[i + 1]:
                        is_consecutive = False
                        break

                if is_consecutive:
                    return matched_pages

            # If we reach here with no results, try one more approach for two-page spans
            # This is a fallback for cases where the line-by-line approach doesn't work
            if len(sorted_content) >= 2:
                for i in range(len(sorted_content) - 1):
                    current_page = sorted_content[i]
                    next_page = sorted_content[i + 1]

                    # Only consider consecutive pages
                    if next_page["page"] != current_page["page"] + 1:
                        continue

                    # Get content from both pages
                    current_content = "\n".join(
                        [line for line in current_page["content"].lower().split("\n")]
                    )
                    next_content = "\n".join(
                        [line for line in next_page["content"].lower().split("\n")]
                    )

                    # Check if first part is at the end of current page
                    # and second part is at the beginning of next page
                    if search_paragraph.replace("\n", " ") in (
                        current_content + "\n" + next_content
                    ).replace("\n", " "):
                        return [current_page["page"], next_page["page"]]

        return result_pages

    def extract_with_pdfplumber(self, pdf_bytes: Union[BytesIO, bytes]) -> str:
        markdown_content = []
        with pdfplumber.open(pdf_bytes) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                section_md = []

                # --- Extract page text ---
                text = page.extract_text()
                if text and text.strip():
                    section_md.append(text.strip())

                # --- Extract tables ---
                tables = page.extract_tables()
                for i, table in enumerate(tables):
                    if not table or not table[0]:
                        continue

                    # Create DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0])

                    # Format table in Markdown
                    md_table = tabulate(
                        df.values.tolist(), headers=df.columns.tolist(), tablefmt="pipe"
                    )
                    section_md.append(md_table)

                # Append the page content to the document
                markdown_content.append("\n\n".join(section_md))

        return "\n\n---\n\n".join(markdown_content)

    def extract_with_docling(self, pdf_bytes: Union[BytesIO, bytes]) -> str:
        """
        Extract text and tables from a PDF using Docling.
        """
        with st.spinner("Loading Documents"):

            runpod.api_key = os.getenv("RUNPOD_API_KEY")

            pods = runpod.get_pods()
            if pods is None or len(pods) == 0:
                return None

            # Call the Docling API (replace with your actual API URL)
            api_url = f"https://{pods[0].get('id')}-5001.proxy.runpod.net/v1alpha/convert/file"

            # Upload the PDF file
            files = {"files": ("document.pdf", pdf_bytes)}
            data = {
                "do_table_structure": True,
                "image_export_mode": "placeholder",
            }
            response = requests.post(api_url, files=files, data=data)

            response.raise_for_status()  # Return the JSON response
            return response.json()["document"]["md_content"].replace('"', "'")

    def extract_json_with_improved_regex(self, text: str) -> str:
        import re
        import json

        # First try to find ```json blocks
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            json_content = match.group(1)
            # Remove comments from the JSON content
            json_content = self._remove_json_comments(json_content)
            # Debug: Print the problematic area around the error
            try:
                json.loads(json_content)
                return json_content
            except json.JSONDecodeError as e:
                print(f"JSON Error at line {e.lineno}, column {e.colno}: {e.msg}")
                # Print the problematic line and surrounding context
                lines = json_content.split("\n")
                error_line = e.lineno - 1
                start_line = max(0, error_line - 2)
                end_line = min(len(lines), error_line + 3)

                print("Context around error:")
                for i in range(start_line, end_line):
                    marker = ">>> " if i == error_line else "    "
                    print(f"{marker}Line {i+1}: {lines[i]}")

                # Try to fix common JSON issues
                json_content = self._fix_common_json_issues(json_content)
                try:
                    json.loads(json_content)
                    return json_content
                except json.JSONDecodeError:
                    # If still failing, fallback to brace counting method
                    cleaned_text = self._remove_json_comments(
                        self.extract_json_from_markdown(text)
                    )
                    return cleaned_text

        # If no markdown blocks, try to extract JSON directly
        extracted = self.extract_json_object(text)
        return self._remove_json_comments(extracted)

    # def extract_json_with_improved_regex(self, text: str) -> str:
    #     import re
    #     import json

    #     # First try to find ```json blocks
    #     pattern = r"```json\s*(\{.*?\})\s*```"
    #     match = re.search(pattern, text, re.DOTALL)

    #     if match:
    #         json_content = match.group(1)
    #         # Remove comments from the JSON content
    #         json_content = self._remove_json_comments(json_content)
    #         # Escape double quotes in string values
    #         json_content = self._escape_quotes_in_json_values(json_content)
    #         # Debug: Print the problematic area around the error
    #         try:
    #             json.loads(json_content)
    #             return json_content
    #         except json.JSONDecodeError as e:
    #             print(f"JSON Error at line {e.lineno}, column {e.colno}: {e.msg}")
    #             # Print the problematic line and surrounding context
    #             lines = json_content.split("\n")
    #             error_line = e.lineno - 1
    #             start_line = max(0, error_line - 2)
    #             end_line = min(len(lines), error_line + 3)

    #             print("Context around error:")
    #             for i in range(start_line, end_line):
    #                 marker = ">>> " if i == error_line else "    "
    #                 print(f"{marker}Line {i+1}: {lines[i]}")

    #             # Try to fix common JSON issues
    #             json_content = self._fix_common_json_issues(json_content)
    #             try:
    #                 json.loads(json_content)
    #                 return json_content
    #             except json.JSONDecodeError:
    #                 # If still failing, fallback to brace counting method
    #                 cleaned_text = self._remove_json_comments(
    #                     self.extract_json_from_markdown(text)
    #                 )
    #                 cleaned_text = self._escape_quotes_in_json_values(cleaned_text)
    #                 return cleaned_text

    #     # If no markdown blocks, try to extract JSON directly
    #     extracted = self.extract_json_object(text)
    #     extracted = self._remove_json_comments(extracted)
    #     extracted = self._escape_quotes_in_json_values(extracted)
    #     return extracted

    def _escape_quotes_in_json_values(self, text: str) -> str:
        """Escape double quotes inside JSON string values while preserving JSON structure quotes."""
        import re

        def escape_quotes_in_string_value(match):
            # Get the full match and the content inside the quotes
            quote_start = match.group(1)  # Opening quote
            content = match.group(2)  # Content between quotes
            quote_end = match.group(3)  # Closing quote

            # Only escape unescaped quotes within the content
            # First, temporarily replace already escaped quotes
            temp_marker = "___TEMP_ESCAPED_QUOTE___"
            content = content.replace('\\"', temp_marker)

            # Now escape any remaining unescaped quotes
            content = content.replace('"', '\\"')

            # Restore the originally escaped quotes
            content = content.replace(temp_marker, '\\"')

            return quote_start + content + quote_end

        # Pattern to match complete JSON string values (including the surrounding quotes)
        # This matches: "any string content including quotes"
        # But only when it's a complete string value, not structural JSON quotes
        pattern = r'(")((?:[^"\\]|\\.)*)(")'

        # We need to be more careful - only process strings that are actual values
        # Split by lines and process each line to avoid matching structural quotes
        lines = text.split("\n")
        processed_lines = []

        for line in lines:
            # Skip lines that are just structural JSON (opening/closing braces, etc.)
            stripped = line.strip()
            if stripped in ["{", "}", "[", "]", ","]:
                processed_lines.append(line)
                continue

            # For lines with key-value pairs, only process the value part
            if ":" in line:
                # Split at the first colon
                colon_pos = line.find(":")
                key_part = line[: colon_pos + 1]
                value_part = line[colon_pos + 1 :]

                # Only process the value part if it contains quoted strings
                if '"' in value_part:
                    value_part = re.sub(
                        pattern, escape_quotes_in_string_value, value_part
                    )

                processed_lines.append(key_part + value_part)
            else:
                # For lines without colons, process if they contain quoted strings
                if '"' in line and not (
                    stripped.startswith('"')
                    and stripped.endswith('"')
                    and stripped.count('"') == 2
                ):
                    line = re.sub(pattern, escape_quotes_in_string_value, line)
                processed_lines.append(line)

        return "\n".join(processed_lines)

    def _fix_common_json_issues(self, text: str) -> str:
        import re

        # Fix missing commas between array elements or object properties
        # This regex looks for } or ] followed by whitespace and then { or "
        text = re.sub(r'(\}|\])\s*(\{|")', r"\1,\2", text)

        # Fix missing commas after closing braces/brackets when followed by quotes
        text = re.sub(r'(\})\s*(")', r"\1,\2", text)

        # Fix trailing commas before closing braces/brackets
        text = re.sub(r",(\s*[\}\]])", r"\1", text)

        return text

    def _is_complete_json_object(self, text: str) -> bool:
        """Check if the text contains a complete JSON object with balanced braces."""
        import json

        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    # def _remove_json_comments(self, text: str) -> str:
    #     """Remove comments from JSON content while preserving valid JSON structure."""
    #     import re

    #     # Remove single-line comments (// comment)
    #     # But be careful not to remove // inside strings
    #     lines = text.split("\n")
    #     cleaned_lines = []

    #     for line in lines:
    #         # Find // that are not inside strings
    #         in_string = False
    #         escape_next = False
    #         comment_start = -1

    #         for i, char in enumerate(line):
    #             if escape_next:
    #                 escape_next = False
    #                 continue

    #             if char == "\\":
    #                 escape_next = True
    #                 continue

    #             if char == '"' and not escape_next:
    #                 in_string = not in_string
    #                 continue

    #             if (
    #                 not in_string
    #                 and char == "/"
    #                 and i + 1 < len(line)
    #                 and line[i + 1] == "/"
    #             ):
    #                 comment_start = i
    #                 break

    #         if comment_start >= 0:
    #             line = line[:comment_start].rstrip()

    #         cleaned_lines.append(line)

    #     cleaned_text = "\n".join(cleaned_lines)

    #     # Remove multi-line comments (/* comment */)
    #     # Again, be careful about strings
    #     cleaned_text = re.sub(r"/\*.*?\*/", "", cleaned_text, flags=re.DOTALL)

    #     return cleaned_text

    def _remove_json_comments(self, text: str) -> str:
        import re

        # Remove single-line comments (// comment)
        # But be careful not to remove // inside strings
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Find // that are not inside strings, considering escaped quotes
            in_string = False
            i = 0
            comment_start = -1

            while i < len(line):
                char = line[i]

                # Handle escaped characters (including escaped quotes)
                if char == "\\" and i + 1 < len(line):
                    # Skip the escaped character entirely - this preserves \"
                    i += 2
                    continue

                # Handle string delimiters (only unescaped quotes)
                if char == '"':
                    in_string = not in_string
                elif (
                    not in_string
                    and char == "/"
                    and i + 1 < len(line)
                    and line[i + 1] == "/"
                ):
                    comment_start = i
                    break

                i += 1

            if comment_start >= 0:
                line = line[:comment_start].rstrip()

            cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines)

        # Remove multi-line comments (/* comment */) while preserving escaped quotes
        # Use a more careful approach that respects string boundaries
        result = []
        i = 0
        in_string = False

        while i < len(cleaned_text):
            char = cleaned_text[i]

            # Handle escaped characters (preserve them exactly)
            if char == "\\" and i + 1 < len(cleaned_text):
                result.append(char)
                result.append(cleaned_text[i + 1])
                i += 2
                continue

            # Handle string delimiters
            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
            elif (
                not in_string
                and char == "/"
                and i + 1 < len(cleaned_text)
                and cleaned_text[i + 1] == "*"
            ):
                # Found start of multi-line comment outside of string
                # Skip until we find the end
                i += 2  # Skip /*
                while i + 1 < len(cleaned_text):
                    if cleaned_text[i] == "*" and cleaned_text[i + 1] == "/":
                        i += 2  # Skip */
                        break
                    i += 1
            else:
                result.append(char)
                i += 1

        return "".join(result)

    def extract_json_object_preserve_escapes(self, text: str) -> str:
        """
        Extract a complete JSON object from text, properly handling nested braces and preserving escaped quotes.
        """
        # Find the first opening brace
        start = text.find("{")
        if start == -1:
            return text  # No JSON object found

        # Count braces to find the matching closing brace, handling escaped quotes
        brace_count = 0
        i = start
        in_string = False

        while i < len(text):
            char = text[i]

            # Handle escaped characters (including escaped quotes)
            if char == "\\" and i + 1 < len(text):
                i += 2  # Skip the escaped character
                continue

            # Handle string delimiters
            if char == '"':
                in_string = not in_string
            elif not in_string:
                # Only count braces when we're not inside a string
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        # Found the matching closing brace
                        return text[start : i + 1]

            i += 1

        # If we get here, the braces weren't balanced
        return text[start:]  # Return from first brace to end

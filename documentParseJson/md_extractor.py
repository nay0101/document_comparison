import json, re
from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional, Literal, Union
from openai import OpenAI
from openai.types.responses import ResponseUsage
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import base64
from .output_schema import Document
from base64 import b64encode
import pymupdf
from pypdf import PdfReader, PdfWriter
import io

# ============ Prompts & Schema ============
SCHEMA = json.loads(
    Path(Path(__file__).with_name("layout_schema.json")).read_text(encoding="utf-8")
)
SYSTEM_PROMPT = Path(Path(__file__).with_name("prompt_system.md")).read_text(
    encoding="utf-8"
)
SYSTEM_PROMPT_IMAGE_MODE = Path(
    Path(__file__).with_name("prompt_system_image_mode.md")
).read_text(encoding="utf-8")
USER_TEMPLATE = Path(Path(__file__).with_name("prompt_user_template.md")).read_text(
    encoding="utf-8"
)
USER_TEMPLATE_IMAGE_MODE = Path(
    Path(__file__).with_name("prompt_user_template_image_mode.md")
).read_text(encoding="utf-8")


def esc_md(s: str) -> str:
    return (
        s.replace("|", "\\|")
        .replace("`", "\\`")
        .replace("_", "\\_")
        .replace("<", "\\<")
        .replace(">", "\\>")
    )


def render_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    head = rows[0]
    out = []
    out.append("| " + " | ".join(esc_md(c) for c in head) + " |")
    out.append("| " + " | ".join(["---"] * len(head)) + " |")
    for r in rows[1:]:
        out.append("| " + " | ".join(esc_md(c) for c in r) + " |")
    return "\n".join(out)


def render_block_md(b: Dict[str, Any]) -> str:
    k = b.get("kind")
    if k == "heading":
        return "#" * int(b.get("level", 2)) + " " + esc_md(b.get("text", ""))
    if k == "paragraph":
        return esc_md(b.get("text", ""))
    if k == "list":
        bullet = "1. " if b.get("ordered") else "- "
        return "\n".join(bullet + esc_md(item) for item in b.get("items", []))
    if k == "table":
        return render_table(b.get("rows", []))
    if k == "code":
        lang = b.get("lang") or ""
        return f"```{lang}\n{b.get('code','')}\n```"
    if k == "figure":
        alt = esc_md(b.get("alt", ""))
        md = f"![{alt}](figure.png)"
        if b.get("caption"):
            md += f"\n*{esc_md(b['caption'])}*"
        return md
    if k == "footnote":
        return f"[^{esc_md(b.get('ref',''))}]: {esc_md(b.get('text',''))}"
    return ""


def extract_section_number(text: str) -> tuple[int | None, int | None]:
    """Extract main section number and subsection number from heading text.
    Returns (main_section, subsection) where subsection is None for main sections.
    Examples: '9' -> (9, None), '9.2' -> (9, 2), 'G 9.3.5' -> (9, 3), 'S 8.1' -> (8, 1)
    """
    # Match patterns like "9", "9.1", "G 9.3.5", "S 8.1", etc.
    # Allow optional letter prefix and "Section" prefix
    match = re.match(
        r"^(?:[A-Z]\s+)?(?:Section\s+)?(\d+)(?:\.(\d+))?", text.strip(), re.IGNORECASE
    )
    if match:
        main_section = int(match.group(1))
        subsection = int(match.group(2)) if match.group(2) else None
        return main_section, subsection
    return None, None


def _is_toc_candidate_page(blocks: List[Dict[str, Any]]) -> bool:
    """Check if a page only contains headings, lists, and tables (potential TOC page)."""
    for block in blocks:
        kind = block.get("kind", "")
        # If we find substantial content (paragraphs), this is not a TOC candidate page
        if kind == "paragraph":
            return False
    return True


def extract_toc_items(doc_json: Dict[str, Any]) -> List[str]:
    """Extract all TOC items from consecutive TOC blocks in the document.
    Also includes any 'list' blocks that appear before the first TOC block,
    but only within the first 10 pages.
    Additionally, for the first 5 pages, if a page only contains headings, lists,
    and tables (no paragraphs), then list blocks from those pages are considered
    potential TOC items.
    """
    toc_items = []
    found_toc = False
    pre_toc_lists = []
    toc_candidate_lists = []

    # First pass: collect all TOC candidate lists from first 5 pages
    for page_index, page in enumerate(doc_json.get("pages", [])):
        if page_index >= 5:  # Only consider first 5 pages for TOC candidates
            break

        page_blocks = page.get("blocks", [])
        is_toc_candidate = _is_toc_candidate_page(page_blocks)

        if is_toc_candidate:
            for b in page_blocks:
                if b.get("kind") == "list":
                    toc_candidate_lists.append(b)

    # Add TOC candidate lists first
    if toc_candidate_lists:
        for list_block in toc_candidate_lists:
            list_items = list_block.get("items", [])
            toc_items.extend(list_items)

    # Second pass: process all pages for TOC blocks and pre-TOC lists
    for page_index, page in enumerate(doc_json.get("pages", [])):
        # Only consider pages within the first 10 pages for TOC detection (0-based indexing)
        if page_index >= 10:
            break

        page_blocks = page.get("blocks", [])

        # For first 5 pages, check if page only contains headings, lists, and tables
        is_first_5_pages = page_index < 5
        is_toc_candidate = (
            _is_toc_candidate_page(page_blocks) if is_first_5_pages else False
        )

        for b in page_blocks:
            if b.get("kind") == "toc":
                # If this is the first TOC block, add any collected pre-TOC lists
                if not found_toc:
                    if pre_toc_lists:
                        for list_block in pre_toc_lists:
                            list_items = list_block.get("items", [])
                            toc_items.extend(list_items)

                found_toc = True
                items = b.get("items", [])
                toc_items.extend(items)
            elif b.get("kind") == "list" and not found_toc:
                # Skip lists from TOC candidate pages as they're already processed
                if not (is_first_5_pages and is_toc_candidate):
                    # Collect list blocks that appear before any TOC block (original logic)
                    pre_toc_lists.append(b)

    return toc_items


def find_toc_position(doc_json: Dict[str, Any]) -> int:
    """Find the position (block index) where TOC starts in the document.
    If there are list blocks before the first TOC block (within first 10 pages),
    returns the position of the first such list.
    Additionally, for the first 5 pages, if a page only contains headings, lists,
    and tables (no paragraphs), then the first list block from those pages is considered
    the TOC start position.
    Returns -1 if no TOC is found."""
    block_index = 0
    first_pre_toc_list_index = None
    first_toc_candidate_list_index = None

    for page_index, page in enumerate(doc_json.get("pages", [])):
        # Only consider pages within the first 10 pages for TOC detection (0-based indexing)
        if page_index >= 10:
            break

        page_blocks = page.get("blocks", [])

        # For first 5 pages, check if page only contains headings, lists, and tables
        is_first_5_pages = page_index < 5
        is_toc_candidate = (
            _is_toc_candidate_page(page_blocks) if is_first_5_pages else False
        )

        for b in page_blocks:
            if b.get("kind") == "toc":
                # Return the position of the first TOC-related list if found, otherwise this TOC position
                if first_toc_candidate_list_index is not None:
                    return first_toc_candidate_list_index
                elif first_pre_toc_list_index is not None:
                    return first_pre_toc_list_index
                else:
                    return block_index
            elif b.get("kind") == "list":
                if (
                    is_first_5_pages
                    and is_toc_candidate
                    and first_toc_candidate_list_index is None
                ):
                    # Record the first list block from TOC candidate pages
                    first_toc_candidate_list_index = block_index
                elif first_pre_toc_list_index is None:
                    # Record the first list block position (potential pre-TOC list)
                    first_pre_toc_list_index = block_index
            block_index += 1

    # If no TOC block was found, return the position of TOC candidate lists if available
    if first_toc_candidate_list_index is not None:
        return first_toc_candidate_list_index

    return -1


def split_blocks_by_toc(
    doc_json: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split all blocks into pre-TOC and post-TOC blocks.
    Returns (pre_toc_blocks, post_toc_blocks).
    Each block will have additional 'page_info' containing page_number and image_path.
    Also treats any 'list' blocks before the first TOC block as part of the TOC boundary,
    but only within the first 10 pages.
    Additionally, for the first 5 pages, if a page only contains headings, lists,
    and tables (no paragraphs), then list blocks from those pages are considered
    part of the TOC boundary.
    """
    all_blocks = []
    toc_started = False
    found_toc = False
    pre_toc_blocks = []
    post_toc_blocks = []
    pre_toc_list_started = False
    toc_candidate_list_started = False

    for page_index, page in enumerate(doc_json.get("pages", [])):
        page_number = page.get("page_number", 1)
        image_path = page.get("image_path")

        page_blocks = page.get("blocks", [])

        # For first 5 pages, check if page only contains headings, lists, and tables
        is_first_5_pages = page_index < 5
        is_toc_candidate = (
            _is_toc_candidate_page(page_blocks) if is_first_5_pages else False
        )

        for b in page_blocks:
            # Skip footnotes as they're handled separately
            if b.get("kind") == "footnote":
                continue

            if b.get("kind") == "toc":
                found_toc = True
                toc_started = True
                continue  # Skip TOC blocks themselves
            elif b.get("kind") == "list" and not found_toc:
                if is_first_5_pages and is_toc_candidate:
                    # Mark that we've found a TOC candidate list (first 5 pages with only headings/lists/tables)
                    toc_candidate_list_started = True
                    continue  # Skip TOC candidate list blocks
                elif page_index < 10:
                    # Mark that we've found a pre-TOC list (only within first 10 pages, 0-based indexing)
                    pre_toc_list_started = True
                    continue  # Skip pre-TOC list blocks as they're now considered part of TOC

            # Create a copy of the block with page info
            block_with_page = b.copy()
            block_with_page["page_info"] = {
                "page_number": page_number,
                "image_path": image_path,
            }

            # If we haven't started TOC yet, and haven't found any pre-TOC lists or TOC candidate lists
            if (
                not toc_started
                and not pre_toc_list_started
                and not toc_candidate_list_started
            ):
                pre_toc_blocks.append(block_with_page)
            else:
                post_toc_blocks.append(block_with_page)

    return pre_toc_blocks, post_toc_blocks


def normalize_toc_item(item: str) -> str:
    """Normalize TOC item for matching with headings."""
    # Remove leading hash symbols for headings
    normalized = re.sub(r"^#+\s*", "", item.strip())
    # Remove leading numbers, dots, and whitespace
    normalized = re.sub(r"^\d+\.?\s*", "", normalized)
    # Remove common prefixes
    normalized = re.sub(
        r"^(PART\s+[A-Z]+\s+|Section\s+)", "", normalized, flags=re.IGNORECASE
    )

    # Enhanced normalization for better matching
    # 1. Remove all round brackets and their content
    normalized = re.sub(r"\s*\([^)]*\)", "", normalized)

    # 2. Remove footnote references like [^8] or [8]
    normalized = re.sub(r"\[\^?\d+\]", "", normalized)

    # 3. Remove trailing numbers without spacing (like Products18 -> Products)
    # This handles cases where words end with numbers
    normalized = re.sub(r"\b([a-zA-Z]+)\d+\b", r"\1", normalized)

    # 4. Normalize multiple spaces to single spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # 5. Normalize slash spacing: remove spaces around slashes
    normalized = re.sub(r"\s*/\s*", "/", normalized)

    # 6. Convert to lowercase for case-insensitive matching
    normalized = normalized.lower()

    return normalized.strip()


def texts_match_flexibly(toc_text: str, heading_text: str) -> bool:
    """Check if two texts match with flexible rules for common variations."""
    # Get normalized versions (now includes bracket removal)
    norm_toc = normalize_toc_item(toc_text)
    norm_heading = normalize_toc_item(heading_text)

    # 1. Try exact match first
    if norm_toc == norm_heading:
        return True

    # 2. Try partial matching with high overlap for longer texts
    if len(norm_toc) > 15 and len(norm_heading) > 15:
        # Skip generic terms that could match anything
        generic_terms = []
        if any(term in norm_toc for term in generic_terms) and any(
            term in norm_heading for term in generic_terms
        ):
            # For generic terms, require very high similarity
            if norm_toc in norm_heading:
                overlap_ratio = len(norm_toc) / len(norm_heading)
                return overlap_ratio > 0.95
            elif norm_heading in norm_toc:
                overlap_ratio = len(norm_heading) / len(norm_toc)
                return overlap_ratio > 0.95
        else:
            # For non-generic terms, use standard overlap
            if norm_toc in norm_heading:
                overlap_ratio = len(norm_toc) / len(norm_heading)
                return overlap_ratio > 0.9
            elif norm_heading in norm_toc:
                overlap_ratio = len(norm_heading) / len(norm_toc)
                return overlap_ratio > 0.9

    return False


def find_matching_heading_in_content(
    toc_item: str, all_blocks: List[Dict[str, Any]]
) -> Dict[str, Any] | None:
    """Find a heading block that matches the TOC item."""
    normalized_toc = normalize_toc_item(toc_item).lower()

    for block in all_blocks:
        if block.get("kind") == "heading":
            heading_text = block.get("text", "")
            normalized_heading = normalize_toc_item(heading_text).lower()

            # Check for exact match or if one contains the other
            if (
                normalized_toc == normalized_heading
                or normalized_toc in normalized_heading
                or normalized_heading in normalized_toc
            ):
                return block

    return None


def group_pre_toc_blocks(
    blocks: List[Dict[str, Any]], all_footnotes: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Apply the same sectioning logic as group_by_section_original to pre-TOC blocks."""
    pairs = []
    current = None
    current_main_section = None

    for b in blocks:
        # Skip footnotes
        if b.get("kind") == "footnote":
            continue

        # Check for headings that could be new sections (level 1 - 4)
        if b.get("kind") == "heading" and b.get("level") in [1, 2, 3, 4]:
            heading_text = b.get("text", "")
            main_section, subsection = extract_section_number(heading_text)

            # Determine if this should be a new section or subsection
            is_new_main_section = False

            if b.get("level") == 1:
                # Level 1 headings: new section unless it's a subsection of current
                if (
                    current is not None
                    and current_main_section is not None
                    and main_section == current_main_section
                    and subsection is not None
                ):
                    # This is a subsection of current main section
                    is_new_main_section = False
                else:
                    # This is a new main section
                    is_new_main_section = True

            elif b.get("level") != 1:
                # Level 2 headings: new section if it's a different main section number
                if main_section is not None and (
                    current_main_section is None or main_section != current_main_section
                ):
                    # This level 2 heading is actually a new main section
                    is_new_main_section = True
                else:
                    # This is a regular subsection
                    is_new_main_section = False

            if is_new_main_section:
                # Finalize previous section if it exists
                if current:
                    current["content_md"] = "\n\n".join(current["content"])
                    del current["content"]
                    # Ensure images list exists and remove duplicates
                    current["images"] = list(
                        set(filter(None, current.get("images", [])))
                    )
                    pairs.append(current)

                # Start new section using the actual heading text
                header_label = heading_text if heading_text else "Untitled Section"
                current = {"header": header_label, "content": [], "images": []}
                current_main_section = main_section

                # For level 2 headings that become main sections, keep them as level 1
                if b.get("level") != 1:
                    main_section_block = b.copy()
                    main_section_block["level"] = 1  # Promote to level 1
                    current["content"].append(render_block_md(main_section_block))
                else:
                    current["content"].append(render_block_md(b))

                # Add image path if available
                page_info = b.get("page_info")
                if page_info and page_info.get("image_path"):
                    current["images"].append(page_info["image_path"])
                continue
            else:
                # This is a subsection - add to current section with appropriate level
                if current is not None:
                    subsection_block = b.copy()
                    # Ensure subsections are at least level 2
                    if subsection_block["level"] == 1:
                        subsection_block["level"] = 2
                    md = render_block_md(subsection_block)
                    if md:
                        current["content"].append(md)

                    # Add image path if available
                    page_info = b.get("page_info")
                    if page_info and page_info.get("image_path"):
                        current["images"].append(page_info["image_path"])
                    continue

        # If no current section exists, create an unknown section
        if current is None:
            current = {"header": "Section (unknown)", "content": [], "images": []}
            current_main_section = None

        # Add block content to current section
        md = render_block_md(b)
        if md:
            current["content"].append(md)

        # Add image path if available
        page_info = b.get("page_info")
        if page_info and page_info.get("image_path"):
            current["images"].append(page_info["image_path"])

    # Finalize the last section
    if current:
        current["content_md"] = "\n\n".join(current["content"])
        del current["content"]
        # Ensure images list exists and remove duplicates
        current["images"] = list(set(filter(None, current.get("images", []))))
        pairs.append(current)

    # Second pass: Find footnote references in each section and add footnotes
    for section in pairs:
        content_md = section["content_md"]
        # Find all footnote references in this section's content
        footnote_refs = re.findall(r"\[(\^[^\]]+)\]", content_md)

        footnotes_to_add = []
        for ref in footnote_refs:
            # Remove the ^ prefix to match footnote ref format
            clean_ref = ref[1:] if ref.startswith("^") else ref
            if clean_ref in all_footnotes:
                footnote_md = render_block_md(all_footnotes[clean_ref])
                if footnote_md and footnote_md not in footnotes_to_add:
                    footnotes_to_add.append(footnote_md)

        # Add footnotes to the section's content
        if footnotes_to_add:
            section["content_md"] += "\n\n" + "\n\n".join(footnotes_to_add)

    return pairs


def group_by_section(doc_json: Dict[str, Any]) -> List[Dict[str, str]]:
    # Collect all footnotes first
    all_footnotes = {}  # ref -> footnote block

    for page in doc_json.get("pages", []):
        for b in page.get("blocks", []):
            if b.get("kind") == "footnote":
                ref = b.get("ref", "")
                if ref:
                    all_footnotes[ref] = b

    # Try to extract TOC items
    toc_items = extract_toc_items(doc_json)

    if toc_items:
        # Split blocks into pre-TOC and post-TOC
        pre_toc_blocks, post_toc_blocks = split_blocks_by_toc(doc_json)

        # Process pre-TOC blocks with normal sectioning
        pre_toc_sections = []
        if pre_toc_blocks:
            pre_toc_sections = group_pre_toc_blocks(pre_toc_blocks, all_footnotes)

        # Process post-TOC blocks with TOC-based sectioning
        post_toc_sections = group_by_section_with_toc(
            doc_json, toc_items, all_footnotes, post_toc_blocks
        )

        # Combine both sections
        return pre_toc_sections + post_toc_sections
    else:
        # Fall back to original logic for entire document
        return group_by_section_original(doc_json, all_footnotes)


def group_by_section_with_toc(
    doc_json: Dict[str, Any],
    toc_items: List[str],
    all_footnotes: Dict[str, Any],
    post_toc_blocks: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Group sections based on TOC items, but use original logic for early sections before TOC matching begins."""

    # First pass: find where TOC-based matching actually starts working
    toc_match_start_index = find_toc_matching_start(post_toc_blocks, toc_items)

    # Split blocks into pre-TOC-matching and TOC-matching sections
    pre_toc_matching_blocks = []
    toc_matching_blocks = []

    current_block_index = 0
    for b in post_toc_blocks:
        if current_block_index < toc_match_start_index:
            pre_toc_matching_blocks.append(b)
        else:
            toc_matching_blocks.append(b)
        current_block_index += 1

    # Process pre-TOC-matching blocks with original logic
    pre_toc_matching_sections = []
    if pre_toc_matching_blocks:
        pre_toc_matching_sections = group_blocks_with_original_logic(
            pre_toc_matching_blocks, all_footnotes
        )

    # Process TOC-matching blocks with TOC-based logic
    toc_based_sections = []
    if toc_matching_blocks:
        toc_based_sections = group_blocks_with_toc_logic(
            toc_matching_blocks, toc_items, all_footnotes, toc_match_start_index
        )

    return pre_toc_matching_sections + toc_based_sections


def find_toc_matching_start(
    post_toc_blocks: List[Dict[str, Any]], toc_items: List[str]
) -> int:
    """Find the block index where reliable TOC matching starts."""
    for block_index, b in enumerate(post_toc_blocks):
        if b.get("kind") == "heading":
            heading_text = b.get("text", "")

            # Check if this heading matches any TOC item
            for toc_item in toc_items:
                if texts_match_flexibly(toc_item, heading_text):
                    return block_index

    # If no TOC matches found, use original logic for all blocks
    return len(post_toc_blocks)


def group_blocks_with_original_logic(
    blocks: List[Dict[str, Any]], all_footnotes: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Apply original sectioning logic to a set of blocks."""
    pairs = []
    current = None
    current_main_section = None

    for b in blocks:
        # Skip footnotes
        if b.get("kind") == "footnote":
            continue

        # Check for headings that could be new sections (level 1 - 4)
        if b.get("kind") == "heading" and b.get("level") in [1, 2, 3, 4]:
            heading_text = b.get("text", "")
            main_section, subsection = extract_section_number(heading_text)

            # Determine if this should be a new section or subsection
            is_new_main_section = False

            if b.get("level") == 1:
                # Level 1 headings: new section unless it's a subsection of current
                if (
                    current is not None
                    and current_main_section is not None
                    and main_section == current_main_section
                    and subsection is not None
                ):
                    # This is a subsection of current main section
                    is_new_main_section = False
                else:
                    # This is a new main section
                    is_new_main_section = True

            elif b.get("level") != 1:
                # Level 2 headings: new section if it's a different main section number
                if main_section is not None and (
                    current_main_section is None or main_section != current_main_section
                ):
                    # This level 2 heading is actually a new main section
                    is_new_main_section = True
                else:
                    # This is a regular subsection
                    is_new_main_section = False

            if is_new_main_section:
                # Finalize previous section if it exists
                if current:
                    current["content_md"] = "\n\n".join(current["content"])
                    del current["content"]
                    # Ensure images list exists and remove duplicates
                    current["images"] = list(
                        set(filter(None, current.get("images", [])))
                    )
                    pairs.append(current)

                # Start new section using the actual heading text
                header_label = heading_text if heading_text else "Untitled Section"
                current = {"header": header_label, "content": [], "images": []}
                current_main_section = main_section

                # For level 2 headings that become main sections, keep them as level 1
                if b.get("level") != 1:
                    main_section_block = b.copy()
                    main_section_block["level"] = 1  # Promote to level 1
                    current["content"].append(render_block_md(main_section_block))
                else:
                    current["content"].append(render_block_md(b))

                # Add image path if available
                page_info = b.get("page_info")
                if page_info and page_info.get("image_path"):
                    current["images"].append(page_info["image_path"])
                continue
            else:
                # This is a subsection - add to current section with appropriate level
                if current is not None:
                    subsection_block = b.copy()
                    # Ensure subsections are at least level 2
                    if subsection_block["level"] == 1:
                        subsection_block["level"] = 2
                    md = render_block_md(subsection_block)
                    if md:
                        current["content"].append(md)

                    # Add image path if available
                    page_info = b.get("page_info")
                    if page_info and page_info.get("image_path"):
                        current["images"].append(page_info["image_path"])
                    continue

        # If no current section exists, create an unknown section
        if current is None:
            current = {"header": "Section (unknown)", "content": [], "images": []}
            current_main_section = None

        # Add block content to current section
        md = render_block_md(b)
        if md:
            current["content"].append(md)

        # Add image path if available
        page_info = b.get("page_info")
        if page_info and page_info.get("image_path"):
            current["images"].append(page_info["image_path"])

    # Finalize the last section
    if current:
        current["content_md"] = "\n\n".join(current["content"])
        del current["content"]
        # Ensure images list exists and remove duplicates
        current["images"] = list(set(filter(None, current.get("images", []))))
        pairs.append(current)

    # Add footnotes to sections
    for section in pairs:
        content_md = section["content_md"]
        # Find all footnote references in this section's content
        footnote_refs = re.findall(r"\[(\^[^\]]+)\]", content_md)

        footnotes_to_add = []
        for ref in footnote_refs:
            # Remove the ^ prefix to match footnote ref format
            clean_ref = ref[1:] if ref.startswith("^") else ref
            if clean_ref in all_footnotes:
                footnote_md = render_block_md(all_footnotes[clean_ref])
                if footnote_md and footnote_md not in footnotes_to_add:
                    footnotes_to_add.append(footnote_md)

        # Add footnotes to the section's content
        if footnotes_to_add:
            section["content_md"] += "\n\n" + "\n\n".join(footnotes_to_add)

    return pairs


def group_blocks_with_toc_logic(
    blocks: List[Dict[str, Any]],
    toc_items: List[str],
    all_footnotes: Dict[str, Any],
    start_toc_index: int = 0,
) -> List[Dict[str, str]]:
    """Apply TOC-based sectioning logic to blocks."""
    pairs = []
    current = None
    toc_index = start_toc_index  # Start from where TOC matching begins
    used_toc_items = set()  # Track which TOC items have been used

    for b in blocks:
        # Check if this is a heading that matches the next expected TOC item
        if b.get("kind") == "heading":
            heading_text = b.get("text", "")

            # Look for the next unused TOC item that matches this heading
            matching_toc_item = None
            matching_toc_index = None

            # Search from current toc_index onwards for the first match
            for i in range(toc_index, len(toc_items)):
                toc_item = toc_items[i]
                if toc_item in used_toc_items:
                    continue

                # Use flexible matching to handle formatting variations
                if texts_match_flexibly(toc_item, heading_text):
                    matching_toc_item = toc_item
                    matching_toc_index = i
                    break

            if matching_toc_item:
                # Finalize previous section if it exists
                if current:
                    current["content_md"] = "\n\n".join(current["content"])
                    del current["content"]
                    # Ensure images list exists and remove duplicates
                    current["images"] = list(
                        set(filter(None, current.get("images", [])))
                    )
                    pairs.append(current)

                # Start new section with matched TOC item as header
                current = {"header": matching_toc_item, "content": [], "images": []}
                used_toc_items.add(matching_toc_item)
                toc_index = matching_toc_index + 1  # Move to next TOC item

                # Add the heading as level 1
                heading_block = b.copy()
                heading_block["level"] = 1
                current["content"].append(render_block_md(heading_block))

                # Add image path if available
                page_info = b.get("page_info")
                if page_info and page_info.get("image_path"):
                    current["images"].append(page_info["image_path"])
                continue
            else:
                # This is a subsection - convert to level 2
                if current is not None:
                    subsection_block = b.copy()
                    subsection_block["level"] = 2
                    md = render_block_md(subsection_block)
                    if md:
                        current["content"].append(md)

                    # Add image path if available
                    page_info = b.get("page_info")
                    if page_info and page_info.get("image_path"):
                        current["images"].append(page_info["image_path"])
                    continue

        # If no current section exists, create one based on next available TOC item
        if current is None:
            # Find next unused TOC item
            while toc_index < len(toc_items) and toc_items[toc_index] in used_toc_items:
                toc_index += 1

            if toc_index < len(toc_items):
                next_toc_item = toc_items[toc_index]
                current = {"header": next_toc_item, "content": [], "images": []}
                used_toc_items.add(next_toc_item)
                toc_index += 1
            else:
                current = {"header": "Section (unknown)", "content": [], "images": []}

        # Add block content to current section
        md = render_block_md(b)
        if md:
            current["content"].append(md)

        # Add image path if available
        page_info = b.get("page_info")
        if page_info and page_info.get("image_path"):
            current["images"].append(page_info["image_path"])

    # Finalize the last section
    if current:
        current["content_md"] = "\n\n".join(current["content"])
        del current["content"]
        # Ensure images list exists and remove duplicates
        current["images"] = list(set(filter(None, current.get("images", []))))
        pairs.append(current)

    # Add footnotes to sections
    for section in pairs:
        content_md = section["content_md"]
        footnote_refs = re.findall(r"\[(\^[^\]]+)\]", content_md)

        footnotes_to_add = []
        for ref in footnote_refs:
            clean_ref = ref[1:] if ref.startswith("^") else ref
            if clean_ref in all_footnotes:
                footnote_md = render_block_md(all_footnotes[clean_ref])
                if footnote_md and footnote_md not in footnotes_to_add:
                    footnotes_to_add.append(footnote_md)

        if footnotes_to_add:
            section["content_md"] += "\n\n" + "\n\n".join(footnotes_to_add)

    return pairs


def group_by_section_original(
    doc_json: Dict[str, Any], all_footnotes: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Original sectioning logic as fallback when no TOC is found."""
    pairs = []
    current = None
    current_main_section = None

    # Create a mapping of block to page and image path
    block_to_page_info = {}
    for page in doc_json.get("pages", []):
        page_number = page.get("page_number", 1)
        image_path = page.get("image_path")
        for block in page.get("blocks", []):
            block_id = id(block)  # Use object id as unique identifier
            block_to_page_info[block_id] = {
                "page_number": page_number,
                "image_path": image_path,
            }

    for page in doc_json.get("pages", []):
        for b in page.get("blocks", []):
            # Skip footnotes
            if b.get("kind") == "footnote":
                continue

            # Check for headings that could be new sections (level 1 - 4)
            if b.get("kind") == "heading" and b.get("level") in [1, 2, 3, 4]:
                heading_text = b.get("text", "")
                main_section, subsection = extract_section_number(heading_text)

                # Determine if this should be a new section or subsection
                is_new_main_section = False

                if b.get("level") == 1:
                    # Level 1 headings: new section unless it's a subsection of current
                    if (
                        current is not None
                        and current_main_section is not None
                        and main_section == current_main_section
                        and subsection is not None
                    ):
                        # This is a subsection of current main section
                        is_new_main_section = False
                    else:
                        # This is a new main section
                        is_new_main_section = True

                elif b.get("level") != 1:
                    # Level 2 headings: new section if it's a different main section number
                    if main_section is not None and (
                        current_main_section is None
                        or main_section != current_main_section
                    ):
                        # This level 2 heading is actually a new main section
                        is_new_main_section = True
                    else:
                        # This is a regular subsection
                        is_new_main_section = False

                if is_new_main_section:
                    # Finalize previous section if it exists
                    if current:
                        current["content_md"] = "\n\n".join(current["content"])
                        del current["content"]
                        # Ensure images list exists and remove duplicates
                        current["images"] = list(
                            set(filter(None, current.get("images", [])))
                        )
                        pairs.append(current)

                    # Start new section using the actual heading text
                    header_label = heading_text if heading_text else "Untitled Section"
                    current = {"header": header_label, "content": [], "images": []}
                    current_main_section = main_section

                    # For level 2 headings that become main sections, keep them as level 1
                    if b.get("level") != 1:
                        main_section_block = b.copy()
                        main_section_block["level"] = 1  # Promote to level 1
                        current["content"].append(render_block_md(main_section_block))
                    else:
                        current["content"].append(render_block_md(b))

                    # Add image path if available
                    block_info = block_to_page_info.get(id(b))
                    if block_info and block_info["image_path"]:
                        current["images"].append(block_info["image_path"])
                    continue
                else:
                    # This is a subsection - add to current section with appropriate level
                    if current is not None:
                        subsection_block = b.copy()
                        # Ensure subsections are at least level 2
                        if subsection_block["level"] == 1:
                            subsection_block["level"] = 2
                        md = render_block_md(subsection_block)
                        if md:
                            current["content"].append(md)

                        # Add image path if available
                        block_info = block_to_page_info.get(id(b))
                        if block_info and block_info["image_path"]:
                            current["images"].append(block_info["image_path"])
                        continue

            # If no current section exists, create an unknown section
            if current is None:
                current = {"header": "Section (unknown)", "content": [], "images": []}
                current_main_section = None

            # Add block content to current section
            md = render_block_md(b)
            if md:
                current["content"].append(md)

            # Add image path if available
            block_info = block_to_page_info.get(id(b))
            if block_info and block_info["image_path"]:
                current["images"].append(block_info["image_path"])

    # Finalize the last section
    if current:
        current["content_md"] = "\n\n".join(current["content"])
        del current["content"]
        # Ensure images list exists and remove duplicates
        current["images"] = list(set(filter(None, current.get("images", []))))
        pairs.append(current)

    # Second pass: Find footnote references in each section and add footnotes
    for section in pairs:
        content_md = section["content_md"]
        # Find all footnote references in this section's content
        footnote_refs = re.findall(r"\[(\^[^\]]+)\]", content_md)

        footnotes_to_add = []
        for ref in footnote_refs:
            # Remove the ^ prefix to match footnote ref format
            clean_ref = ref[1:] if ref.startswith("^") else ref
            if clean_ref in all_footnotes:
                footnote_md = render_block_md(all_footnotes[clean_ref])
                if footnote_md and footnote_md not in footnotes_to_add:
                    footnotes_to_add.append(footnote_md)

        # Add footnotes to the section's content
        if footnotes_to_add:
            section["content_md"] += "\n\n" + "\n\n".join(footnotes_to_add)

    return pairs


def chunks_document(
    pdf: Union[Path, bytes], pages_per_chunk: int, pages_limit, outdir: Path
) -> Path:
    if isinstance(pdf, bytes):
        # Handle PDF bytes
        chunks_dir = outdir / "pdf_chunks"
        chunks_dir.mkdir(exist_ok=True)
        reader = PdfReader(io.BytesIO(pdf))
    else:
        # Handle PDF path
        pdf_path = Path(pdf)
        chunks_dir = pdf_path.parent / f"{pdf_path.stem}_chunks"
        chunks_dir.mkdir(exist_ok=True)
        reader = PdfReader(str(pdf_path))

    total = len(reader.pages)
    if pages_limit and pages_limit > 0:
        total = min(total, pages_limit)
    for start in range(0, total, pages_per_chunk):
        writer = PdfWriter()
        end = min(start + pages_per_chunk, total)
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        out_path = chunks_dir / f"chunk_{start+1:04d}_to_{end:04d}.pdf"
        with out_path.open("wb") as f:
            writer.write(f)
    return chunks_dir


def iter_image_jobs(
    pdf: Union[Path, bytes],
    chunks_dir: Path | None,
    pages_per_chunk: int,
    outdir: Path,
    dpi: int = 100,
    pages_limit: int = 0,
) -> Iterable[Dict[str, Any]]:
    if chunks_dir is None:
        chunks_dir = chunks_document(pdf, pages_per_chunk, pages_limit, outdir)
    else:
        chunks_dir = Path(chunks_dir)

    for idx, p in enumerate(sorted(chunks_dir.glob("*.pdf"))):
        doc = pymupdf.open(str(p))
        outdir_images = chunks_dir.parent / f"{chunks_dir.stem}_images"
        outdir_images.mkdir(exist_ok=True)
        for i, page in enumerate(doc, start=1):
            text = page.get_text("blocks")
            blocks_sorted = sorted(text, key=lambda b: (b[1], b[0]))
            sorted_text = ""
            for b in blocks_sorted:
                sorted_text += b[4] + "\n"
            pix = page.get_pixmap(dpi=dpi)
            pth = outdir_images / f"image_{idx:04d}_{i}.png"
            pix.save(pth)
            yield {"type": "image", "path": pth, "page_number": i, "text": sorted_text}
        doc.close()


def iter_pdf_chunk_jobs(
    pdf: Union[Path, bytes],
    chunks_dir: Path | None,
    pages_per_chunk: int,
    outdir: Path,
    pages_limit: int = 0,
) -> Iterable[Dict[str, Any]]:
    if chunks_dir is None:
        # auto-split into tmp dir
        chunks_dir = chunks_document(pdf, pages_per_chunk, pages_limit, outdir)
    else:
        chunks_dir = Path(chunks_dir)

    # yield all chunk PDFs (respect pages_limit approximately by file name if present)
    for p in sorted(chunks_dir.glob("*.pdf")):
        yield {"type": "pdf", "path": p}


def call_openai_on_pdf(
    client: OpenAI,
    model: str,
    pdf: Union[Path, bytes],
    user_template: str,
    reasoning: str,
    verbosity: str,
) -> Dict[str, ResponseUsage]:
    if isinstance(pdf, bytes):
        pdf_base64 = b64encode(pdf).decode("utf-8")
    else:
        with pdf.open("rb") as f:
            pdf_bytes = f.read()
            pdf_base64 = b64encode(pdf_bytes).decode("utf-8")

    resp = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_template.format(page_count=1),
                    },
                    {
                        "type": "input_file",
                        "filename": "user_data",
                        "file_data": f"data:application/pdf;base64,{pdf_base64}",
                    },
                ],
            },
        ],
        reasoning={
            "effort": reasoning,
            "summary": None,
        },
        text={
            "verbosity": verbosity,
        },
        text_format=Document,
    )
    try:
        text = resp.output[0].content[0].text
        token_usage = resp.usage
    except Exception:
        text = resp.output_text
        token_usage = resp.usage
    return {"data": json.loads(text), "usage": token_usage}


def call_openai_on_image(
    client: OpenAI,
    model: str,
    img_path: Path,
    text: str,
    user_template: str,
    reasoning: str,
    verbosity: str,
) -> Dict[str, Any]:
    with img_path.open("rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    resp = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT_IMAGE_MODE},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_template.format(page_text=text),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}",
                    },
                ],
            },
        ],
        reasoning={
            "effort": reasoning,
            "summary": None,
        },
        text={
            "verbosity": verbosity,
        },
        text_format=Document,
    )
    try:
        text = resp.output[0].content[0].text
        token_usage = resp.usage
    except Exception:
        text = resp.output_text
        token_usage = resp.usage
    return {"data": json.loads(text), "usage": token_usage}


def process_single_chunk(
    job: Dict[str, Any],
    model: str,
    mode: Literal["pdf", "image"],
    user_template: str,
    reasoning: str,
    verbosity: str,
) -> tuple[str, Dict[Document, ResponseUsage]]:
    """Process a single PDF chunk with OpenAI API call.

    Returns:
        tuple: (chunk_name, extracted_data) where extracted_data contains 'pages' and 'usage'
    """
    client = OpenAI()

    # Handle different job types
    if "pdf_bytes" in job:
        chunk_name = "pdf_bytes"
        pdf_data = job["pdf_bytes"]
    else:
        chunk_name = job["path"].name
        pdf_data = job["path"]

    print(f"[{mode}] Extracting {chunk_name}")
    try:
        if mode == "pdf":
            data = call_openai_on_pdf(
                client, model, pdf_data, user_template, reasoning, verbosity
            )
        else:
            data = call_openai_on_image(
                client,
                model,
                img_path=job["path"],
                text=job["text"],
                user_template=user_template,
                reasoning=reasoning,
                verbosity=verbosity,
            )
        return chunk_name, data
    except Exception as e:
        print(f"[error] Failed to process {chunk_name}: {e}")
        return chunk_name, {"data": {"pages": []}, "usage": None}


def extract_layout(
    pdf: Union[Path, bytes],
    outdir: Path,
    mode: Literal["pdf", "image"] = "pdf",
    chunks_dir: Optional[Path] = None,
    reasoning: str = "minimal",
    verbosity: str = "medium",
    model: str = "gpt-5-nano",
    pages_per_chunk: int = 1,
    max_workers: int = 4,
    progress_callback=None,
    status_callback=None,
) -> Dict[str, Any]:
    """Extract layout from PDF with parallel processing.

    Args:
        pdf: Path to the input PDF file or PDF bytes data
        chunks_dir: Directory containing PDF chunks
        outdir: Output directory for results
        model: OpenAI model to use
        pages_per_chunk: Number of pages per chunk
        max_workers: Maximum number of parallel workers for API calls
        progress_callback: Optional callback function to update progress (for Streamlit progress bar)
        status_callback: Optional callback function to update status message

    Returns:
        Dict containing total token usage across all API calls with keys:
        - input_tokens: Total input tokens used
        - input_tokens_details: Details about input tokens (cached_tokens)
        - output_tokens: Total output tokens used
        - output_tokens_details: Details about output tokens (reasoning_tokens)
        - total_tokens: Total tokens used
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Initialize progress tracking
    if status_callback:
        status_callback("Preparing PDF chunks...")

    if progress_callback:
        progress_callback(0.0)

    # Handle PDF bytes appropriately for both modes
    if isinstance(pdf, bytes):
        if mode == "pdf" and chunks_dir is None and pages_per_chunk == 1:
            # Process PDF bytes directly without chunking
            jobs = [{"pdf_bytes": pdf}]
        else:
            # For image mode or chunking, we need to work with files
            # So we'll create chunks from bytes and let the existing logic handle it
            if mode == "pdf":
                jobs = list(
                    iter_pdf_chunk_jobs(
                        pdf,
                        Path(chunks_dir) if chunks_dir else None,
                        pages_per_chunk,
                        outdir,
                    )
                )
            else:
                jobs = list(
                    iter_image_jobs(
                        pdf,
                        Path(chunks_dir) if chunks_dir else None,
                        pages_per_chunk,
                        outdir,
                    )
                )
    else:
        # Use existing chunking logic for Path input
        if mode == "pdf":
            jobs = list(
                iter_pdf_chunk_jobs(
                    pdf,
                    Path(chunks_dir) if chunks_dir else None,
                    pages_per_chunk,
                    outdir,
                )
            )
        else:
            jobs = list(
                iter_image_jobs(
                    pdf,
                    Path(chunks_dir) if chunks_dir else None,
                    pages_per_chunk,
                    outdir,
                )
            )

    if status_callback:
        status_callback(f"Processing {len(jobs)} chunks with {max_workers} workers...")

    if progress_callback:
        progress_callback(0.1)

    print(f"Processing {len(jobs)} chunks with {max_workers} workers...")

    all_pages = []
    chunk_results = {}  # Store results with chunk names for ordering
    job_image_paths = {}  # Store image paths for each job
    completed_chunks = 0  # Track completed chunks for progress
    total_token_usage = {
        "input_tokens": 0,
        "input_tokens_details": {"cached_tokens": 0},
        "output_tokens": 0,
        "output_tokens_details": {"reasoning_tokens": 0},
        "total_tokens": 0,
    }

    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create partial function with fixed arguments
        process_func = partial(
            process_single_chunk,
            model=model,
            mode=mode,
            user_template=USER_TEMPLATE if mode == "pdf" else USER_TEMPLATE_IMAGE_MODE,
            reasoning=reasoning,
            verbosity=verbosity,
        )

        # Submit all jobs
        future_to_job = {executor.submit(process_func, job): job for job in jobs}

        # Store image paths from jobs for later association
        for job in jobs:
            if "pdf_bytes" in job:
                chunk_name = "pdf_bytes"
                job_image_paths[chunk_name] = None  # No image path for pdf_bytes
            elif job.get("type") == "image" and "path" in job:
                chunk_name = job["path"].name
                job_image_paths[chunk_name] = str(job["path"])
            else:
                chunk_name = job["path"].name
                job_image_paths[chunk_name] = None

        # Collect results as they complete
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            try:
                chunk_name, data = future.result()
                chunk_results[chunk_name] = data["data"]
                completed_chunks += 1

                # Update progress (processing takes 80% of total progress: 10% to 90%)
                processing_progress = 0.1 + (completed_chunks / len(jobs)) * 0.8
                if progress_callback:
                    progress_callback(processing_progress)

                if status_callback:
                    status_callback(f"Processed {completed_chunks}/{len(jobs)} chunks")

                # Accumulate token usage if available
                if "usage" in data and data["usage"]:
                    usage = data["usage"]
                    total_token_usage["input_tokens"] += usage.input_tokens
                    total_token_usage["output_tokens"] += usage.output_tokens
                    total_token_usage["total_tokens"] += usage.total_tokens
                    total_token_usage["input_tokens_details"][
                        "cached_tokens"
                    ] += usage.input_tokens_details.cached_tokens
                    total_token_usage["output_tokens_details"][
                        "reasoning_tokens"
                    ] += usage.output_tokens_details.reasoning_tokens

                print(f"[{mode}] Completed {chunk_name}")
            except Exception as e:
                # Handle both job types for error reporting
                if "pdf_bytes" in job:
                    job_name = "pdf_bytes"
                else:
                    job_name = job["path"].name
                print(f"[error] Exception for {job_name}: {e}")
                chunk_results[chunk_name] = {"pages": [], "usage": None}

    # Update progress for post-processing
    if status_callback:
        status_callback("Organizing document sections...")

    if progress_callback:
        progress_callback(0.9)

    # Reconstruct pages in the correct order based on chunk filenames
    for job in jobs:
        if "pdf_bytes" in job:
            chunk_name = "pdf_bytes"
        else:
            chunk_name = job["path"].name

        if chunk_name in chunk_results:
            pages_data = chunk_results[chunk_name].get("pages", [])
            image_path = job_image_paths.get(chunk_name)

            # Add image path to each page if available
            for page in pages_data:
                if image_path:
                    page["image_path"] = image_path

            all_pages.extend(pages_data)

    # Save document JSON
    doc_json = {"pages": all_pages}
    (outdir / "document.json").write_text(
        json.dumps(doc_json, indent=2), encoding="utf-8"
    )

    # Flat Markdown
    flat_lines = []
    for i, page in enumerate(doc_json["pages"], start=1):
        if i > 1:
            flat_lines.append(f"<!-- PAGEBREAK p={i} -->")
        for b in page.get("blocks", []):
            md = render_block_md(b)
            if md:
                flat_lines.append(md)
    (outdir / "document.md").write_text("\n\n".join(flat_lines), encoding="utf-8")

    # Header-content pairs
    pairs = group_by_section(doc_json)
    (outdir / "sections.json").write_text(json.dumps(pairs, indent=2), encoding="utf-8")

    # Final progress update
    if status_callback:
        status_callback("Extraction completed!")

    if progress_callback:
        progress_callback(1.0)

    print("Done.")
    print(
        f"Wrote {outdir/'document.json'}, {outdir/'document.md'}, {outdir/'sections.json'}"
    )

    (outdir / "usage.txt").write_text(
        json.dumps(total_token_usage, indent=2), encoding="utf-8"
    )
    print("Wrote usage statistics to usage.txt")

    return total_token_usage

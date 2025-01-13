import pymupdf
from collections import defaultdict
from difflib import SequenceMatcher


def extract_filtered_content(
    pdf_path, similarity_threshold=0.85, min_occurrence_percent=80
):
    doc = pymupdf.open(pdf_path)
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
                        line.strip() for line in content.splitlines() if line.strip()
                    )
                )

    # Print summary
    print("\nSummary:")
    print(f"Total pages analyzed: {total_pages}")
    print(f"Frequent patterns found: {len(frequent_patterns)}")

    doc.close()

    return "\n".join(filtered_content)


result = extract_filtered_content(
    "./data_sources/Auto Loan Terms & Conditions - BM.pdf"
)
with open("./test.txt", "w") as file:
    file.write(result)

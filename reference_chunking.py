from typing import List, Dict, Tuple
from dataclasses import dataclass
import asyncio
import numpy as np
from openai import AsyncOpenAI
from sklearn.metrics.pairwise import cosine_similarity
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
import os
from helpers.document_processor import DocumentProcessor

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@dataclass
class ChunkPair:
    english_chunk: str
    malay_chunk: str
    chunk_index: int
    similarity_score: float
    metadata: Dict


class ProgressiveChunker:
    def __init__(
        self,
        api_key: str,
        max_chunk_size: int = 1000,
        batch_size: int = 5,
        similarity_threshold: float = 0.75,
        window_size_factor: float = 1.5,
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.max_chunk_size = max_chunk_size
        self.batch_size = batch_size
        self.similarity_threshold = similarity_threshold
        self.window_size_factor = window_size_factor
        self.model = "text-embedding-3-large"

    def chunk_reference_document(self, text: str) -> List[Tuple[str, int, int]]:
        """Split reference document (English) into chunks."""
        chunks = []
        current_pos = 0
        sentence_end = r"[.!?][\s\n]+"

        while current_pos < len(text):
            target_pos = min(current_pos + self.max_chunk_size, len(text))

            if target_pos == len(text):
                chunk = text[current_pos:].strip()
                if chunk:
                    chunks.append((chunk, current_pos, len(text)))
                break

            text_window = text[current_pos : target_pos + 50]
            matches = list(re.finditer(sentence_end, text_window))

            if matches:
                last_match = matches[-1]
                end_pos = current_pos + last_match.start() + 1
            else:
                end_pos = target_pos
                while end_pos > current_pos and not text[end_pos - 1].isspace():
                    end_pos -= 1

            chunk = text[current_pos:end_pos].strip()
            if chunk:
                chunks.append((chunk, current_pos, end_pos))

            current_pos = end_pos

        return chunks

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for texts."""
        try:
            response = await self.client.embeddings.create(
                model=self.model, input=texts, encoding_format="float"
            )
            return np.array([e.embedding for e in response.data])
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            raise

    def find_chunk_boundaries(self, text: str, chunk: str) -> Tuple[int, int]:
        """Find the exact start and end positions of a chunk in text."""
        chunk_clean = chunk.strip()
        start = text.find(chunk_clean)
        if start == -1:
            return -1, -1
        return start, start + len(chunk_clean)

    def remove_chunk_from_text(self, text: str, start: int, end: int) -> str:
        """Remove a chunk from text and clean up whitespace."""
        if start == -1 or end == -1:
            return text

        # Remove the chunk
        new_text = text[:start] + text[end:]

        # Clean up extra whitespace and newlines
        new_text = re.sub(r"\s+", " ", new_text)
        new_text = re.sub(r"\n\s*\n\s*\n", "\n\n", new_text)

        return new_text.strip()

    def create_search_windows(
        self, text: str, chunk_size: int, window_size_factor: float = 1.5
    ) -> List[Tuple[str, int, int]]:
        """Create overlapping windows for searching."""
        windows = []
        window_size = int(chunk_size * window_size_factor)

        # Create overlapping windows
        current_pos = 0
        while current_pos < len(text):
            window_end = min(current_pos + window_size, len(text))
            window = text[current_pos:window_end].strip()

            if window:
                windows.append((window, current_pos, window_end))

            # Overlap by 50%
            current_pos += window_size // 2

            if current_pos >= len(text):
                break

        return windows

    async def find_best_match(
        self,
        english_chunk: str,
        malay_text: str,
    ) -> Tuple[str, float, int, int]:
        """Find best matching chunk in remaining Malay text."""
        if not malay_text.strip():
            return "", 0.0, -1, -1

        # Create search windows
        windows = self.create_search_windows(
            malay_text, len(english_chunk), self.window_size_factor
        )

        if not windows:
            return "", 0.0, -1, -1

        # Get embeddings
        all_texts = [english_chunk] + [w[0] for w in windows]
        embeddings = await self.get_embeddings(all_texts)

        # Calculate similarities
        english_embedding = embeddings[0]
        window_embeddings = embeddings[1:]
        similarities = cosine_similarity([english_embedding], window_embeddings)[0]

        # Find best match
        best_idx = np.argmax(similarities)
        best_similarity = similarities[best_idx]

        if best_similarity < self.similarity_threshold:
            return "", best_similarity, -1, -1

        best_window = windows[best_idx]

        # Find exact boundaries of the matched text
        start, end = self.find_chunk_boundaries(malay_text, best_window[0])
        return best_window[0], best_similarity, start, end

    async def align_documents(
        self, english_doc: str, malay_doc: str
    ) -> List[ChunkPair]:
        """Align documents progressively, removing matched chunks."""
        # First chunk the English document
        english_chunks = self.chunk_reference_document(english_doc)

        aligned_pairs = []
        remaining_malay_text = malay_doc

        # Process chunks in batches
        for i in range(0, len(english_chunks), self.batch_size):
            batch = english_chunks[i : i + self.batch_size]

            print(f"Processing batch {i//self.batch_size + 1}")
            print(f"Remaining Malay text length: {len(remaining_malay_text)}")

            for chunk_idx, (eng_chunk, eng_start, eng_end) in enumerate(batch):
                # Find best match in remaining Malay text
                malay_chunk, similarity, start, end = await self.find_best_match(
                    eng_chunk, remaining_malay_text
                )

                if malay_chunk and similarity >= self.similarity_threshold:
                    pair = ChunkPair(
                        english_chunk=eng_chunk,
                        malay_chunk=malay_chunk,
                        chunk_index=i + chunk_idx,
                        similarity_score=similarity,
                        metadata={
                            "english_length": len(eng_chunk),
                            "malay_length": len(malay_chunk),
                            "english_position": (eng_start, eng_end),
                            "malay_position": (start, end),
                            "content_ratio": len(malay_chunk) / len(eng_chunk),
                        },
                    )
                    aligned_pairs.append(pair)

                    # Remove the matched chunk from remaining Malay text
                    remaining_malay_text = self.remove_chunk_from_text(
                        remaining_malay_text, start, end
                    )

            # Add delay between batches
            if i + self.batch_size < len(english_chunks):
                await asyncio.sleep(1)

        return aligned_pairs


# Example usage
async def main():
    document_processor = DocumentProcessor()
    doc1 = document_processor.extract_text(
        "./data_sources/hlb-pay-and-save-i-tnc-en.pdf"
    )
    doc2 = document_processor.extract_text(
        "./data_sources/hlb-pay-and-save-i-tnc-bm.pdf"
    )
    with open("./test_doc1.txt", "w") as file:
        file.write(doc1)

    with open("./test_doc2.txt", "w") as file:
        file.write(doc2)
    english_doc = doc1

    malay_doc = doc2

    chunker = ProgressiveChunker(
        api_key=OPENAI_API_KEY,
        max_chunk_size=500,
        batch_size=5,
        similarity_threshold=0.9,
    )

    pairs = await chunker.align_documents(english_doc, malay_doc)

    for pair in pairs:
        print(f"\nChunk {pair.chunk_index}")
        print(f"English: {pair.english_chunk}")
        print(f"Malay: {pair.malay_chunk}")
        print(f"Similarity: {pair.similarity_score:.3f}")
        print(f"Length Ratio: {pair.metadata['content_ratio']:.2f}")

        with open("./test_logs/progressive_chunking_similarity_9.txt", "a") as file:
            file.write(
                f"Pair {pair.chunk_index}\n\nEnglish: {pair.english_chunk}\n\nMalay: {pair.malay_chunk}\n\nSimilarity: {pair.similarity_score:.3f}\n########################\n"
            )


if __name__ == "__main__":
    asyncio.run(main())

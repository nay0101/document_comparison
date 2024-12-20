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
    english_text: str
    malay_text: str
    pair_index: int
    similarity_score: float
    english_length: int
    malay_length: int
    metadata: Dict


class SizeBasedChunker:
    def __init__(
        self,
        api_key: str,
        max_chunk_size: int = 1000,
        batch_size: int = 5,
        similarity_threshold: float = 0.75,
        overlap_size: int = 100,
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.max_chunk_size = max_chunk_size
        self.batch_size = batch_size
        self.similarity_threshold = similarity_threshold
        self.overlap_size = overlap_size
        self.model = "text-embedding-3-large"

    def create_chunks(self, text: str, is_english: bool = True) -> List[str]:
        """Split text into chunks of approximately max_chunk_size characters."""
        # Common sentence endings
        endings = r"[.!?]+"

        # Find all sentence endings with their positions
        matches = list(re.finditer(endings, text))
        sentence_ends = [m.end() for m in matches]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Find the best split point near max_chunk_size
            target_pos = current_pos + self.max_chunk_size

            if target_pos >= len(text):
                # Add the remaining text as the last chunk
                chunk = text[current_pos:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Find the closest sentence ending before target_pos
            split_pos = max(
                (end for end in sentence_ends if end <= target_pos),
                default=current_pos + self.max_chunk_size,
            )

            # Extract chunk
            chunk = text[current_pos:split_pos].strip()
            if chunk:
                chunks.append(chunk)

            # Move position for next chunk, including overlap
            current_pos = max(current_pos + 1, split_pos - self.overlap_size)

        return chunks

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a batch of texts."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float",
                dimensions=3072,
            )
            return np.array([e.embedding for e in response.data])
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            raise

    async def process_batch(
        self, english_chunks: List[str], malay_chunks: List[str], batch_start_index: int
    ) -> List[ChunkPair]:
        """Process a batch of chunks using embeddings."""
        # Get embeddings
        english_embeddings = await self.get_embeddings(english_chunks)
        malay_embeddings = await self.get_embeddings(malay_chunks)
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(english_embeddings, malay_embeddings)

        # Match chunks based on similarity
        pairs = []
        used_malay_indices = set()

        for i, english_text in enumerate(english_chunks):
            best_similarity = -1
            best_malay_idx = None

            # Find best matching Malay chunk
            for j, malay_text in enumerate(malay_chunks):
                if j not in used_malay_indices:
                    similarity = similarity_matrix[i, j]
                    if (
                        similarity > best_similarity
                        and similarity >= self.similarity_threshold
                    ):
                        best_similarity = similarity
                        best_malay_idx = j

            if best_malay_idx is not None:
                pair = ChunkPair(
                    english_text=english_text,
                    malay_text=malay_chunks[best_malay_idx],
                    pair_index=batch_start_index + len(pairs),
                    similarity_score=float(best_similarity),
                    english_length=len(english_text),
                    malay_length=len(malay_chunks[best_malay_idx]),
                    metadata={
                        "english_embedding_norm": float(
                            np.linalg.norm(english_embeddings[i])
                        ),
                        "malay_embedding_norm": float(
                            np.linalg.norm(malay_embeddings[best_malay_idx])
                        ),
                        "length_ratio": len(malay_chunks[best_malay_idx])
                        / len(english_text),
                    },
                )
                pairs.append(pair)
                used_malay_indices.add(best_malay_idx)

        return pairs

    async def align_documents(
        self, english_doc: str, malay_doc: str, min_chunk_length: int = 50
    ) -> List[ChunkPair]:
        """Align documents by processing size-based chunks in batches."""
        # Create chunks for both documents
        english_chunks = self.create_chunks(english_doc, is_english=True)
        malay_chunks = self.create_chunks(malay_doc, is_english=False)

        # Filter out very short chunks
        english_chunks = [c for c in english_chunks if len(c) >= min_chunk_length]
        malay_chunks = [c for c in malay_chunks if len(c) >= min_chunk_length]

        all_pairs = []

        # Process in batches
        for i in range(0, len(english_chunks), self.batch_size):
            batch_english = english_chunks[i : i + self.batch_size]

            # Consider a window of Malay chunks for better matching
            start_idx = max(0, i - 1)
            end_idx = min(len(malay_chunks), i + self.batch_size + 1)
            batch_malay = malay_chunks[start_idx:end_idx]

            print(f"Processing batch {i//self.batch_size + 1}")

            batch_pairs = await self.process_batch(
                batch_english, batch_malay, len(all_pairs)
            )

            all_pairs.extend(batch_pairs)

            if i + self.batch_size < len(english_chunks):
                await asyncio.sleep(1)

        return sorted(all_pairs, key=lambda x: x.pair_index)


# Example usage
async def main():
    # Example documents
    document_processor = DocumentProcessor()
    doc1 = document_processor.extract_text(
        "./data_sources/hlb-pay-and-save-i-tnc-en.pdf"
    )
    doc2 = document_processor.extract_text(
        "./data_sources/hlb-pay-and-save-i-tnc-bm.pdf"
    )
    english_doc = doc1

    malay_doc = doc2

    chunker = SizeBasedChunker(
        api_key=OPENAI_API_KEY,
        max_chunk_size=1000,
        batch_size=5,
        similarity_threshold=0.8,
        overlap_size=100,
    )

    pairs = await chunker.align_documents(english_doc, malay_doc)
    # Print results
    for pair in pairs:
        print(f"\nPair {pair.pair_index}")
        print(f"English ({pair.english_length} chars): {pair.english_text}")
        print(f"Malay ({pair.malay_length} chars): {pair.malay_text}")
        print(f"Similarity: {pair.similarity_score:.3f}")
        print(f"Length ratio: {pair.metadata['length_ratio']:.2f}")

        with open("./test5.txt", "a") as file:
            file.write(
                f'Pair {pair.pair_index}\n\nEnglish ({pair.english_length} chars): {pair.english_text}\n\nMalay ({pair.malay_length} chars): {pair.malay_text}\n\nSimilarity: {pair.similarity_score:.3f}\n\nLength ratio: {pair.metadata["length_ratio"]:.2f}\n########################\n'
            )


if __name__ == "__main__":
    asyncio.run(main())

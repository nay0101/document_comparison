from batch_chunking import SentenceBatchProcessor
import asyncio


async def main():
    # Example documents
    source_doc = """
    Climate change is a global challenge. It affects every country and every person.
    We need immediate action to address this crisis. The future of our planet depends on it.
    Scientists have been warning us for decades. We can no longer ignore their findings.
    """

    target_doc = """
    El cambio climático es un desafío global. Afecta a todos los países y a todas las personas.
    Necesitamos acción inmediata para abordar esta crisis. El futuro de nuestro planeta depende de ello.
    Los científicos nos han estado advirtiendo durante décadas. Ya no podemos ignorar sus hallazgos.
    """

    processor = SentenceBatchProcessor(
        api_key="your_api_key", source_lang="en", target_lang="es", batch_size=10
    )

    aligned_pairs = await processor.align_documents(source_doc, target_doc)

    # Print results
    for pair in aligned_pairs:
        print("\nAlignment:")
        print(f"Source [{pair.source_index}]: {pair.source_sentence}")
        print(f"Target [{pair.target_index}]: {pair.target_sentence}")
        print(f"Confidence: {pair.confidence}")
        print(f"Notes: {pair.metadata['notes']}")


if __name__ == "__main__":
    asyncio.run(main())

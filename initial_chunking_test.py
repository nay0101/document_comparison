from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langfuse.callback import CallbackHandler
from helpers.document_processor import DocumentProcessor

document_processor = DocumentProcessor()


def chunk_docs(doc1, doc2):
    instruction = """
        You will be chunking two documents in different languages to have the same content in each chunk. Follow these instructions carefully:

        1. You will be provided with two documents in different languages. Here they are:

        <document1>
        {doc1}
        </document1>

        <document2>
        {doc2}
        </document2>

        2. You will chunk these documents into a maximum of 5000 parts each.

        3. Your task is to divide each document into chunks so that the content of each chunk in one language corresponds to the content of the same-numbered chunk in the other language.

        4. To align the content between languages:
          a. First, analyze both documents to understand their overall structure and content.
          b. Identify natural break points in both documents (e.g., paragraph breaks, section headings, or sentence boundaries) that occur at roughly the same points in the content.
          c. Try to make each chunk convey a complete thought or section, rather than breaking mid-sentence or mid-paragraph if possible.
          d. Ensure that the chunks in both languages cover approximately the same amount of content, even if the exact word count may differ due to language differences.

        5. Output your chunked and aligned content in the following format:

        <chunked_documents>
        <chunk number="1">
        <language1>
        [Page number of the content]
        [Content of first chunk in Language 1]
        </language1>
        <language2>
        [Page number of the content]
        [Content of first chunk in Language 2]
        </language2>
        </chunk>

        <chunk number="2">
        <language1>
        [Page number of the content]
        [Content of second chunk in Language 1]
        </language1>
        <language2>
        [Page number of the content]
        [Content of second chunk in Language 2]
        </language2>
        </chunk>

        [... continue for all chunks ...]
        </chunked_documents>

        6. If you encounter any issues:
          a. If the documents seem to have significantly mismatched content or lengths, make a note of this before the chunked output.
          b. If it's impossible to create the exact number of chunks specified while maintaining content alignment, create the closest number of chunks possible and explain the discrepancy.

        7. Do not summarize. The chunks should still include all the original content.

        8. The process should continue until all the content are chunked.

        Remember, the goal is to have each chunk contain roughly equivalent content across both languages, allowing for natural language differences in expression and length.
      """

    prompt = ChatPromptTemplate.from_messages(
        [("system", instruction), ("human", "Start Chunking.")]
    )

    model = ChatOpenAI(model="gpt-4o")

    chain = prompt | model | StrOutputParser()

    return chain.invoke(
        {"doc1": doc1, "doc2": doc2}, config={"callbacks": [CallbackHandler()]}
    )

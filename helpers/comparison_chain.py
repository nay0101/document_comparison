from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from io import BytesIO
from typing import Union, Optional, List, Dict
from langfuse.callback import CallbackHandler
from .types import Model
from .llm_integrations import get_llm
from .document_processor import DocumentProcessor
import xmltodict
import json
from operator import itemgetter

load_dotenv()


class ComparisonChain:
    def __init__(
        self,
        chat_model_name: Model = "gpt-4o-mini",
    ):
        self.chat_model = get_llm(model=chat_model_name)
        self.document_processor = DocumentProcessor()

    def _process_document(self, doc_file_bytes: Union[bytes, BytesIO]) -> str:
        return self.document_processor.extract_text_with_page_number(
            pdf_bytes=BytesIO(doc_file_bytes)
        )

    def _load_xml_file(self, xml_file_path: str) -> List[str]:
        xml_string = ""
        with open(f"./{xml_file_path}", "r") as file:
            xml_string = file.read()

        xml_string = self.document_processor.clean_xml(xml_string)
        data = xmltodict.parse(xml_string)
        chunks = data["chunked_documents"]["chunk"]

        chunk_list = []

        for chunk in chunks:
            content1 = chunk["language1"].strip()
            content2 = chunk["language2"].strip()
            chunk_list.append({"doc1": content1, "doc2": content2})

        return chunk_list

    def _chunk_documents(
        self,
        doc1: str,
        doc2: str,
        xml_file_path: Optional[str] = None,
        use_existing_file: bool = False,
    ) -> List[str]:
        if not use_existing_file:
            print("Chunking...")
            instruction = """
              You are a skilled document analyst specializing in multilingual content alignment. Your task is to chunk two documents in different languages while maintaining content alignment between chunks. Here are the documents and relevant information:

              <document1>
              {doc1}
              </document1>

              <document2>
              {doc2}
              </document2>

              ## END OF DOCUMENTS ##

              Maximum number of words per chunks to create: <num_words>10000</num_words>

              Follow these steps to complete the task:

              1. Analyze both documents to understand their overall structure and content.
              2. Identify natural break points in both documents (e.g., paragraph breaks, section headings, or sentence boundaries) that occur at roughly the same points in the content.
              3. Divide each document into the specified number of chunks, ensuring that:
                a. Each chunk conveys a complete thought or section when possible.
                b. Chunks in both languages cover approximately the same amount of content, even if the exact word count differs due to language differences.
                c. If content is present in one language but not in the other, include the present content in the appropriate chunk without creating a corresponding paragraph in the other language and don't remove the present content.
              4. Align the chunks between the two languages.
              5. Before giving output, analyze and ensure that all pages and content from both documents are fully processed and included in the chunks before finalizing your output.
              6. Output the chunked and aligned content using the specified format.

              Output your chunked and aligned content in the following format:

              <chunked_documents>
                <chunk number="1">
                  <language1>
                    [Content of first chunk in Language 1]
                  </language1>
                  <language2>
                    [Content of first chunk in Language 2]
                  </language2>
                </chunk>

              <chunk number="2">
                <language1>
                  [Content of second chunk in Language 1]
                </language1>
                <language2>
                  [Content of second chunk in Language 2]
                </language2>
              </chunk>

              [... generate until all the content are covered ...]
              </chunked_documents>

              Important notes:
              - Do not add language identifiers like ```xml in the output.
              - Just output the xml format. Do not output any other text.
              - Do not summarize the content.
              - If it's impossible to create the exact number of chunks specified while maintaining content alignment, create the closest number of chunks possible and explain the discrepancy.
            """

            # instruction = """
            #   You are a skilled document analyst specializing in multilingual content alignment. Your task is to chunk two documents in different languages while maintaining content alignment between chunks. Here are the documents and relevant information:

            #   <document1>
            #   {doc1}
            #   </document1>

            #   <document2>
            #   {doc2}
            #   </document2>

            #   Maximum number of words per chunks to create: <num_words>500</num_words>

            #   Follow these steps to complete the task:

            #   1. Analyze both documents to understand their overall structure and content.
            #   2. Identify natural break points in both documents (e.g., paragraph breaks, section headings, or sentence boundaries) that occur at roughly the same points in the content.
            #   3. Divide each document into the specified number of chunks, ensuring that:
            #     a. Each chunk conveys a complete thought or section when possible.
            #     b. Chunks in both languages cover approximately the same amount of content, even if the exact word count differs due to language differences.
            #     c. If content is present in one language but not in the other, include the present content in the appropriate chunk without creating a corresponding paragraph in the other language and don't remove the present content.
            #   4. Align the chunks between the two languages.
            #   5. Before giving output, analyze and ensure that all pages and content from both documents are fully processed and included in the chunks before finalizing your output.
            #   6. Output the chunked and aligned content using the specified format.

            #   Output your chunked and aligned content in the following format:

            #   <chunked_documents>
            #     <chunk number="1">
            #       <language1>
            #         [Page: Page Number of the content] (if applicable)
            #         [Content of first chunk in Language 1]
            #       </language1>
            #       <language2>
            #         [Page: Page Number of the content] (if applicable)
            #         [Content of first chunk in Language 2]
            #       </language2>
            #     </chunk>

            #   <chunk number="2">
            #     <language1>
            #       [Page: Page Number of the content] (if applicable)
            #       [Content of second chunk in Language 1]
            #     </language1>
            #     <language2>
            #       [Page: Page Number of the content] (if applicable)
            #       [Content of second chunk in Language 2]
            #     </language2>
            #   </chunk>

            #   [... generate until all the content are covered ...]
            #   </chunked_documents>

            #   Important notes:
            #   - Do not add language identifiers like ```xml in the output.
            #   - Just output the xml format. Do not output any other text.
            #   - Do not summarize the content.
            #   - If it's impossible to create the exact number of chunks specified while maintaining content alignment, create the closest number of chunks possible and explain the discrepancy.
            # """

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", instruction),
                    (
                        "human",
                        "Start chunking.",
                    ),
                ]
            )

            model = self.chat_model

            def create_recursive_chain(model, system_instruction, doc1, doc2):
                def check_token_limit(
                    _input: Dict, accumulated_responses: str = "", iteration: int = 0
                ):
                    iteration += 1
                    response_content = _input["llm_result"].content
                    response_metadata = _input["llm_result"].response_metadata
                    stop_reason_keys = ["finish_reason", "stop_reason"]
                    stop_reason_flags = ["length", "max_tokens"]
                    stop_reason = next(
                        map(response_metadata.get, stop_reason_keys), None
                    )

                    last_chunk = self.document_processor.get_last_chunk(
                        response_content
                    )
                    response_content = self.document_processor.get_complete_chunks(
                        response_content
                    )
                    accumulated_responses += f"{response_content}\n"

                    if stop_reason not in stop_reason_flags:
                        return accumulated_responses

                    new_prompt = ChatPromptTemplate.from_messages(
                        [
                            ("system", system_instruction),
                            (
                                "human",
                                "Start chunking.",
                            ),
                            (
                                "ai",
                                f"...\n{last_chunk}",
                            ),
                            (
                                "human",
                                "Continue EXACTLY from this last chunk shown above. Do not restart from the beginning. Generate the next chunks following the same format and numbering sequence. Don't stop halfway. Generate as long as possible.",
                            ),
                        ]
                    )

                    recursive_chain = RunnablePassthrough.assign(
                        prompt=new_prompt
                    ).assign(llm_result=itemgetter("prompt") | model)

                    chunks = recursive_chain.stream({"doc1": doc1, "doc2": doc2})
                    result = ""
                    with open(f"./chunks/iteration_{iteration}.txt", "w") as file:
                        file.write("")
                    for chunk in chunks:
                        result += chunk
                        if "llm_result" in chunk:
                            with open(
                                f"./chunks/iteration_{iteration}.txt", "a"
                            ) as file:
                                file.write(chunk["llm_result"].content)

                    return check_token_limit(result, accumulated_responses, iteration)

                return check_token_limit

            chunking_chain = RunnablePassthrough.assign(
                prompt={"doc1": itemgetter("doc1"), "doc2": itemgetter("doc2")} | prompt
            ).assign(llm_result=itemgetter("prompt") | model)

            recursive_chain = create_recursive_chain(
                model=model, system_instruction=instruction, doc1=doc1, doc2=doc2
            )

            result_chunks = chunking_chain.stream({"doc1": doc1, "doc2": doc2})

            result = ""
            with open(f"./chunks/iteration_0.txt", "w") as file:
                file.write("")
            for chunk in result_chunks:
                result += chunk
                if "llm_result" in chunk:
                    with open(f"./chunks/iteration_0.txt", "a") as file:
                        file.write(chunk["llm_result"].content)

            final_result = recursive_chain(result)
            final_result = self.document_processor.clean_chunk_response(final_result)

            with open(f"./{xml_file_path}", "w") as file:
                file.write(final_result)

        chunks = self._load_xml_file(f"./{xml_file_path}")

        return chunks

    def chunk_documents(self, _input: Dict) -> List[str]:
        return self._chunk_documents(
            doc1=_input["doc1"],
            doc2=_input["doc2"],
            xml_file_path=_input["xml_file_path"],
            use_existing_file=_input["use_existing_file"],
        )

    def _processor_chain(self) -> Runnable:
        """Compares two documents"""

        # system_prompt = """
        #   You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

        #   Here are the two documents you need to compare:

        #   Document 1 (considered the main reference):
        #   <document1>
        #   {doc1}
        #   </document1>

        #   Document 2:
        #   <document2>
        #   {doc2}
        #   </document2>

        #   Please follow these steps to complete your analysis:

        #   1. Carefully read and compare both documents in their entirety.

        #   2. Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content. Ignore minor variations in wording or slight differences that don't impact the overall message.

        #   3. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
        #     - Inaccurate disclosure: Information that is incorrectly stated or translated
        #     - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
        #     - Outdated information: Data or statements that are no longer relevant or accurate
        #     - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
        #     - Major deviations from the English version: Any substantial differences from Document 1

        #   4. For each flag, include:
        #     - A list of applicable difference types (from the list above)
        #     - A brief description of the flag
        #     - The relevant content from both documents, including the page number
        #     - An explanation of the difference, highlighting the main issues

        #   5. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.

        #   6. If multiple discrepancies are found in one paragraph or sentence, combine them into a single flag and list all applicable flag types.

        #   7. If you don't find any major discrepancies, state that no significant differences were found.

        #   After your comparison, format your response as a JSON object with the following structure:

        #   {{
        #     "flags": [
        #       {{
        #         "types": ["List of applicable difference types"],
        #         "description": "Brief description of the flag",
        #         "doc1": {{
        #           "page": "Page number in Document 1 (just the number)",
        #           "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
        #         }},
        #         "doc2": {{
        #           "page": "Page number in Document 2 (just the number)",
        #           "content": "Relevant content from Document 2 with <span style=\"color: red\">highlighted difference</span>"
        #         }},
        #         "explanation": "Detailed explanation of the difference"
        #       }}
        #     ]
        #   }}

        #   If no major discrepancies are found, your JSON response should be:

        #   {{
        #     "flags": []
        #   }}

        #   Remember to use proper JSON formatting, including quotes around keys and string values, and commas to separate objects and key-value pairs. Don't need to include any language identifiers like ```json in the output.
        # """

        system_prompt = """
          You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

          Here are the two documents you need to compare:

          Document 1 (considered the main reference):
          <document1>
          {doc1}
          </document1>

          Document 2:
          <document2>
          {doc2}
          </document2>

          Please follow these steps to complete your analysis:

          1. Carefully read and compare both documents in their entirety.

          2. Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content. Ignore minor variations in wording or slight differences that don't impact the overall message.

          3. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
            - Inaccurate disclosure: Information that is incorrectly stated or translated
            - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
            - Outdated information: Data or statements that are no longer relevant or accurate
            - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
            - Major deviations from the English version: Any substantial differences from Document 1

          4. For each flag, include:
            - A list of applicable difference types (from the list above)
            - A brief description of the flag
            - The relevant content from both documents, including the page number
            - An explanation of the difference, highlighting the main issues

          5. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.

          6. If you don't find any major discrepancies, state that no significant differences were found.

          After your comparison, format your response as a JSON object with the following structure:

          {{
            "flags": [
              {{
                "types": ["List of applicable difference types"],
                "description": "Brief description of the flag",
                "doc1": {{
                  "page": "Page number in Document 1 (just the number)",
                  "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
                }},
                "doc2": {{
                  "page": "Page number in Document 2 (just the number)",
                  "content": "Relevant content from Document 2 with <span style=\"color: red\">highlighted difference</span>"
                }},
                "explanation": "Detailed explanation of the difference"
              }}
            ]
          }}

          If no major discrepancies are found, your JSON response should be:

          {{
            "flags": []
          }}

          Remember to use proper JSON formatting, including quotes around keys and string values, and commas to separate objects and key-value pairs. Don't need to include any language identifiers like ```json in the output.
        """

        user_prompt = """Begin your analysis now."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", user_prompt)]
        )

        def loop_invoke(chunks: List[Dict]) -> List[Dict]:
            flags = []
            loop_chain = prompt | self.chat_model | StrOutputParser()

            for index, chunk in enumerate(chunks):
                print(f"Comparing Chunk: {index + 1}")
                response = loop_chain.invoke(
                    {"doc1": chunk["doc1"], "doc2": chunk["doc2"]}
                )
                response = self.document_processor.clean_compare_response(response)
                flags.append(json.loads(response)["flags"])

            return {"flags": sum(flags, [])}

        processor_chain = RunnableLambda(self.chunk_documents) | (
            lambda x: loop_invoke(x)
        )

        return processor_chain

    def invoke_chain(
        self,
        doc1_file_bytes: Union[BytesIO, bytes],
        doc2_file_bytes: Union[BytesIO, bytes],
        xml_file_path: str,
        use_existing_file: bool = False,
        chat_id: str = None,
    ) -> Dict:
        doc1 = self._process_document(doc1_file_bytes)
        doc2 = self._process_document(doc2_file_bytes)
        final_chain = self._processor_chain()
        result = final_chain.invoke(
            {
                "doc1": doc1,
                "doc2": doc2,
                "xml_file_path": xml_file_path,
                "use_existing_file": use_existing_file,
            },
            config={"callbacks": [CallbackHandler(user_id=str(chat_id))]},
        )

        return result

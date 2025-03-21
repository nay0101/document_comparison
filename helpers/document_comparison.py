from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from io import BytesIO
from typing import Union, Optional, List, Dict
from langfuse.callback import CallbackHandler
from .types import Model, Mismatches
from .llm_integrations import get_llm
from .document_processor import DocumentProcessor
import xmltodict
import json
from operator import itemgetter
from helpers.llm_mappings import LLM_MAPPING
from helpers.suggestions import SuggestionChain
import streamlit as st
import os

environment = os.getenv("ENVIRONMENT")


class DocumentComparisonChain:
    def __init__(self, chat_model_name: Model = "gpt-4o", temperature: float = 0.0):
        self.chat_model_name = chat_model_name
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()
        self.suggestion_chain = SuggestionChain(
            chat_model_name=chat_model_name, temperature=temperature
        )

    def _load_xml_content(
        self,
        doc1: List[Dict],
        doc2: List[Dict],
        xml_file_path: Optional[str] = None,
        xml_string: Optional[str] = None,
    ) -> List[str]:
        if xml_string is None:
            with open(f"./{xml_file_path}", "r") as file:
                xml_string = file.read()

        clean_xml_string = self.document_processor.clean_xml_format(xml_string)

        data = xmltodict.parse(clean_xml_string)
        chunks = data["chunked_documents"]["chunk"]

        chunk_list = []
        with open("./content_list_doc1.json", "w") as file:
            file.write(json.dumps(doc1, indent=2))

        with open("./content_list_doc2.json", "w") as file:
            file.write(json.dumps(doc2, indent=2))

        if isinstance(chunks, list):
            for chunk in chunks:
                content1 = (
                    chunk["language1"].strip() if chunk["language1"] is not None else ""
                )
                content1_page = self.document_processor.find_page_by_paragraph(
                    content_list=doc1, search_paragraph=content1
                )

                content2 = (
                    chunk["language2"].strip() if chunk["language2"] is not None else ""
                )
                content2_page = self.document_processor.find_page_by_paragraph(
                    content_list=doc2, search_paragraph=content2
                )

                chunk_list.append(
                    {
                        "doc1": {"content": content1, "page": content1_page},
                        "doc2": {"content": content2, "page": content2_page},
                    }
                )
        else:
            content1 = chunks["language1"].strip()
            content1_page = self.document_processor.find_page_by_paragraph(
                content_list=doc1, search_paragraph=content1
            )

            content2 = chunks["language2"].strip()
            content2_page = self.document_processor.find_page_by_paragraph(
                content_list=doc2, search_paragraph=content2
            )

            chunk_list.append(
                {
                    "doc1": {"content": content1, "page": content1_page},
                    "doc2": {"content": content2, "page": content2_page},
                }
            )

        return chunk_list

    def _chunk_documents(
        self,
        doc1: List[Dict],
        doc2: List[Dict],
        xml_file_path: Optional[str] = None,
        use_existing_file: bool = False,
    ) -> List[Dict]:
        doc1_content = "\n".join(item["content"] for item in doc1)
        doc2_content = "\n".join(item["content"] for item in doc2)
        if not use_existing_file:
            instruction = """
              You are a skilled document analyst specializing in multilingual content alignment. Your task is to chunk two documents in different languages while maintaining content alignment between chunks. Here are the documents and relevant information:

              <document1>
              {doc1_content}
              </document1>

              <document2>
              {doc2_content}
              </document2>

              ## END OF DOCUMENTS ##

              Maximum number of words per chunks to create: <num_words>1000</num_words>

              Follow these steps to complete the task:

              1. Analyze both documents to understand their overall structure and content.
              2. Identify natural break points in both documents (e.g., paragraph breaks, section headings, or sentence boundaries) that occur at roughly the same points in the content.
              3. Divide each document into chunks, ensuring that:
                a. Each chunk conveys a complete thought or section when possible.
                b. Chunks in both languages cover approximately the same amount of content, even if the exact word count differs due to language differences.
                c. If content is present in one language but not in the other, include the present content in the appropriate chunk without creating a corresponding content in the other language and don't remove the present content.
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
              - Make sure that all the content of original documents are included in the output chunks.
              - If it's impossible to create the exact number of chunks specified while maintaining content alignment, create the closest number of chunks possible.
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

            def create_recursive_chain(
                model, system_instruction, doc1_content, doc2_content
            ):
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
                    accumulated_responses += f"{self.document_processor.remove_code_fences(response_content)}\n"

                    if stop_reason.lower() not in stop_reason_flags:
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
                                "Continue EXACTLY from this last chunk shown above. Do not restart from the beginning. Generate the next chunks following the same format and numbering sequence. Don't stop halfway. Generate until you reach the END OF DOCUMENTS.",
                            ),
                        ]
                    )

                    recursive_chain = RunnablePassthrough.assign(
                        prompt=new_prompt
                    ).assign(llm_result=itemgetter("prompt") | model)

                    chunks = recursive_chain.stream(
                        {"doc1_content": doc1_content, "doc2_content": doc2_content}
                    )
                    result = ""

                    if environment == "development":
                        with open(
                            f"./chunks/iteration_{iteration}.txt", "w", encoding="utf-8"
                        ) as file:
                            file.write("")

                    for chunk in chunks:
                        result += chunk
                        if environment == "development":
                            if "llm_result" in chunk:
                                with open(
                                    f"./chunks/iteration_{iteration}.txt",
                                    "a",
                                    encoding="utf-8",
                                ) as file:
                                    file.write(chunk["llm_result"].content)

                    return check_token_limit(result, accumulated_responses, iteration)

                return check_token_limit

            chunking_chain = RunnablePassthrough.assign(
                prompt={
                    "doc1_content": itemgetter("doc1_content"),
                    "doc2_content": itemgetter("doc2_content"),
                }
                | prompt
            ).assign(llm_result=itemgetter("prompt") | model)

            recursive_chain = create_recursive_chain(
                model=model,
                system_instruction=instruction,
                doc1_content=doc1_content,
                doc2_content=doc2_content,
            )

            result_chunks = chunking_chain.stream(
                {"doc1_content": doc1_content, "doc2_content": doc2_content}
            )

            result = ""
            if environment == "development":
                with open(f"./chunks/iteration_0.txt", "w", encoding="utf-8") as file:
                    file.write("")
            for chunk in result_chunks:
                result += chunk
                if environment == "development":
                    if "llm_result" in chunk:
                        with open(
                            f"./chunks/iteration_0.txt", "a", encoding="utf-8"
                        ) as file:
                            file.write(chunk["llm_result"].content)

            final_result = recursive_chain(result)
            final_result = self.document_processor.reformat_chunk_boundary(final_result)

            if environment == "development":
                with open(xml_file_path, "w", encoding="utf-8") as file:
                    file.write(final_result)
        else:
            with open(f"./{xml_file_path}", "r") as file:
                final_result = file.read()

        chunks = self._load_xml_content(
            doc1=doc1,
            doc2=doc2,
            xml_string=final_result,
        )

        return chunks

    def chunk_documents(self, _input: Dict) -> List[Dict]:
        with st.spinner("Processing Documents"):
            result = self._chunk_documents(
                doc1=_input["doc1"],
                doc2=_input["doc2"],
                xml_file_path=_input["xml_file_path"],
                use_existing_file=_input["use_existing_file"],
            )
        return result

    def _comparison_chain(self) -> Runnable:
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

        #   ## END OF DOCUMENTS ##

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
        #     - The relevant content from both documents, including the page number
        #     - An explanation of the difference, highlighting the main issues
        #   5. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.

        #   After your comparison, format your response as a JSON object with the following structure:

        #   {{
        #     "flags": [
        #       {{
        #         "types": ["List of applicable difference types"],
        #         "doc1": {{
        #           "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
        #         }},
        #         "doc2": {{
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

        # system_prompt = """
        # You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

        # Here are the two documents you need to compare:

        # <document1>
        # {doc1}
        # </document1>

        # ## END OF DOCUMENT 1 ##

        # <document2>
        # {doc2}
        # </document2>

        # ## END OF DOCUMENT 2 ##

        # Please follow these steps to complete your analysis:

        # 1. Carefully read and compare both documents until you reach the ## END OF DOCUMENT ## line by line, paragraph by paragraph.
        # 2. Ensure that every part of both documents is given equal attention, from the beginning to the end.
        # 3. Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content. Ignore minor variations in wording or slight differences that don't impact the overall message.
        # 4. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
        #   - Inaccurate disclosure: Information that is incorrectly stated or translated
        #   - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
        #   - Outdated information: Data or statements that are no longer relevant or accurate
        #   - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
        #   - Major deviations from the English version: Any substantial differences from Document 1
        # 5. For each flag, include:
        #   - A list of applicable difference types (from the list above)
        #   - The relevant content from both documents, including the page number
        #   - An explanation of the difference, highlighting the main issues
        # 6. You can flag same sentences or paragraphs more than once.
        # 7. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.

        # After your comparison, format your response as a JSON object with the following structure:

        # {{
        #   "flags": [
        #     {{
        #       "types": ["List of applicable difference types"],
        #       "doc1": {{
        #         "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
        #       }},
        #       "doc2": {{
        #         "content": "Relevant content from Document 2 with <span style=\"color: red\">highlighted difference</span>"
        #       }},
        #       "explanation": "Detailed explanation of the difference"
        #     }}
        #   ]
        # }}

        # If no major discrepancies are found, your JSON response should be:

        # {{
        #   "flags": []
        # }}

        # Remember to use proper JSON formatting, including quotes around keys and string values, and commas to separate objects and key-value pairs. Don't need to include any language identifiers like ```json in the output.
        #         """
        match LLM_MAPPING.get(self.chat_model_name, None):
            case "openai":
                system_prompt = """
              You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

              Here are the two documents you need to compare:

              <document1>
              {doc1}
              </document1>

              ## END OF DOCUMENT 1 ##

              <document2>
              {doc2}
              </document2>

              ## END OF DOCUMENT 2 ##

              Please follow these steps to complete your analysis:

              1. Carefully read and compare both documents until you reach the ## END OF DOCUMENT ## line by line, paragraph by paragraph.
              2. Ensure that every part of both documents is given equal attention, from the beginning to the end.
              3. Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content.
              4. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
                - Inaccurate disclosure: Information that is incorrectly stated or translated
                - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
                - Outdated information: Data or statements that are no longer relevant or accurate
                - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
                - Major deviations from the English version: Any substantial differences from Document 1
                - Structural Difference: The same content is labelled in different enumeration labels [like (a)(b)(c) or 1, 2, 3]
              5. For each flag, include:
                - A list of applicable difference types (from the list above)
                - The relevant content from both documents, including the page number
                - An explanation of the difference, highlighting the main issues
              6. You can flag same sentences or paragraphs more than once.
              7. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.
              8. If there is no major discrepancy, just reponse with an empty list. Don't explain that there is no discrepancy.

              After your comparison, format your response as a JSON object with the following structure:

              {{
                "flags": [
                  {{
                    "types": ["List of applicable difference types"],
                    "doc1": {{
                      "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
                    }},
                    "doc2": {{
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
            case "google":
                system_prompt = """
        ### Context ###
You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents and identify **only major discrepancies** that could significantly alter the meaning, interpretation, or usability of the content.

Here are the two documents you need to compare:

<Document1>
{doc1}
</Document1>

## END OF DOCUMENT 1 ##

<Document2>
{doc2}
</Document2>

## END OF DOCUMENT 2 ##

### Instructions for Analysis ###
Please follow these steps to complete your analysis:

1. Compare both documents carefully until the ## END OF DOCUMENT ## markers, line by line, paragraph by paragraph.
2. Identify only the major discrepancies between the documents. Focus on significant discrepancies that change the meaning, interpretation, or intent of the content. Avoid highlighting minor wording, phrasing variations or slight differences that do not substantially impact the overall message.
3. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
    - **Inaccurate disclosure:** Information incorrectly stated or mistranslated.
    - **Misleading content:** Statements or omissions that could cause misunderstanding or misrepresentation.
    - **Missing content:** Significant sections or details in one document but absent in the other.
    - **Outdated information:** Data or statements no longer accurate or relevant.
    - **Major deviations from Document 1:** Substantial differences in meaning or critical information.
4. For each flag, include:
  - A list of applicable difference types (from the list above)
  - The relevant content from both documents, including the page number
  - An explanation of the difference, highlighting the main issues
5. You can flag same sentences or paragraphs more than once.
6. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.
7. **Ignore minor differences** that do not impact the meaning or intent, such as:
    - Slight variations in wording or phrasing.
    - Minor grammatical or stylistic changes.
    - Differences in formatting or punctuation.

### Output Format ###
After your comparison, provide your analysis in a JSON object using the structure below:

{{
  "flags": [
    {{
      "types": ["List of applicable difference types"],
      "doc1": {{
        "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
      }},
      "doc2": {{
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

### Example of a Major Discrepancy ###
{{
  "flags": [
    {{
      "types": ["Missing content"],
      "doc1": {{
        "content": "The policy clearly outlines <span style=\"color: red\">a 30-day return period</span>."
      }},
      "doc2": {{
        "content": "The policy does not mention the return period."
      }},
      "explanation": "Document 2 omits the return period, which could lead to confusion for customers."
    }}
  ]
}}

### Key Notes ###
- **Only flag differences that significantly affect content meaning or usability.**
- **Do not flag stylistic, grammatical, or formatting variations unless they create ambiguity.**
- Ensure the JSON structure is valid and complete.
                """
            case _:
                system_prompt = """
              You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

              Here are the two documents you need to compare:

              <document1>
              {doc1}
              </document1>

              ## END OF DOCUMENT 1 ##

              <document2>
              {doc2}
              </document2>

              ## END OF DOCUMENT 2 ##

              Please follow these steps to complete your analysis:

              1. Carefully read and compare both documents until you reach the ## END OF DOCUMENT ## line by line, paragraph by paragraph.
              2. Ensure that every part of both documents is given equal attention, from the beginning to the end.
              3. Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content.
              4. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
                - Inaccurate disclosure: Information that is incorrectly stated or translated
                - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
                - Outdated information: Data or statements that are no longer relevant or accurate
                - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
                - Major deviations from the English version: Any substantial differences from Document 1
                - Structural Difference: The same content is labelled in different enumeration labels [like (a)(b)(c) or 1, 2, 3]
              5. For each flag, include:
                - A list of applicable difference types (from the list above)
                - The relevant content from both documents, including the page number
                - An explanation of the difference, highlighting the main issues
              6. You can flag same sentences or paragraphs more than once.
              7. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.
              8. If there is no major discrepancy, just reponse with an empty list. Don't explain that there is no discrepancy.

              After your comparison, format your response as a JSON object with the following structure:

              {{
                "flags": [
                  {{
                    "types": ["List of applicable difference types"],
                    "doc1": {{
                      "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
                    }},
                    "doc2": {{
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

        # system_prompt = """
        # ### Context ###
        # You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents and identify **only major discrepancies** that could significantly alter the meaning, interpretation, or usability of the content.

        # Here are the two documents you need to compare:

        # <Document1>
        # {doc1}
        # </Document1>

        # ## END OF DOCUMENT 1 ##

        # <Document2>
        # {doc2}
        # </Document2>

        # ## END OF DOCUMENT 2 ##

        # ### Instructions for Analysis ###
        # Please follow these steps to complete your analysis:

        # 1. Compare both documents carefully until the ## END OF DOCUMENT ## markers, line by line, paragraph by paragraph.
        # 2. Identify only the major discrepancies between the documents. Focus on significant discrepancies that change the meaning, interpretation, or intent of the content. Avoid highlighting minor wording, phrasing variations or slight differences that do not substantially impact the overall message.
        # 3. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
        #    - **Inaccurate disclosure:** Information incorrectly stated or mistranslated.
        #    - **Misleading content:** Statements or omissions that could cause misunderstanding or misrepresentation.
        #    - **Missing content:** Significant sections or details in one document but absent in the other.
        #    - **Outdated information:** Data or statements no longer accurate or relevant.
        #    - **Major deviations from Document 1:** Substantial differences in meaning or critical information.
        # 4. For each flag, include:
        #   - A list of applicable difference types (from the list above)
        #   - The relevant content from both documents, including the page number
        #   - An explanation of the difference, highlighting the main issues
        # 5. You can flag same sentences or paragraphs more than once.
        # 6. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.
        # 7. **Ignore minor differences** that do not impact the meaning or intent, such as:
        #    - Slight variations in wording or phrasing.
        #    - Minor grammatical or stylistic changes.
        #    - Differences in formatting or punctuation.

        # ### Output Format ###
        # After your comparison, provide your analysis in a JSON object using the structure below:

        # {{
        #   "flags": [
        #     {{
        #       "types": ["List of applicable difference types"],
        #       "doc1": {{
        #         "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
        #       }},
        #       "doc2": {{
        #         "content": "Relevant content from Document 2 with <span style=\"color: red\">highlighted difference</span>"
        #       }},
        #       "explanation": "Detailed explanation of the difference"
        #     }}
        #   ]
        # }}

        # If no major discrepancies are found, your JSON response should be:

        # {{
        #   "flags": []
        # }}

        # Remember to use proper JSON formatting, including quotes around keys and string values, and commas to separate objects and key-value pairs. Don't need to include any language identifiers like ```json in the output.

        # ### Example of a Major Discrepancy ###
        # {{
        #   "flags": [
        #     {{
        #       "types": ["Missing content"],
        #       "doc1": {{
        #         "content": "The policy clearly outlines <span style=\"color: red\">a 30-day return period</span>."
        #       }},
        #       "doc2": {{
        #         "content": "The policy does not mention the return period."
        #       }},
        #       "explanation": "Document 2 omits the return period, which could lead to confusion for customers."
        #     }}
        #   ]
        # }}

        # ### Key Notes ###
        # - **Only flag differences that significantly affect content meaning or usability.**
        # - **Do not flag stylistic, grammatical, or formatting variations unless they create ambiguity.**
        # - Ensure the JSON structure is valid and complete."""

        user_prompt = """Begin your analysis now."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", user_prompt)]
        )

        def loop_invoke(chunks: List[Dict]) -> List[Dict]:
            flags = []
            loop_chain = prompt | self.chat_model | StrOutputParser()

            with st.spinner("Comparing Documents"):
                progress_bar = st.progress(0)
                for index, chunk in enumerate(chunks):
                    progress_bar.progress((index + 1) / len(chunks))
                    response = loop_chain.invoke(
                        {
                            "doc1": chunk["doc1"]["content"],
                            "doc2": chunk["doc2"]["content"],
                        }
                    )
                    flag_list = json.loads(
                        self.document_processor.remove_code_fences(response)
                    )["flags"]

                    for flag in flag_list:
                        flag["doc1"]["page"] = chunk["doc1"]["page"]
                        flag["doc2"]["page"] = chunk["doc2"]["page"]

                        suggestions = self.suggestion_chain.invoke_suggestion_chain(
                            document1=flag["doc1"]["content"],
                            document2=flag["doc2"]["content"],
                            target_documents="Document 1, Document 2",
                            explanation=flag["explanation"],
                        )
                        flag["suggestions"] = suggestions

                    flags.append(flag_list)
                progress_bar.empty()
            return {"flags": sum(flags, [])}

        processor_chain = RunnableLambda(self.chunk_documents) | (
            lambda x: loop_invoke(x)
        )

        return processor_chain

    def invoke_chain(
        self,
        doc1_file_bytes: Union[BytesIO, bytes],
        doc2_file_bytes: Union[BytesIO, bytes],
        xml_file_path: Optional[str] = None,
        use_existing_file: bool = False,
        chat_id: Optional[str] = None,
    ) -> Mismatches:
        doc1 = self.document_processor.extract_filtered_content(doc1_file_bytes)[
            "document"
        ]
        doc2 = self.document_processor.extract_filtered_content(doc2_file_bytes)[
            "document"
        ]
        final_chain = self._comparison_chain()
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

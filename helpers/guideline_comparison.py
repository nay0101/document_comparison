from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from io import BytesIO
from typing import Union, Optional, List, Dict
from langfuse.callback import CallbackHandler
from .types import Model, Deviation, GuidelineInfo
from .llm_integrations import get_llm
from .document_processor import DocumentProcessor
import streamlit as st
import os

environment = os.getenv("ENVIRONMENT")


class GuidelineComparisonChain:
    def __init__(self, chat_model_name: Model = "gpt-4o", temperature: float = 0.0):
        self.chat_model_name = chat_model_name
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()

    def _guideline_comparison_chain(self) -> Runnable:
        # instruction = """
        # You are an expert analyst tasked with comparing a document against a guideline to identify any deviations or exceptions. Your goal is to provide a comprehensive and exhaustive list of instances where the document does not adhere to or contradicts the guideline.

        # First, carefully read and understand the following guideline:

        # <guideline>
        # {guideline}
        # </guideline>

        # Now, read and analyze the following document:

        # <document>
        # {document}
        # </document>

        # Your task is to compare the document against the guideline, paying close attention to any deviations or exceptions. Follow these steps:

        # 1. Thoroughly read both the guideline and the document.
        # 2. Compare the document to the guideline, treating the guideline as a whole.
        # 3. Identify any instances where the document deviates from or contradicts the guideline.
        # 4. Group related deviations together under a single exception.
        # 5. For each group of deviations, formulate a recommendation on how to fix them to align with the guideline.

        # After your comparison breakdown, present your findings in the following JSON format:

        # {{
        #   "guideline": <Quote the original guideline here>,
        #   "exceptions": [
        #     {{
        #       "description": <Describe the group of related deviations>,
        #       "issue_items": [
        #         <List individual deviations within this group>,
        #         <Repeat for each individual deviation in this group>
        #       ],
        #       "fix_recommendations": [
        #         <Suggest how to fix an issue item from deviation, with an example if possible>,
        #         <Repeat for each individual issue item in this group>
        #       ]
        #     }},
        #     <Repeat for each group of exceptions found>
        #   ]
        # }}

        # If you find no exceptions, your output should look like this:

        # {{
        #   "guideline": <Quote the original guideline here>,
        #   "exceptions": [],
        # }}

        # Remember to be thorough and identify all possible exceptions. Your analysis should cover the entire document and consider all aspects of the guideline.
        # """

        if environment == "development":
            with open("./test.json", "w") as file:
                file.write("{\n")

        def formatted_prompt(_input: Dict):
            guideline = _input["guideline"]
            image_urls = _input["image_urls"]
            document = _input["document"]
            user_message = [
                {
                    "type": "text",
                    "text": f"""<guideline>{guideline}</guideline>\n{'Refer to the images in the provided sequence for accurate output. The text does not need to be an exact match in the case of comparing the layouts but should follow the expected layout, including correct section order, headings, and formatting elements like tables and lists.' if image_urls else ''}""",
                },
            ]
            for image in image_urls:
                user_message.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image},
                    },
                )

            instruction = f"""
        You are an expert analyst tasked with comparing a document against a guideline that the user provides to identify any deviations or exceptions. Your goal is to provide a comprehensive and exhaustive list of instances where the document does not adhere to or contradicts the guideline.

        First, carefully read and understand the guideline provided by the user.

        And then, read and analyze the following document:

        <document>
        {document}
        </document>

        Your task is to compare the document against the guideline, paying close attention to any deviations or exceptions. Follow these steps:

        1. Thoroughly read both the guideline and the document.
        2. Compare the document to the guideline, treating the guideline as a whole.
        3. Identify any instances where the document deviates from or contradicts the guideline.
        4. Group related deviations together under a single exception.
        5. For each group of deviations, formulate a recommendation on how to fix them to align with the guideline.

        After your comparison breakdown, present your findings in the following JSON format:

        {{{{
          "guideline": <Quote the original guideline here>,
          "exceptions": [
            {{{{
              "description": <Describe the group of related deviations>,
              "issue_items": [
                <List individual deviations within this group>,
                <Repeat for each individual deviation in this group>
              ],
              "fix_recommendations": [
                <Suggest how to fix an issue item from deviation, with an example if possible>,
                <Repeat for each individual issue item in this group>
              ]
            }}}},
            <Repeat for each group of exceptions found>
          ]
        }}}}

        If you find no exceptions, your output should look like this:

        {{{{
          "guideline": <Quote the original guideline here>,
          "exceptions": [],
        }}}}

        Remember to be thorough and identify all possible exceptions. Your analysis should cover the entire document and consider all aspects of the guideline.
        Remember to just response with the JSON format.
        """

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", instruction),
                    ("user", user_message),
                ]
            )

            return prompt

        def loop_invoke(_input: Dict) -> List[Dict]:
            guidelines = _input["guidelines"]
            document = _input["document"]
            deviations = []

            loop_chain = formatted_prompt | self.chat_model | StrOutputParser()

            with st.spinner("Comparing"):
                progress_bar = st.progress(0)
                for index, chunk in enumerate(guidelines):
                    progress_bar.progress((index + 1) / len(guidelines))
                    guideline = chunk["clause"]
                    image_urls = chunk["image_urls"]
                    output = loop_chain.invoke(
                        {
                            "guideline": guideline,
                            "image_urls": image_urls,
                            "document": document,
                        },
                    )

                    deviations.append(
                        self.document_processor.remove_code_fences(output)
                    )

                    if environment == "development":
                        with open("./test.json", "a") as file:
                            file.write(f"{output},")

                progress_bar.empty()

                if environment == "development":
                    with open("./test.json", "a") as file:
                        file.write("}")

            return deviations

        chain = RunnableLambda(loop_invoke)

        return chain

    def invoke_chain(
        self,
        guidelines: List[GuidelineInfo],
        document_file: Union[BytesIO, bytes],
        chat_id: Optional[str] = None,
    ) -> List[Deviation]:
        document = self.document_processor.extract_full_content(document_file)
        chain = self._guideline_comparison_chain()

        output = chain.invoke(
            {
                "guidelines": guidelines,
                "document": document,
            },
            config={"callbacks": [CallbackHandler(user_id=str(chat_id))]},
        )

        return output

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from io import BytesIO
from typing import Union, Optional, List, Dict
from langfuse.callback import CallbackHandler
from .types import Model, Deviation, GuidelineInfo, InputType
from .llm_integrations import get_llm
from .document_processor import DocumentProcessor
from .models import ClauseComparisonReport
import streamlit as st
import os
from pydantic import BaseModel, Field
import json
import base64

environment = os.getenv("ENVIRONMENT")


class GuidelineComparisonChain:
    def __init__(
        self,
        chat_model_name: Model = "gpt-5",
        temperature: float = 0.0,
        instruction: str = None,
    ):
        self.chat_model_name = chat_model_name
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()
        self.instruction = instruction

    def _guideline_comparison_chain(self) -> Runnable:

        if environment == "development":
            with open("./test.json", "w") as file:
                file.write("{\n")

        def formatted_prompt(_input: Dict):
            guideline = _input["guideline"]
            attachments = _input["attachments"]
            document = _input["document"]

            user_message = [
                {
                    "type": "text",
                    "text": f"""# Guideline Section
{guideline["text"]}""",
                },
            ]
            for image in sorted(guideline["images"]):
                with open(image, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode("utf-8")
                user_message.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                )

            if attachments and len(attachments) > 0:
                user_message.append({"type": "text", "text": f"# Attachments"})
                for index, attachment in enumerate(attachments):
                    user_message.append(
                        {
                            "type": "text",
                            "text": f"**Attachment {index+1}:** {attachment['text']}",
                        }
                    )
                    for image in sorted(attachment["images"]):
                        with open(image, "rb") as f:
                            base64_image = base64.b64encode(f.read()).decode("utf-8")

                        user_message.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        )

            user_message.append(
                {
                    "type": "text",
                    "text": f"""# Document to compare against
{document['text']}""",
                }
            )

            for image in sorted(document["images"]):
                with open(image, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode("utf-8")
                user_message.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                )

            instruction = """You are an expert compliance analyst. Extract **every clause** from a guideline section (e.g., “S 16.1…”, “G 16.2…”) and compare **each clause** against the provided document. Produce one result **per clause**, covering **all clauses** in order. Also produce a **summary** that lists the clause IDs by outcome.

## Clause extraction
- Treat a **clause** as any block that begins with `S` or `G` followed by a space and a numeric identifier (e.g., `S 16.1`, `G 16.2`, `S 16.14`).
- The **clause text** runs from its identifier to **just before** the next `S xx.x` / `G xx.x` identifier or the end of the guideline section.
- Define **clause ID** as the leading token (e.g., `S 16.1`, `G 16.2`) that appears at the start of the clause.

## Applicability & evaluation policy
- **Clause types**:
  - `S` = **Standard / Mandatory** → evaluate **strictly**.
  - `G` = **Guidance / Secondary** → evaluate **leniently** (good to follow; okay if not), but still return an outcome.
- **Applicability test** (per clause):
  - If a clause applies only under certain conditions (e.g., telemarketing distribution, riders, Islamic products, intermediaries), and the document **does not evidence** that condition, mark **"not-applicable"**.
- **Verification rules**:
  - Analyse word-to-word, paragraph-to-paragraph, and sequence-to-sequence against the clause.  
  - If the clause references external templates, notes, appendices, or **requires external actions outside the provided document (e.g., will provide in person, will check externally)**, mark **"not-applicable"**.  
  - If *any* required element is missing, unclear, contradicted, out-of-sequence, or only partially satisfied, mark **"non-complied"**.  
  - Only mark **"complied"** if **every sentence, paragraph, and sequence in the document fully and unambiguously satisfies the clause, with no exceptions or partial alignment**.  
  - Any doubt = **"non-complied"**.

## Evidence discipline
- Base your assessment **only** on the provided guideline and document text. Do **not** assume unstated facts or use external sources.
- Be consistent and deterministic across all clauses.

## Content Focus
- Focus on textual content. Images are supplementary and should not be the primary basis for compliance decisions.

## Output rules (strict)
- Respond **only** with a valid **JSON object** (no extra text, no code fences).
- The object must have **two keys**: `"results"` and `"summary"`.

**1) `results`**  
- Type: **array** of objects.  
- Include **one object per extracted clause**, in the **same order** as in the guideline.  
- Use **exactly** these keys in every object:
  - `"clause"`: the full clause text beginning with its identifier (e.g., `"S 16.1 A FSP shall …"`).
  - `"isComplied"`: `"complied"` | `"non-complied"` | `"not-applicable"`.
  - `"reason"`:
    - If `"isComplied" = "complied"` → a **brief description** of why it is complied (reference where the document aligns).
    - If `"non-complied"` → brief, concrete reason citing what is missing/contradicted/not in required order.
    - If `"not-applicable"` → state why it cannot be assessed or why it does not apply.

**2) `summary`**  
- Type: **object** with exactly these keys:
  - `"complied"`: array of **clause IDs** (e.g., `["S 16.1", "G 16.7"]`) in guideline order.
  - `"nonComplied"`: array of clause IDs in guideline order.
  - `"notApplicable"`: array of clause IDs in guideline order.
- A **clause ID** is the leading token of each clause (e.g., `S 16.1`, `G 16.2`). Do **not** include the rest of the clause text in the summary lists.

### JSON schema (example shape; do not include comments in your output)
{{{{
  "results": [
    {{{{
      "clause": "S 16.1 A FSP shall provide a PDS …",
      "isComplied": "non-complied",
      "reason": "PDS sequence cannot be verified against required template; referenced Notes/templates not provided."
    }}}},
    {{{{
      "clause": "G 16.2 For the avoidance of doubt …",
      "isComplied": "complied",
      "reason": "The document’s wording and order broadly align with the clause’s intent."
    }}}}
  ],
  "summary": {{{{
    "complied": ["G 16.2"],
    "nonComplied": ["S 16.1"],
    "notApplicable": []
  }}}}
}}}}"""

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

            loop_chain = (
                formatted_prompt
                | self.chat_model.with_structured_output(ClauseComparisonReport)
                # | StrOutputParser()
            )

            with st.spinner("Comparing"):
                progress_bar = st.progress(0)
                for index, chunk in enumerate(guidelines):
                    progress_bar.progress((index + 1) / len(guidelines))
                    guideline = chunk["clauses"]
                    attachments = chunk["attachments"]
                    output = loop_chain.invoke(
                        {
                            "guideline": guideline,
                            "attachments": attachments,
                            "document": document,
                        },
                    )

                    json_response = json.loads(output.model_dump_json())
                    json_response["title"] = chunk["title"]
                    deviations.append(json_response)

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
        document_file: InputType,
        chat_id: Optional[str] = None,
    ) -> List[Deviation]:
        # document = self.document_processor.extract_full_content(document_file)
        chain = self._guideline_comparison_chain()

        output = chain.invoke(
            {
                "guidelines": guidelines,
                "document": document_file,
            },
            config={"callbacks": [CallbackHandler(user_id=str(chat_id))]},
        )

        return output

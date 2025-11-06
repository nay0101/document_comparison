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
from .models import ClauseComparisonReport, FinalComparisonResult
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
                    "text": f"""# Document section to compare against
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

            #             instruction = """You are an expert compliance analyst. Extract **every clause** from a guideline section (e.g., “S 16.1…”, “G 16.2…”) and compare **each clause** against the provided document. Produce one result **per clause**, covering **all clauses** in order. Also produce a **summary** that lists the clause IDs by outcome.

            # ## Clause extraction
            # - Treat a **clause** as any block that begins with `S` or `G` followed by a space and a numeric identifier (e.g., `S 16.1`, `G 16.2`, `S 16.14`).
            # - The **clause text** runs from its identifier to **just before** the next `S xx.x` / `G xx.x` identifier or the end of the guideline section.
            # - Define **clause ID** as the leading token (e.g., `S 16.1`, `G 16.2`) that appears at the start of the clause.

            # ## Applicability & evaluation policy
            # - **Clause types**:
            #   - `S` = **Standard / Mandatory** → evaluate **strictly**.
            #   - `G` = **Guidance / Secondary** → evaluate **leniently** (good to follow; okay if not), but still return an outcome.
            # - **Applicability test** (per clause):
            #   - If a clause applies only under certain conditions (e.g., telemarketing distribution, riders, Islamic products, intermediaries), and the document **does not evidence** that condition, mark **"not-applicable"**.
            # - **Verification rules**:
            #   - Analyse word-to-word, paragraph-to-paragraph, and sequence-to-sequence against the clause.
            #   - If the clause references external templates, notes, appendices, or **requires external actions outside the provided document (e.g., will provide in person, will check externally)**, mark **"not-applicable"**.
            #   - If *any* required element is missing, unclear, contradicted, out-of-sequence, or only partially satisfied, mark **"non-complied"**.
            #   - Only mark **"complied"** if **every sentence, paragraph, and sequence in the document fully and unambiguously satisfies the clause, with no exceptions or partial alignment**.
            #   - Any doubt = **"non-complied"**.

            # ## Evidence discipline
            # - Base your assessment **only** on the provided guideline and document text. Do **not** assume unstated facts or use external sources.
            # - Be consistent and deterministic across all clauses.

            # ## Content Focus
            # - Focus on textual content. Images are supplementary and should not be the primary basis for compliance decisions.

            # ## Output rules (strict)
            # - Respond **only** with a valid **JSON object** (no extra text, no code fences).
            # - The object must have **two keys**: `"results"` and `"summary"`.

            # **1) `results`**
            # - Type: **array** of objects.
            # - Include **one object per extracted clause**, in the **same order** as in the guideline.
            # - Use **exactly** these keys in every object:
            #   - `"clause"`: the full clause text beginning with its identifier (e.g., `"S 16.1 A FSP shall …"`).
            #   - `"isComplied"`: `"complied"` | `"non-complied"` | `"not-applicable"`.
            #   - `"reason"`:
            #     - If `"isComplied" = "complied"` → a **brief description** of why it is complied (reference where the document aligns).
            #     - If `"non-complied"` → brief, concrete reason citing what is missing/contradicted/not in required order.
            #     - If `"not-applicable"` → state why it cannot be assessed or why it does not apply.

            # **2) `summary`**
            # - Type: **object** with exactly these keys:
            #   - `"complied"`: array of **clause IDs** (e.g., `["S 16.1", "G 16.7"]`) in guideline order.
            #   - `"nonComplied"`: array of clause IDs in guideline order.
            #   - `"notApplicable"`: array of clause IDs in guideline order.
            # - A **clause ID** is the leading token of each clause (e.g., `S 16.1`, `G 16.2`). Do **not** include the rest of the clause text in the summary lists.

            # ### JSON schema (example shape; do not include comments in your output)
            # {{{{
            #   "results": [
            #     {{{{
            #       "clause": "S 16.1 A FSP shall provide a PDS …",
            #       "isComplied": "non-complied",
            #       "reason": "PDS sequence cannot be verified against required template; referenced Notes/templates not provided."
            #     }}}},
            #     {{{{
            #       "clause": "G 16.2 For the avoidance of doubt …",
            #       "isComplied": "complied",
            #       "reason": "The document’s wording and order broadly align with the clause’s intent."
            #     }}}}
            #   ],
            #   "summary": {{{{
            #     "complied": ["G 16.2"],
            #     "nonComplied": ["S 16.1"],
            #     "notApplicable": []
            #   }}}}
            # }}}}"""

            instruction = """You are an expert compliance analyst. Extract **every clause** from a guideline section (e.g., “S 16.1…”, “G 16.2…”) and compare **each clause** against the provided document. Produce one result **per clause**, covering **all clauses** in order. Also produce a **summary** that lists the clause IDs by outcome.

## Clause extraction
- Treat a **clause** as any block that begins with `S` or `G` followed by a numeric identifier (e.g., `S 16.1`, `G 16.2`, `S 16.14`).
- The **clause text** runs from its identifier to **just before** the next `S xx.x` / `G xx.x` identifier or the end of the guideline section.
- Define **clause ID** as the leading token (e.g., `S 16.1`, `G 16.2`) that appears at the start of the clause.

## Applicability & evaluation policy
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
- Look at both textual content and images for compliance assessment.

## Output rules (strict)
- Respond **only** with a valid **JSON object** (no extra text, no code fences).
- The object must have **one key**: `"results"`.

**1) `results`**
- Type: **array** of objects.
- Include **one object per extracted clause**, in the **same order** as in the guideline.
- Use **exactly** these keys in every object:
  - `"clauseId"`: the identifier of the clause (e.g., `"S 16.1"`).
  - `"clause"`: the full clause text beginning with its identifier (e.g., `"S 16.1 A FSP shall …"`).
  - `"isComplied"`: `"complied"` | `"non-complied"` | `"not-applicable"`.
  - `"reason"`:
    - If `"isComplied" = "complied"` → a **brief description** of why it is complied (reference where the document aligns).
    - If `"non-complied"` → detailed reasoning of what is missing/contradicted/not in required order.
    - If `"not-applicable"` → state why it cannot be assessed or why it does not apply.
  - `"suggestions"`:
    - If `"non-complied"` → provide a **clear, actionable suggestions** on how the document can be modified to comply (e.g., “Add a disclosure section detailing XYZ as required by S 16.1”).
    - Leave blank (`[]`) for `"complied"` and `"not-applicable"`.

### JSON schema (example shape; do not include comments in your output)
{{
  "results": [
    {{
      "clauseId": "S xx.x",
      "clause": "S xx.x A FSP shall provide a PDS …",
      "isComplied": "non-complied",
      "reason": "The required PDS structure and disclosures are missing.",
      "suggestions": ["Add a full Product Disclosure Statement section including risk warnings, fees, and comparison table as required by S 16.1."]
    }},
    {{
      "clauseId": "G xx.x",
      "clause": "G xx.x For the avoidance of doubt …",
      "isComplied": "complied",
      "reason": "The document’s structure and intent broadly align.",
      "suggestions": []
    }},
    {{
      "clauseId": "G 16.4",
      "clause": "G 16.4 Product summary must be written in plain language.",
      "isComplied": "non-complied",
      "reason": "The document uses formal and legal-style language, such as 'pursuant to the aforementioned provisions' and 'hereinafter referred to as', which makes the summary difficult for ordinary readers to understand. Sentences are long and packed with multiple ideas, reducing readability.",
      "suggestions": [
        "Replace 'pursuant to the aforementioned provisions' → 'under the rules mentioned above'.",
        "Replace 'hereinafter referred to as' → 'called'.",
        "Change 'the applicant is required to submit documentation for verification purposes' → 'you must send us your documents so we can check them'.",
        "Customers who wish to terminate their policy prior to its maturity date are required to submit a written notice to the service department within thirty (30) calendar days, failing which the termination request shall not be processed.' → 'If you want to end your policy early, send us a written notice. You must do this within 30 days. We cannot process your request after that period.'",
        "Use direct, friendly wording such as 'you' and 'we' to make it easier to follow."
      ]
    }},
    {{
      "clauseId": "S 16.5",
      "clause": "S 16.5 All instructions provided to customers shall be clear, concise, and written in plain language.",
      "isComplied": "non-complied",
      "reason": "The document mixes instruction and warning text, with phrases like 'it is incumbent upon the user to ensure compliance with all stipulated requirements', which are too formal and may confuse customers. There is no simple step-by-step guide to actions.",
      "suggestions": [
        "Replace 'it is incumbent upon the user to ensure compliance with all stipulated requirements' → 'you must follow these steps carefully'.",
        "Replace 'prior to the initiation of the process' → 'before you start'.",
        "Divide instructions into clear numbered steps (1, 2, 3).",
        "Add short headings like 'Before you apply', 'What you need', and 'How to finish'.",
        "Remove duplicate warnings and keep one clear statement in plain wording."
      ]
    }},
    {{
      "clauseId": "G 16.6",
      "clause": "G 16.6 The disclosure section should be understandable to a reader with no financial background.",
      "isComplied": "non-complied",
      "reason": "The disclosure section contains technical terms such as 'amortization schedule', 'liquidity buffer', and 'compound yield' with no explanation or examples. A reader without financial experience would not easily understand these terms or their impact.",
      "suggestions": [
        "Add simple explanations beside key terms, e.g., 'amortization schedule (how you pay back your loan over time)'.",
        "Replace 'liquidity buffer' → 'money kept aside for emergencies'.",
        "Replace 'compound yield' → 'how your money grows when interest is added to previous interest'.",
        "Include short examples like 'If you invest $1,000, you will earn $50 in interest each year'.",
        "Add a short 'In simple terms' box summarizing the main ideas in everyday language."
      ]
    }}
  ],
}}
"""

            #             instruction = """# Guideline Clause Compliance Comparison Prompt

            # You are an **expert compliance analyst**.
            # Compare **each clause** from a provided guideline section (e.g., “S 16.1…”, “G 16.2…”) against the **provided document**.
            # The analysis must operate **per clause** and output one result **for every extracted clause**, in **original order**.
            # ---

            # ## Clause Extraction Rules

            # - A **clause** is any block that begins with `S` or `G` followed by a numeric identifier (e.g., `S 16.1`, `G 16.2`, `S 16.14`).
            # - The **clause text** starts from its identifier up to **before** the next `S xx.x` / `G xx.x` identifier or the end of the guideline section.
            # - The **clause ID** is the leading token (e.g., `S 16.1`, `G 16.2`).

            # ---

            # ## Applicability and Evaluation Policy

            # ### Applicability Test
            # - If a clause applies only under **specific conditions** (e.g., telemarketing distribution, riders, intermediaries, Islamic products), and the provided document **section does not show evidence** of those conditions, mark as:
            #   - `"isComplied": "not-applicable"`

            # ### Section-Based Evaluation
            # - The assessment is based **only on the provided section**, not on the entire document.
            # - If the clause refers to layout, visuals, or structure, **partial layout or partial evidence** in the section is sufficient for compliance consideration.
            # - If the section **lacks sufficient information** to assess the clause, mark as `"not-applicable"`.

            # ---

            # ## Verification Rules

            # For each clause:

            # - Perform **textual and structural comparison** (word-to-word, paragraph-to-paragraph, and sequence-to-sequence) between the clause and the document section.
            # - If the clause requires **external materials, references, or actions** and they are not provided (e.g., “will provide externally,” “see appendix”), mark `"not-applicable"`.
            # - Mark:
            #   - `"complied"` → every requirement in the clause is **fully and unambiguously** satisfied by the section.
            #   - `"non-complied"` → any element is **missing, unclear, contradicted, or incomplete**.
            #   - `"not-applicable"` → cannot be assessed from the given section or not relevant to its content.
            # - **Any uncertainty = "non-complied"**, unless the clause itself is clearly inapplicable.

            # ---

            # ## Evidence and Consistency Rules

            # - Base judgments **solely** on the text visible in the provided guideline and section.
            # - Do **not infer or assume** unstated facts.
            # - Maintain **consistent, deterministic logic** across all clauses.

            # ---

            # ## Content Focus
            # - Focus on textual content. Images are supplementary and should not be the primary basis for compliance decisions.
            # - But for layout/visual structure requirements, partial layout or partial evidence in the section is sufficient for compliance consideration.

            # ---

            # ## Output Format

            # Respond **only** with a valid **JSON object**.
            # Do **not** include extra text, comments, or code fences.

            # ### JSON Structure

            # ```json
            # {{
            #   "results": [
            #     {{
            #       "clauseId": "S xx.x",
            #       "clause": "S xx.x A FSP shall provide a PDS …",
            #       "isComplied": "non-complied",
            #       "reason": "The required PDS disclosures are missing or incomplete.",
            #       "suggestion": "Add a full Product Disclosure section detailing risk warnings, fees, and comparison tables as required by S xx.x."
            #     }},
            #     {{
            #       "clauseId": "G xx.x",
            #       "clause": "G xx.x For the avoidance of doubt …",
            #       "isComplied": "complied",
            #       "reason": "The document section aligns with the intent and content of the guideline.",
            #       "suggestion": ""
            #     }},
            #     {{
            #       "clauseId": "S xx.y",
            #       "clause": "S xx.y A FSP must maintain records of …",
            #       "isComplied": "not-applicable",
            #       "reason": "This clause applies to record-keeping processes not represented in the provided section.",
            #       "suggestion": ""
            #     }}
            #   ]
            # }}
            # """

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", instruction),
                    ("user", user_message),
                ]
            )

            return prompt

        def loop_invoke(_input: Dict) -> List[Dict]:
            guidelines = _input["guidelines"]
            documents = _input["documents"]
            final_comparisons: List[FinalComparisonResult] = []

            loop_chain = (
                formatted_prompt
                | self.chat_model.with_structured_output(ClauseComparisonReport)
                # | StrOutputParser()
            )

            with st.spinner("Comparing"):
                progress_bar = st.progress(0)
                for index, chunk in enumerate(guidelines):
                    final_comparisons.append(
                        {"section": chunk["title"], "comparisons": []}
                    )
                    print(f"Processing guideline section: {chunk['title']}")
                    print(f"documents to compare against: {len(documents)}")
                    for index_doc, document in enumerate(documents):
                        print(f"  Comparing against document {index_doc+1}")
                        print(document)
                        progress_bar.progress(
                            int(
                                (index * len(documents) + index_doc)
                                / (len(guidelines) * len(documents))
                                * 100
                            )
                        )
                        guideline = chunk["clauses"]
                        attachments = chunk["attachments"]
                        output = loop_chain.invoke(
                            {
                                "guideline": guideline,
                                "attachments": attachments,
                                "document": document,
                            },
                        )

                        print(f"    Output: {output}")
                        json_response = json.loads(output.model_dump_json())
                        json_response["snippet"] = document["text"]
                        final_comparisons[index]["comparisons"].append(json_response)

                        if environment == "development":
                            with open("./test.json", "a") as file:
                                file.write(f"{output},")

                # Flatten the results by clauseNumber across all documents. Final output - [{section, comparisons: [{clauseNumber, clause, results: [{isComplied, reason}]}]}].
                flattened_results = []
                for comparison in final_comparisons:
                    section = comparison["section"]
                    clause_dict = {}
                    for comp in comparison["comparisons"]:
                        for result in comp["results"]:
                            clause_id = result["clauseId"]
                            if clause_id not in clause_dict:
                                clause_dict[clause_id] = {
                                    "clauseId": clause_id,
                                    "clause": result["clause"],
                                    "results": [],
                                }
                            clause_dict[clause_id]["results"].append(
                                {
                                    "snippet": comp["snippet"],
                                    "isComplied": result["isComplied"],
                                    "reason": result["reason"],
                                    "suggestions": result["suggestions"],
                                }
                            )
                    flattened_results.append(
                        {
                            "section": section,
                            "comparisons": list(clause_dict.values()),
                        }
                    )
                progress_bar.empty()

                if environment == "development":
                    with open("./test.json", "a") as file:
                        file.write("}")

            with open("./test.json", "w") as file:
                json.dump(flattened_results, file)
            return [FinalComparisonResult(**fc) for fc in flattened_results]

        chain = RunnableLambda(loop_invoke)

        return chain

    def invoke_chain(
        self,
        guidelines: List[GuidelineInfo],
        documents: List[InputType],
        chat_id: Optional[str] = None,
    ) -> List[FinalComparisonResult]:
        # document = self.document_processor.extract_full_content(document_file)
        chain = self._guideline_comparison_chain()

        output = chain.invoke(
            {
                "guidelines": guidelines,
                "documents": documents,
            },
            config={"callbacks": [CallbackHandler(user_id=str(chat_id))]},
        )

        return output

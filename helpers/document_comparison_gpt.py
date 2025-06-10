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
import re


class DocumentComparisonGPT:
    """
    A class to handle document comparison using GPT.
    """

    def __init__(self, chat_model_name: Model = "gpt-4.1", temperature: float = 0.1):
        self.chat_model_name = chat_model_name
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()
        self.suggestion_chain = SuggestionChain(
            chat_model_name=chat_model_name, temperature=temperature
        )
        self.flag_list = []
        self.doc1 = None
        self.doc2 = None

    def invoke_chain(
        self,
        doc1_file_bytes: Union[BytesIO, bytes],
        doc2_file_bytes: Union[BytesIO, bytes],
        prev_flag: str = "",
        remaining_flags: int = 0,
        chat_id: Optional[str] = None,
    ) -> str:
        if self.doc1 is None or self.doc2 is None:
            self.doc1 = self.document_processor.extract_with_docling(doc1_file_bytes)
            self.doc2 = self.document_processor.extract_with_docling(doc2_file_bytes)
        doc1 = self.doc1
        doc2 = self.doc2
        if doc1 is None or doc2 is None:
            st.error("No document processor found. Please contact the administrator.")
            return
        flags = []
        with st.spinner("Comparing Documents"):
            try:
                chunks = self._comparison_chain(prev_flag, remaining_flags).stream(
                    {
                        "doc1": doc1,
                        "doc2": doc2,
                    },
                    config={"callbacks": [CallbackHandler(user_id=str(chat_id))]},
                )
                result = ""
                for chunk in chunks:
                    result += chunk
            except Exception as e:
                st.error(f"Error during document comparison: {e}")
                return str(e)

            json_str = result
            match = re.search(r"```json\s*(\{.*\})\s*```", result, re.DOTALL)
            if match:
                json_str = match.group(1)
                json_str = re.sub(r"}\s*//.*?(?=\s*\]\s*})", "}", json_str, re.DOTALL)
            try:
                result_dict = json.loads(json_str)  # Attempt to parse the JSON
                # if result_dict.get("flags"):  # Check if "flags" key exists and is not empty
                #     print(json.dumps(result_dict, indent=2))
                # else:
                #     print("No flags found in the result.")
            except json.JSONDecodeError as e:
                return json_str

            # flag_list = json.loads(self.document_processor.remove_code_fences(result))[
            #     "flags"
            # ]
            # result_dict = self.document_processor.extract_json_with_improved_regex(
            #     json_str
            # )
            flag_list = result_dict.get("flags")
            self.flag_list.extend(flag_list)
            total = result_dict.get("total")
            # if flag_list and len(flag_list) < int(total):
            #     return self.invoke_chain(
            #         doc1_file_bytes=doc1_file_bytes,
            #         doc2_file_bytes=doc2_file_bytes,
            #         chat_id=chat_id,
            #         prev_flag=json.dumps(flag_list[-1])
            #         .replace("{", "{{")
            #         .replace("}", "}}"),
            #         remaining_flags=int(total) - len(flag_list),
            #     )

            for flag in self.flag_list:
                suggestions = self.suggestion_chain.invoke_suggestion_chain(
                    document1=flag["doc1"]["content"],
                    document2=flag["doc2"]["content"],
                    target_documents="Document 1, Document 2",
                    explanation=flag["explanation"],
                )
                flag["suggestions"] = suggestions

            flags.append(flag_list)
            return {"flags": sum(flags, [])}

    def _comparison_chain(self, prev_flag, remaining_flags) -> Runnable:
        """Compares two documents"""

        instruction = """You are a meticulous linguistic analyst comparing English and Bahasa Malaysia versions of a legal document.

Your task is to create a comprehensive list of ALL discrepancies between the two documents.

1. Examine both documents with **WORD-LEVEL PRECISION** - compare every single word in corresponding sentences, even when the overall meaning appears equivalent
2. Compare documents section by section, paragraph by paragraph, and sentence by sentence to maintain proper alignment
3. **CRITICAL BIDIRECTIONAL ANALYSIS:** Check for discrepancies in BOTH directions systematically:
   - English → Bahasa Malaysia: What's missing or wrong in the BM version?
   - Bahasa Malaysia → English: What's missing or wrong in the English version?
4. For efficiency, combine multiple discrepancies from the same sentence or paragraph under one flag, but list each individual discrepancy within that flag

5. Pay special attention to these specific discrepancy patterns:
   **Missing Content:**
   - Missing words in either language
   - Missing translations of individual words within translated sentences
   - Additional descriptive words in one version not translated to the other
   - Asymmetric translations where one version has more qualifying words
   - Missing entire sentences or clauses in either version
   - Missing translations of phrases
   - Missing conjunctions or connecting words
   - Partial translations where some words are translated but key descriptive words are omitted
   
   **Spelling & Language Errors:**
   - Spelling errors in either language (IMPORTANT: even if there are other discrepancies in the same sentence, still point out spelling errors)
   - Wrong word translations
   - Language mixing (English words used in BM version or vice versa)
   
   **Structural & Formatting Issues:**
   - Different clause numbering between versions
   - Different numbering systems within lists
   - Different table/section references
   - Inconsistent terminology usage across documents
   - Word repetition errors
   
   **Content Interpretation Differences:**
   - Different amounts or percentages
   - Different website links between versions
   - Inaccurate translations that change meaning
   - Different transaction categories or descriptions
   - Additional words in one version that change meaning
   - Different interpretations of same concept
   - Missing qualifiers that change scope
   
   **Punctuation & Grammar:**
   - Missing commas, periods, or other punctuation
   - Different sentence structures that change meaning
   - Inconsistent use of quotation marks or brackets
   
   **Standardization Issues:**
   - Inconsistent translation of standard terms
   - Different word choices for same concept

6. **WORD-LEVEL ANALYSIS REQUIRED:** Even when sentences have the same general meaning, flag any missing or different words between versions. Perfect translation accuracy means EVERY word should have its equivalent representation, regardless of whether the sentence meaning is preserved

7. Both documents should reflect the exact same meaning and structure in the same order, with perfect translations - flag even the smallest discrepancies including:
   - Single character differences
   - Word order variations that change meaning
   - Missing or extra words that alter context
   - Incomplete translations where some words are translated but others are omitted
   - Unbalanced translations where one version has additional qualifying words
   - Any missing word even if the sentence meaning remains clear
   - Inconsistent translations of the same term throughout the document
   - Different interpretations that could mislead readers

8. **COMPLETE LINE CAPTURE MANDATORY:** When identifying corresponding sentences or clauses for comparison, you MUST capture and compare the ENTIRE line content from absolute beginning to absolute end, including all terminal words, conjunctions, and punctuation. Never truncate lines or stop before trailing conjunctions like "and", "or", semicolons, or any end-of-line elements.

9. **EXHAUSTIVE MULTIPLE DISCREPANCY DETECTION:** Within each sentence or clause, you MUST identify and flag ALL discrepancies present, not just the first one found. Conduct multiple passes through each sentence to ensure no discrepancy is missed. A single sentence may contain multiple different types of errors (missing words, wrong translations, spelling errors, punctuation differences, etc.) - document every single one. Do not stop analysis after finding one discrepancy; continue scanning the entire sentence until all issues are identified.

10. When highlighting differences:
   - Highlight ONLY the specific word or element that differs
   - For missing words, highlight the word in the version where it exists
   - For partial translations, highlight the missing word in the complete version and note its absence in the incomplete version
   - For asymmetric translations, highlight the additional word(s) in the more detailed version and note the absence in the simpler version
   - Check for discrepancies in BOTH directions (English→Bahasa Malaysia AND Bahasa Malaysia→English)
   - Ensure no discrepancy is missed from either document
   - For complex clauses: Scan the ENTIRE clause multiple times to catch all issues, don't stop after finding one discrepancy
   - Word-by-word comparison: Compare each word in equivalent sentences to catch missing individual word translations
   - FLAG EVEN MINOR WORD OMISSIONS: Even if sentence meaning is preserved, flag any missing words for complete accuracy

After your analysis, provide a JSON object with this structure:

```json
{{
  "total": "Total number of discrepancy flags found",
  "flags": [
    {{
      "location": "Precise location in the document (e.g., 'Paragraph 2, Sentence 1' or 'Section 3.1')",
      "doc1": {{
        "content": "Content from Document 1 (do not use double quotes in the content, use single quotes instead to avoid JSON parsing issues)",
      }},
      "doc2": {{
        "content": "Content from Document 2 (do not use double quotes in the content, use single quotes instead to avoid JSON parsing issues)"
      }},
      "discrepancies": [
        "1. List each individual discrepancy found in this location",
        "2. Another discrepancy in the same sentence/paragraph",
        "3. Third discrepancy if present"
      ],
      "explanation": "Brief explanation of all discrepancies in this location"
    }}
  ]
}}
```

**CRITICAL:** This is a highly sensitive legal document analysis. Do not worry about output length - generate ALL discrepancies found, no matter how many there are. Every single mismatch, missing word, spelling error, formatting difference, amount discrepancy, structural variation, or translation inconsistency must be documented. 

Based on actual review findings, expect to find dozens of discrepancies including missing brand names, incorrect translations, different numbering systems, wrong amounts, inconsistent terminology, structural differences, AND complex multi-issue clauses where multiple problems exist in single locations. Scan each clause thoroughly - don't stop after finding the first issue.

**BIDIRECTIONAL SCANNING:** Always check BOTH English→BM AND BM→English for missing content. Many discrepancies involve content present in one version but missing in the other. **Pay EXTRA attention to missing translations in the BM version - this is a common issue where English descriptive words are frequently omitted in Bahasa Malaysia translations.**

**TABLE CONTENT FOCUS:** For tables, compare only the content, headers, and data within the tables - do not flag differences in layout, formatting, or visual structure. Focus solely on textual content, amounts, and data accuracy.

**WORD-LEVEL PRECISION REQUIRED:** Flag ANY missing word, even if the overall sentence meaning is clear. Legal documents require perfect word-for-word accuracy, not just conceptual equivalence. A missing adjective, adverb, or descriptive word must be flagged regardless of whether the sentence still makes sense.

**ASYMMETRIC TRANSLATION DETECTION:** Also flag when one version has MORE qualifying words than the other. Both under-translation and over-specification must be detected.

Completeness is more important than brevity.
DO NOT summarize the output even if the output is very long. Provide the full detailed analysis of all the discrepancies you detected as specified.
DO NOT put anything comments in the JSON object. JSON object must be valid JSON.
---

Here are the two documents:

**ENGLISH_VERSION:**
{doc1}

**BAHASA_MALAYSIA_VERSION:**
{doc2}"""
        if prev_flag:
            instruction += f"""This is the previous flag

**PREVIOUS_FLAG:** {prev_flag}
Generate the next flag after this one. There are {remaining_flags} flags remaining to be generated.
"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Output all flags, even if it’s a long list. Do not truncate or summarize. Continue until everything is shown.",
                ),
                ("human", instruction),
            ]
        )

        chain = prompt | self.chat_model | StrOutputParser()
        return chain

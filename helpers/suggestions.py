from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from helpers.llm_integrations import get_llm
from dotenv import load_dotenv
from .types import Model
from .document_processor import DocumentProcessor
import json

load_dotenv()


class SuggestionChain:
    def __init__(self, chat_model_name: Model = "gpt-4o", temperature: float = 0.0):
        self.chat_model_name = chat_model_name
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()

    def _suggestion_chain(self):
        instruction = """
You are an expert in multilingual document comparison and modification. Your task is to analyze two documents in different languages and suggest changes to align them while preserving the original language and style of the target document(s).

Here are the two documents and their respective languages:

Document 1:
<document1>
{document1}
</document1>

Document 2:
<document2>
{document2}
</document2>

Now, here is the explanation of the differences between the two documents:
<comparison_explanation>
{explanation}
</comparison_explanation>

The document(s) that need to be modified are:
<target_document>
{target_documents}
</target_document>

Your task is to analyze the differences explained in the comparison explanation and suggest specific changes to make the target document(s) match the other document as closely as possible, while maintaining the original language and style of the target document(s).

Please follow these steps:

1. Analyze the documents and the comparison explanation.
2. Identify the key differences between the documents.
3. Generate {k} suggestions for modifying the target document(s).
4. Ensure that your suggested changes are appropriate for the language and context of the target document(s).
5. Consider any cultural or linguistic nuances that need to be addressed.

After your analysis, provide your suggestions in JSON format. The JSON structure should only include suggestions for the specified target document(s). Each suggestion should include the following:
- The original text
- The suggested modification (which should be the complete updated version of the original text)
- A version number (v1, v2, etc.)

Here's an example of the expected JSON structure (do not use this content in your response, it's just for illustration):

```json
{{
  "document1_suggestions": {{
    [
      {{
        "version": "v1",
        "modification": "Modified text here"
      }},
      {{
        "version": "v2",
        "modification": "Another modified text"
      }}
    ]
  }}
}}
```

Important notes:
1. Generate exactly {k} suggestions per target document. If both documents are targets, provide {k} suggestions for each.
2. Only include suggestions for the specified target document(s) in your JSON output.
3. Do not include explanations for the suggestions.

After completing your suggestions, review them to ensure they accurately address the differences noted in the comparison explanation and are appropriate for the target document's language and context.
"""

        user_input = "Begin your analysis now."

        prompt = ChatPromptTemplate.from_messages(
            [("system", instruction), ("user", user_input)]
        )

        chain = prompt | self.chat_model | StrOutputParser()

        return chain

    def invoke_suggestion_chain(
        self,
        document1: str,
        document2: str,
        explanation: str,
        target_documents: str,
        k: int = 1,
    ):
        chain = self._suggestion_chain()
        result = chain.invoke(
            {
                "document1": document1,
                "document2": document2,
                "explanation": explanation,
                "target_documents": target_documents,
                "k": k,
            }
        )
        json_result = json.loads(self.document_processor.remove_code_fences(result))
        return json_result

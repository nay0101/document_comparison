from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from helpers.llm_integrations import get_llm
from dotenv import load_dotenv
from .types import Model
from .document_processor import DocumentProcessor
import json
from typing import Optional
from langfuse.callback import CallbackHandler

load_dotenv()


class SimplificationChain:
    def __init__(self, chat_model_name: Model = "gpt-4o", temperature: float = 0.0):
        self.chat_model_name = chat_model_name
        self.chat_model = get_llm(model=chat_model_name, temperature=temperature)
        self.document_processor = DocumentProcessor()

    def _suggestion_chain(self):
        instruction = """
You are an expert in simplifying complex text while maintaining its core meaning. Your task is to simplify the following paragraph:

<paragraph_to_simplify>
{paragraph}
</paragraph_to_simplify>

You will produce <num_variations>{k}</num_variations> simplified version(s) of this paragraph.

Instructions:
1. Analyze the given paragraph thoroughly.
2. Simplify each sentence while maintaining the overall meaning and format.
3. Keep specific information like links, numbers, and other essential data intact.
4. Use plain language and active verbs.
5. Break down complex sentences into simpler ones when necessary.
6. Replace jargon or technical terms with simpler alternatives, unless they are crucial to the meaning.
7. Ensure that the main ideas are clearly conveyed.
8. For complex but necessary terms, simplify the surrounding language without removing these key terms.
9. Format the output as you see fit.

Provide the simplified version(s) of the paragraph in JSON format. The JSON structure should be as follows:

{{
  "simplifiedVersions": [
    {{
      "versionNumber": 1,
      "simplifiedText": "Your simplified paragraph here"
    }},
    {{
      "versionNumber": 2,
      "simplifiedText": "Your second simplified paragraph here (if applicable)"
    }}
  ]
}}

If only one version is requested, the JSON will contain only one object in the "simplifiedVersions" array.
"""

        user_input = "Please proceed with simplifying the given paragraph and formatting the output as specified."

        prompt = ChatPromptTemplate.from_messages(
            [("system", instruction), ("user", user_input)]
        )

        chain = prompt | self.chat_model | StrOutputParser()

        return chain

    def invoke_chain(
        self,
        paragraph: str,
        k: int = 1,
        chat_id: Optional[str] = None,
    ):
        chain = self._suggestion_chain()
        result = chain.invoke(
            {
                "paragraph": paragraph,
                "k": k,
            },
            config={"callbacks": [CallbackHandler(user_id=str(chat_id))]},
        )
        json_result = json.loads(self.document_processor.remove_code_fences(result))
        return json_result

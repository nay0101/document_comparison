from langchain_core.prompts import ChatPromptTemplate
from helpers.llm_integrations import get_llm
from langchain_core.output_parsers import StrOutputParser
from helpers.document_processor import DocumentProcessor
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from operator import itemgetter
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

load_dotenv()

document_processor = DocumentProcessor()

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
2. Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content. Ignore minor variations in wording or slight differences that don't impact the overall message.
3. For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
  - Inaccurate disclosure: Information that is incorrectly stated or translated
  - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
  - Outdated information: Data or statements that are no longer relevant or accurate
  - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
  - Major deviations from the English version: Any substantial differences from Document 1
4. For each flag, include:
  - A list of applicable difference types (from the list above)
  - The relevant content from both documents, including the page number
  - An explanation of the difference, highlighting the main issues
5. You can flag same sentences or paragraphs more than once.
6. When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.

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

user_prompt = """Begin your analysis now."""

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", user_prompt)]
)

model = get_llm(model="gpt-4o")

chain = prompt | model | StrOutputParser()

doc1 = document_processor.extract_filtered_content(
    "./data_sources/hlb-3-in-1-junior-savings-account-tnc-en.pdf"
)
doc2 = document_processor.extract_filtered_content(
    "./data_sources/hlb-3-in-1-junior-savings-account-tnc-bm.pdf"
)
result = chain.invoke({"doc1": doc1, "doc2": doc2})
with open("./test.txt", "w") as file:
    file.write(result)

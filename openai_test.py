from langchain_core.prompts import ChatPromptTemplate
from helpers.llm_integrations import get_llm
from langchain_core.output_parsers import StrOutputParser
from helpers.document_processor import DocumentProcessor
from openai import OpenAI
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from operator import itemgetter
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

load_dotenv()

client = OpenAI()

system_prompt = """You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

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

1. Carefully read and compare both documents in their entirety. Don't need to summarize.

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

6. If multiple discrepancies are found in one paragraph or sentence, combine them into a single flag and list all applicable flag types.

7. You have to response with an exhaustive list of differences.

8. If you don't find any major discrepancies, state that no significant differences were found.

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

user_prompt = """{input}"""

prompt = ChatPromptTemplate.from_messages([("human", user_prompt)])

model = get_llm(model="gpt-4o")


def create_recursive_chain(model, initial_prompt):
    def check_token_limit(_input, accumulated_responses: str = ""):
        response_content = _input["llm_result"].content
        response_metadata = _input["llm_result"].response_metadata
        stop_reason_keys = ["finish_reason", "stop_reason"]
        stop_reason_flags = ["length", "max_tokens"]
        stop_reason = next(map(response_metadata.get, stop_reason_keys), None)
        print("log", response_content)
        accumulated_responses += response_content
        if stop_reason not in stop_reason_flags:
            return accumulated_responses

        new_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    initial_prompt,
                ),
                ("ai", f"{response_content}"),
                ("human", "continue"),
            ]
        )
        recursive_chain = RunnablePassthrough.assign(prompt=new_prompt).assign(
            llm_result=itemgetter("prompt") | model
        )
        result = recursive_chain.invoke({})
        return check_token_limit(result, accumulated_responses)

    return check_token_limit


# chain = {"input": itemgetter("input")} | prompt | model
initial_prompt = "Give me a list of five animals."
recursive_chain = create_recursive_chain(model, initial_prompt)
chain = RunnablePassthrough.assign(prompt=prompt).assign(
    llm_result=itemgetter("prompt") | model
)

document_processor = DocumentProcessor()


# doc1 = document_processor.extract_text("./data_sources/hlb-pay-and-save-i-tnc-en.pdf")
# doc2 = document_processor.extract_text("./data_sources/hlb-pay-and-save-i-tnc-bm.pdf")
chunks = chain.stream({"input": initial_prompt})
result = ""
with open("./stream_write", "w") as file:
    file.write
for chunk in chunks:
    result += chunk
    print(chunk)

# final_result = recursive_chain(result)
# test_prompt = f"""You are a highly skilled linguistic analyst specializing in document comparison across different languages. Your task is to compare two documents in different languages and identify any major discrepancies between them.

# Here are the two documents you need to compare:

# Document 1 (considered the main reference):
# <document1>
# {doc1}
# </document1>

# Document 2:
# <document2>
# {doc2}
# </document2>

# - Look for major discrepancies between the documents. Focus on significant differences that could substantially alter the meaning or interpretation of the content. Ignore minor variations in wording or slight differences that don't impact the overall message.

# - For each major discrepancy you identify, create a "flag" entry. Consider the following types of differences:
#   - Inaccurate disclosure: Information that is incorrectly stated or translated
#   - Misleading statements or features: Content that could be misinterpreted or is presented in a potentially deceptive manner
#   - Outdated information: Data or statements that are no longer relevant or accurate
#   - Missing paragraphs or information: Significant sections or details present in one document but absent in the other
#   - Major deviations from the English version: Any substantial differences from Document 1

# - For each flag, include:
#   - A list of applicable difference types (from the list above)
#   - A brief description of the flag
#   - The relevant content from both documents, including the page number
#   - An explanation of the difference, highlighting the main issues

# - When including content in your flag, use a whole paragraph for context. Highlight the specific part of the content that contains the difference using the <span style="color: red"></span> tag.

# - If multiple discrepancies are found in one paragraph or sentence, combine them into a single flag and list all applicable flag types.

# - The process should continue until all the pages in the documents are compared.

# After your comparison, format your response as a JSON object with the following structure:

# {{
#   "flags": [
#     {{
#       "types": ["List of applicable difference types"],
#       "description": "Brief description of the flag",
#       "doc1": {{
#         "page": "Page number in Document 1 (just the number)",
#         "content": "Relevant content from Document 1 with <span style=\"color: red\">highlighted difference</span>"
#       }},
#       "doc2": {{
#         "page": "Page number in Document 2 (just the number)",
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
# """

# print(result)
# result = client.chat.completions.create(
#     model="o1", messages=[{"role": "user", "content": test_prompt}]
# )
# print(final_result)
# with open("./test.txt", "w") as file:
#     file.write(final_result)

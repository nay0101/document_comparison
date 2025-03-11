from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from helpers.llm_integrations import get_llm
from dotenv import load_dotenv

load_dotenv()

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

Before providing the final suggestions, conduct your analysis within <document_comparison_analysis> tags. In your analysis:
- List the main differences between the documents, numbering each one.
- For each difference, consider any cultural or linguistic implications.
- Brainstorm potential modifications for each difference.

After your analysis, provide your suggestions in JSON format. The JSON structure should only include suggestions for the specified target document(s). Each suggestion should include the following:
- The original text
- The suggested modification (which should be the complete updated version of the original text)
- A version number (v1, v2, etc.)

Here's an example of the expected JSON structure (do not use this content in your response, it's just for illustration):

```json
{
  "document1_suggestions": [
    {
      "version": "v1",
      "original": "Original text here",
      "modification": "Modified text here"
    },
    {
      "version": "v2",
      "original": "Original text here",
      "modification": "Another modified text"
    }
  ]
}
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

llm = get_llm("gpt-4o")

chain = prompt | llm | StrOutputParser()

document1 = """
8.2 A physical receipt will be
issued for FCY FD placement and 
withdrawal of FCY FD is NOT
allowed without the production of
the original receipt by the account
holder at any HLB branch."""

document2 = """
8.2 Pengeluaran Deposit Tetap Mata Wang Asing
sama ada sebahagian atau keseluruhan sebelum
tarikh matang hanya boleh dibuat dengan
persetujuan HLB, tertakluk kepada apa-apa
syarat yang dikenakan oleh HLB, termasuk
kehilangan faedah atas Deposit Tetap Mata
Wang Asing tersebut.
"""

explanation = """
Document 1 specifies that a physical receipt is required for the withdrawal of
FCY FD, and it is not allowed without the original receipt. This information is missing in
Document 2, which could lead to misunderstandings about the withdrawal process and
requirements.
"""

target_documents = "Document 1"

k = 1

result = chain.invoke(
    {
        "document1": document1,
        "document2": document2,
        "explanation": explanation,
        "target_documents": target_documents,
        "k": k,
    }
)

print(result)

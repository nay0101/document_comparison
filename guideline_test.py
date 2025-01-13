from helpers.document_processor import DocumentProcessor
from helpers.comparison_chain import ComparisonChain

document_processor = DocumentProcessor()

guideline = document_processor.extract_text(
    "./data_sources/pd_product transparency and disclosure_dec2024.pdf"
)

document = document_processor.extract_text("./data_sources/hlb-credit-card-pds-en.pdf")

comparison_chain = ComparisonChain()

result = comparison_chain._guideline_test(
    guideline_file=guideline, document_file=document
)

print(result)
with open("./test.txt", "w") as file:
    file.write(result)

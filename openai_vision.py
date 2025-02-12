from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import base64
import pymupdf
from helpers.document_processor import DocumentProcessor

load_dotenv()

pdf_file = "./data_sources/pd_product transparency and disclosure_dec2024.pdf"
document_processor = DocumentProcessor()
with open(pdf_file, "rb") as file:
    images = document_processor.pdf_to_image(file.read(), [45, 46, 47])

user_message = [
    {
        "type": "text",
        "text": "Describe the images",
    },
]
for image in images:
    user_message.append(
        {
            "type": "image_url",
            "image_url": {"url": image},
        },
    )
model = ChatOpenAI(model="gpt-4o")
message = HumanMessage(content=user_message)
response = model.invoke([message])
print(response.content)

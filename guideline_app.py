import streamlit as st
from streamlit import session_state as ss
from helpers.guideline_comparison import GuidelineComparisonChain
from helpers.reports import MarkdownPDFConverter
from helpers.document_processor import DocumentProcessor
from time import perf_counter
from uuid import uuid4
import os
from dotenv import load_dotenv
import json

load_dotenv()

environment = os.getenv("ENVIRONMENT")
ss.default_chat_model = "gpt-4.1"
chat_model_list = [
    "gpt-4.1",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-preview-05-20",
]
document_processor = DocumentProcessor()

if "result" not in ss:
    ss.result = None

if "chat_id" not in ss:
    ss.chat_id = uuid4()

if "chat_model" not in ss:
    ss.chat_model = ss.default_chat_model

if "formatted_guidelines" not in ss:
    ss.formatted_guidelines = None

if "clauses" not in ss:
    ss.clauses = None

if "titles" not in ss:
    ss.titles = None

if "compare_btn" in ss and ss.compare_btn:
    ss.chat_id = uuid4()

if ("guidelines" in ss and ss.guidelines is None) or ("doc" in ss and ss.doc is None):
    ss.result = None

if "guidelines" in ss and ss.guidelines is None:
    ss.formatted_guidelines = None
    ss.clauses = None
    ss.titles = None


st.header("Atenxion Guideline Compare Agent")
st.caption(f"Session ID: {ss.chat_id }")
st.divider()

st.file_uploader(
    label="Upload Central Bank Guideline Document", type=["pdf"], key="guidelines"
)
if ss.guidelines:
    if ss.formatted_guidelines is None:
        ss.formatted_guidelines = {}
        filtered_content = document_processor.extract_filtered_content(
            pdf_bytes=ss.guidelines.getvalue()
        )
        ss.formatted_guidelines["total_pages"] = filtered_content["total_pages"]
        ss.formatted_guidelines["content"] = "\n".join(
            f"<npage>{page['page']}</npage>\n{page['content']}"
            for page in filtered_content["document"]
        )

        ss.titles = document_processor.extract_titles(
            ss.formatted_guidelines["content"]
        )

st.selectbox(
    "Choose a guideline section to extract", key="section_title", options=ss.titles
)
# st.text_input("Enter section title to extract", key="section_title")
load_guidelines_btn = st.button("Load Guidelines", disabled=ss.section_title is None)

if load_guidelines_btn:
    ss.clauses = document_processor.extract_clauses(
        target_title=ss.section_title, text=ss.formatted_guidelines["content"]
    )

if "clauses" in ss and ss.clauses is not None:
    for i in range(len(ss.clauses)):
        if f"remove_clause_{i}" in ss and ss[f"remove_clause_{i}"]:
            ss.clauses.pop(i)

if ss.clauses:
    for index, clause in enumerate(ss.clauses):
        st.title(body=f"Guideline {index+1}")
        st.text_area(
            label="Guideline",
            value=clause,
            key=f"guideline_{index}",
            label_visibility="hidden",
        )
        st.multiselect(
            label="Attach page(s) as supporting element(s). (Optional)",
            key=f"attachments_{index}",
            placeholder="Choose page numbers",
            options=[i + 1 for i in range(ss.formatted_guidelines["total_pages"])],
        )
        # st.file_uploader(
        #     label="Attach additional file(s) as supporting element(s). (Optional)",
        #     key=f"external_attachment_{index}",
        #     type=["pdf"],
        #     accept_multiple_files=True,
        # )
        st.button(label="Remove Clause", type="primary", key=f"remove_clause_{index}")
        st.divider()

st.file_uploader(label="Upload a Document to be Compared", type=["pdf"], key="doc")

compare_btn = st.button(
    label="Compare",
    type="secondary",
    key="compare_btn",
    disabled=ss.clauses is None or ss.doc is None,
)

if compare_btn:
    guideline_info = []
    for i in range(len(ss.clauses)):
        image_urls = []
        clause = ss[f"guideline_{i}"]
        if ss[f"attachments_{i}"]:
            image_urls.extend(
                document_processor.pdf_to_image(
                    pdf_bytes=ss.guidelines.getvalue(),
                    page_numbers=ss[f"attachments_{i}"],
                )
            )
        # if ss[f"external_attachment_{i}"]:
        #     for attachment in ss[f"external_attachment_{i}"]:
        #         image_urls.extend(
        #             document_processor.pdf_to_image(
        #                 pdf_bytes=attachment.getvalue(),
        #             )
        #         )
        guideline_info.append({"clause": clause, "image_urls": image_urls})

    chain = GuidelineComparisonChain(chat_model_name=ss.chat_model)
    start_time = perf_counter()
    doc = ss.doc.getvalue()

    deviations = chain.invoke_chain(
        guidelines=guideline_info,
        document_file=doc,
        chat_id=f"guideline_{ss.chat_id}",
    )
    ss.result = deviations
    ss.time_taken = perf_counter() - start_time

if ss.result:
    final_result = ss.result
    with st.container():
        st.header(f"Comparison Summary")

    if len(final_result) > 0:
        with st.container():
            for deviation in final_result:
                deviation = json.loads(deviation)
                with st.container(border=True):
                    st.markdown(
                        f'<b style="font-size: 1.5rem;">{deviation["guideline"]}</b>',
                        True,
                    )
                    st.divider()
                    if len(deviation["exceptions"]) > 0:
                        for i, exception in enumerate(deviation["exceptions"]):
                            st.markdown(
                                f"<b style='font-size: 1.5rem;'>Exception {i+1}</b>",
                                True,
                            )
                            st.markdown(f"<p>{exception['description']}</p>", True)

                            st.markdown(
                                f"<b style='font-size: 1.5rem;'>Issue Items</b>", True
                            )
                            for j, issue_item in enumerate(exception["issue_items"]):
                                st.markdown(f"<p>({j+1}) {issue_item}</p>", True)
                            st.markdown(
                                f"<b style='font-size: 1.5rem;'>Recommendations For Fixes</b>",
                                True,
                            )
                            for k, fix_recommendation in enumerate(
                                exception["fix_recommendations"]
                            ):
                                st.markdown(
                                    f"<p>({k+1}) {fix_recommendation}</p>", True
                                )
                            if i != len(deviation["exceptions"]) - 1:
                                st.divider()
                    else:
                        st.markdown(
                            f"<b style='font-size: 1.5rem;'>No Exception Found.</b>",
                            True,
                        )
    report_generator = MarkdownPDFConverter()

    report = report_generator.generate_guideline_report(
        chat_model_name=ss.chat_model,
        chat_id=f"guideline_{ss.chat_id}",
        result=ss.result,
        time_taken=ss.time_taken,
        document_name=ss.doc.name,
    )
    st.download_button(
        "Download Report",
        data=report,
        file_name=f"report.pdf",
        mime="application/pdf",
    )

with st.sidebar:
    st.selectbox(
        label="Models",
        options=chat_model_list,
        index=chat_model_list.index(ss.default_chat_model),
        key="chat_model",
    )

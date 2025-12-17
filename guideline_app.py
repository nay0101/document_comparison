import streamlit as st
from streamlit import session_state as ss
from helpers.guideline_comparison import GuidelineComparisonChain
from helpers.models import FinalComparisonResult
from helpers.reports import MarkdownPDFConverter
from helpers.document_processor import DocumentProcessor
from time import perf_counter
from uuid import uuid4
import os
from dotenv import load_dotenv
import json
from documentParseJson.md_extractor import extract_layout
import shutil
from pathlib import Path
import pandas as pd
import time

load_dotenv()

environment = os.getenv("ENVIRONMENT")
ss.default_chat_model = "gpt-5"
chat_model_list = [
    "gpt-5",
    # "gemini-2.5-pro-preview-05-06",
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

if "formatted_document" not in ss:
    ss.formatted_document = None

if "clauses" not in ss:
    ss.clauses = None

if "titles" not in ss:
    ss.titles = []

if "compare_btn" in ss and ss.compare_btn:
    ss.chat_id = uuid4()

if ("guidelines" in ss and ss.guidelines is None) or ("doc" in ss and ss.doc is None):
    ss.result = None

if "guidelines" in ss and ss.guidelines is None:
    ss.formatted_guidelines = None
    ss.clauses = None
    ss.titles = []

if "doc" in ss and ss.doc is None:
    ss.formatted_document = None

if "sections" not in ss:
    ss.sections = None

if "time_taken" not in ss:
    ss.time_taken = None

if "guideline_info" not in ss:
    ss.guideline_info = []

ss.out_dir = Path("./guideline_app").resolve()
ss.compared_doc_dir = Path("./compared_doc").resolve()

output_file = f"{ss.out_dir}/sections.json"

# with open(output_file, "r") as f:
#     ss.sections = json.loads(f.read())
#     ss.titles = [section["header"] for section in ss.sections]

st.header("Atenxion Guideline Compare Agent")
st.caption(f"Session ID: {ss.chat_id }")

# Custom CSS for pills
st.markdown(
    """
<style>
.attachment-pill {
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 12px;
    margin: 2px 4px 2px 0;
    display: inline-block;
    border: 1px solid #bbdefb;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

.attachment-pill:hover {
    background-color: #bbdefb;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.attachment-pill-used {
    background-color: #e8f5e8;
    color: #2e7d32;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    margin: 2px 4px 2px 0;
    display: inline-block;
    border: 1px solid #c8e6c9;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
</style>
""",
    unsafe_allow_html=True,
)

st.divider()

st.file_uploader(
    label="Upload Central Bank Guideline Document", type=["pdf"], key="guidelines"
)

if ss.formatted_guidelines is None and ss.guidelines:
    try:
        shutil.rmtree(ss.out_dir)
    except FileNotFoundError:
        print("No existing directories to remove")
    ss.formatted_guidelines = True

    # Create progress placeholders
    progress_bar = st.progress(0.0)

    def update_progress(progress):
        progress_bar.progress(progress)

    extract_layout(
        pdf=ss.guidelines.getvalue(),
        reasoning="minimal",
        verbosity="medium",
        model="gpt-5-mini",
        outdir=ss.out_dir,
        max_workers=8,
        mode="image",
        progress_callback=update_progress,
    )

    # Clear progress indicators
    progress_bar.empty()

    with open(output_file, "r") as f:
        ss.sections = json.loads(f.read())
        ss.titles = [section["header"] for section in ss.sections]

st.multiselect(
    "Choose guideline section(s) to compare", key="section_title", options=ss.titles
)

if ss.sections:
    ss.clauses = [data for data in ss.sections if data["header"] in ss.section_title]

if ss.clauses:
    for index, data in enumerate(ss.clauses):
        ss[f"section_images_{index}"] = data["images"]
        st.title(body=f"{data['header']}")
        ss[f"title_{index}"] = data["header"]
        st.text_area(
            label="Guideline",
            value=data["content_md"],
            key=f"section_{index}",
            label_visibility="hidden",
            height=300,
        )
        st.multiselect(
            "Select Attachments (if any)",
            key=f"attachments_{index}",
            options=ss.titles,
        )
        ss[f"attachment_data_{index}"] = [
            item for item in ss.sections if item["header"] in ss[f"attachments_{index}"]
        ]

        if ss[f"attachment_data_{index}"]:
            for att_index, attachment in enumerate(ss[f"attachment_data_{index}"]):
                ss[f"attachment_images_{index}_{att_index}"] = attachment["images"]
                ss[f"attachment_{index}_{att_index}"] = attachment["content_md"]

st.file_uploader(label="Upload a Document to be Compared", type=["pdf"], key="doc")


if ss.formatted_document is None and ss.doc:
    try:
        shutil.rmtree(ss.compared_doc_dir)
    except FileNotFoundError:
        print("No existing directories to remove")
    ss.formatted_document = True

    # Create progress placeholders for document processing
    doc_progress_bar = st.progress(0.0)

    def update_doc_progress(progress):
        doc_progress_bar.progress(progress)

    extract_layout(
        pdf=ss.doc.getvalue(),
        reasoning="minimal",
        verbosity="medium",
        model="gpt-5-mini",
        outdir=ss.compared_doc_dir,
        max_workers=8,
        mode="image",
        progress_callback=update_doc_progress,
    )

    # Clear progress indicators
    time.sleep(2)
    doc_progress_bar.empty()

compare_btn = st.button(
    label="Compare",
    type="secondary",
    key="compare_btn",
    disabled=ss.clauses is None or ss.doc is None,
)

if compare_btn:
    # Reset guideline_info for new comparison
    ss.guideline_info = []

    for i in range(len(ss.clauses)):
        images = ss[f"section_images_{i}"]
        clauses = ss[f"section_{i}"]
        title = ss[f"title_{i}"]
        attachments = []

        if ss[f"attachment_data_{i}"]:
            for j in range(len(ss[f"attachment_data_{i}"])):
                attachment_images = ss[f"attachment_images_{i}_{j}"]
                attachment_clauses = ss[f"attachment_{i}_{j}"]
                attachment_header = ss[f"attachment_data_{i}"][j]["header"]
                attachments.append(
                    {
                        "text": attachment_clauses,
                        "images": attachment_images,
                        "header": attachment_header,
                    }
                )

        ss.guideline_info.append(
            {
                "clauses": {"text": clauses, "images": images},
                "title": title,
                "attachments": attachments,
            }
        )

    chain = GuidelineComparisonChain(chat_model_name=ss.chat_model)
    start_time = perf_counter()

    with open(f"{ss.compared_doc_dir}/sections.json", "r") as f:
        doc = []
        json_sections = json.loads(f.read())
        # doc = "\n\n".join([section["content_md"] for section in json_sections])
        # doc_images = list(
        #     {img for section in json_sections for img in section.get("images", [])}
        # )
        # doc_dict = {"text": doc, "images": doc_images}
        for section in json_sections:
            doc.append(
                {
                    "text": section["content_md"],
                    "images": section.get("images", []),
                }
            )

    result = chain.invoke_chain(
        guidelines=ss.guideline_info,
        documents=doc,
        chat_id=f"guideline_{ss.chat_id}",
    )
    ss.result = result
    ss.time_taken = perf_counter() - start_time

if ss.result:
    final_result = ss.result
    with st.container():
        st.header(f"Comparison Details")
    # st.json(final_result, expanded=True)

    if len(final_result) > 0:
        report_generator = MarkdownPDFConverter()

        report = report_generator.generate_guideline_report(
            chat_model_name=ss.chat_model,
            chat_id=f"guideline_{ss.chat_id}",
            result=ss.result,
            time_taken=ss.time_taken,
            document_name=ss.doc.name if "doc" in ss and ss.doc is not None else None,
            guideline_info=ss.guideline_info,
        )
        st.download_button(
            "Download Report",
            data=report,
            file_name=f"report.pdf",
            mime="application/pdf",
        )
        st.divider()

        with st.container():
            for result in final_result:
                st.markdown(
                    f"<b style='font-size: 1.5rem;'>{result.section}</b>",
                    unsafe_allow_html=True,
                )

                # Display attachments used for this section as pills
                section_attachments = []
                for guideline in ss.guideline_info:
                    if guideline["title"] == result.section and guideline.get(
                        "attachments"
                    ):
                        section_attachments = guideline["attachments"]
                        break

                if section_attachments:
                    st.markdown("**Attachments Used:**")
                    # Create pills for attachments
                    attachment_pills = ""
                    for attachment in section_attachments:
                        attachment_header = attachment.get(
                            "header", "Unknown Attachment"
                        )
                        attachment_pills += f'<span class="attachment-pill">📎 {attachment_header}</span>'
                    st.markdown(attachment_pills, unsafe_allow_html=True)
                    st.markdown("")  # Add spacing

                for comparison in result.comparisons:
                    with st.container(border=True):
                        st.markdown(
                            f'<b style="font-size: 1.5rem;">{comparison.clause}</b>',
                            True,
                        )
                        st.divider()

                        for clause_result in comparison.results:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(
                                    "<b style='font-size: 1.2rem;'>Document Excerpt:</b>",
                                    True,
                                )
                                st.markdown(
                                    f"<p>{clause_result.snippet}</p>",
                                    True,
                                )

                            with col2:
                                st.markdown(
                                    "<b style='font-size: 1.2rem;'>Analysis:</b>", True
                                )
                                match clause_result.isComplied:
                                    case "complied":
                                        st.success("Complied", icon="✅")
                                    case "non-complied":
                                        st.error("Not Complied", icon="❌")
                                    case _:
                                        st.warning("Not Applicable", icon="⚠️")
                                st.markdown(
                                    f'<p style="font-size: 1rem;">{clause_result.reason}</p>',
                                    True,
                                )
                                if clause_result.suggestions:
                                    st.markdown("**Suggestions:**")
                                    for suggestion in clause_result.suggestions:
                                        st.markdown(f"- {suggestion}")
                            st.divider()


with st.sidebar:
    st.selectbox(
        label="Models",
        options=chat_model_list,
        index=chat_model_list.index(ss.default_chat_model),
        key="chat_model",
    )

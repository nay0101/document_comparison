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
from documentParseJson.md_extractor import extract_layout
import shutil
from pathlib import Path
import pandas as pd

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
ss.result = [
    {
        "results": [
            {
                "clause": "S 16.1 A FSP shall provide a PDS (following the order and sequence of items as specified in the PDS templates provided in the Schedules) for financial consumers to make product comparisons and informed decisions. The FSP shall comply with the “Notes on PDS requirements” provided in the PDS templates.",
                "isComplied": "non-complied",
                "reason": "Document’s order and content deviate from Appendix II template: lacks opening consumer guidance text and clear numbered sections matching 1–4; includes extra sections (historical SBR, packages, repayment methods); fees/charges are only via website QR link, not disclosed inline; template Notes N1–N4 not fully followed (e.g., RM350k/35y illustration not provided).",
            },
            {
                "clause": "G 16.2 For the avoidance of doubt, a FSP may use appropriate infographics, illustrations or colours to draw the attention of financial consumers to important terms in the PDS.",
                "isComplied": "complied",
                "reason": "Document uses boxes, charts, QR code and highlighted notes to draw attention to terms.",
            },
            {
                "clause": "G 16.3 A FSP is encouraged to provide a PDS containing relevant product information that is tailored to the needs of financial consumers at the pre-contractual stage to facilitate consumers in making informed financial choices.",
                "isComplied": "complied",
                "reason": "Document provides product-specific details (facility types, rates, tenure, obligations, scenarios) intended for pre-contract stage.",
            },
            {
                "clause": "S 16.4 A FSP shall ensure the PDS does not exceed two A4 pages and ensure that the information is presented in an easily readable font size.",
                "isComplied": "non-complied",
                "reason": "Provided PDS spans 7 pages (page numbers and content).",
            },
            {
                "clause": "S 16.5 A FSP shall use plain language and active verbs to make the PDS easy to read and understand.",
                "isComplied": "non-complied",
                "reason": "Contains lengthy, technical sentences and legalistic terms (e.g., tiered amended prescribed rates, detailed OD excess interest clauses), reducing plain-language readability.",
            },
            {
                "clause": "G 16.6 In relation to paragraph 16.5, keeping sentences short will make the PDS easier to read. Most plain language writing guides recommend an average sentence length of not more than twenty words per sentence.",
                "isComplied": "non-complied",
                "reason": "Many sentences exceed twenty words, especially in sections 8–10; not aligned with guidance.",
            },
            {
                "clause": "S 16.7 A FSP shall ensure the PDS is clearly distinguishable from other marketing materials to enable financial consumers to refer to the PDS for comparison and decision-making.",
                "isComplied": "complied",
                "reason": "Document is titled “PRODUCT DISCLOSURE SHEET”, includes structured sections and version/date; distinguishable from marketing flyers.",
            },
            {
                "clause": "S 16.8 A FSP shall put in place adequate measures to ensure financial consumers are guided to read and understand the PDS prior to entering into a contract. The extent to which the FSP implements these measures shall be commensurate with the complexity of the financial product (i.e. adopting a risk-based approach). The level of measures that must be put in place by FSPs for more complex products would be higher as compared to less complex products. For complex products, the FSP must take additional steps, such as calling customers post-sales, to confirm that the customers are aware of all key terms and risks of the product.",
                "isComplied": "not-applicable",
                "reason": "Document content alone cannot evidence organisational measures (e.g., guidance processes or post-sales calls).",
            },
            {
                "clause": "G 16.9 In complying with paragraph 16.8, a FSP may require its front-line sales staff and intermediaries to advise financial consumers to read the PDS and explain the key information in the PDS, such as their obligations and product risks.",
                "isComplied": "not-applicable",
                "reason": "Operational practices of staff/intermediaries are not evidenced within the document.",
            },
            {
                "clause": "S 16.10 A FSP shall provide a copy of the PDS to financial consumers at the pre-contractual stage.",
                "isComplied": "not-applicable",
                "reason": "Whether and when the PDS is provided cannot be determined from the document text alone.",
            },
            {
                "clause": "S 16.11 If it is not practical to provide the PDS at the pre-contractual stage, particularly for telemarketing transactions, a FSP shall direct financial consumers to its website to view, read or obtain a copy of the PDS.",
                "isComplied": "not-applicable",
                "reason": "No evidence of telemarketing or alternative provision context in the document.",
            },
            {
                "clause": "S 16.12 A FSP that distributes its financial products through intermediaries, including a digital channel, shall customise the information contained in the PDS according to the distribution channel. The FSP shall disclose specific charges to be borne by financial consumers for securing the sale through its intermediaries, such as the platform, processing or administrative fees, if any.",
                "isComplied": "not-applicable",
                "reason": "Document does not indicate intermediary/digital platform distribution or disclose intermediary-specific charges.",
            },
            {
                "clause": "S 16.13 For riders to an insurance/takaful product offering a variety of benefits, a FSP must provide a separate PDS for such riders. The FSP must provide the PDS for the riders together with the PDS for the basic insurance or takaful product.",
                "isComplied": "not-applicable",
                "reason": "Document relates to housing loan/home financing, not insurance/takaful riders.",
            },
            {
                "clause": "S 16.14 For financial products that are not set out in the Schedules, a FSP shall be guided by the format provided in the Schedules in producing a PDS on such products.",
                "isComplied": "not-applicable",
                "reason": "Product is housing loan/home financing, which is set out in the Schedules (Appendix II template provided).",
            },
            {
                "clause": "S 16.15 A FSP offering an Islamic financial product must explain the applicable Shariah contract, including the key terms and conditions in the PDS.",
                "isComplied": "not-applicable",
                "reason": "Document is for conventional loans; no evidence of Islamic product disclosure requiring Shariah contract explanation.",
            },
            {
                "clause": "G 16.16 BNM reserves the right to require a FSP to make appropriate amendments to a PDS if information contained in the PDS is found to be inaccurate, incomplete or misleading.",
                "isComplied": "not-applicable",
                "reason": "This is a regulator reservation; compliance cannot be evidenced within the PDS document.",
            },
            {
                "clause": "S 16.17 A FSP shall immediately make appropriate amendments to the information contained in the PDS upon being informed by BNM in writing that the PDS is inaccurate or misleading.",
                "isComplied": "not-applicable",
                "reason": "Action depends on future BNM notification; not assessable from the document.",
            },
        ],
        "summary": {
            "complied": ["G 16.2", "G 16.3", "S 16.7"],
            "nonComplied": ["S 16.1", "S 16.4", "S 16.5", "G 16.6"],
            "notApplicable": [
                "S 16.8",
                "G 16.9",
                "S 16.10",
                "S 16.11",
                "S 16.12",
                "S 16.13",
                "S 16.14",
                "S 16.15",
                "G 16.16",
                "S 16.17",
            ],
        },
        "title": "16 Product Disclosure Sheet (PDS)",
    }
]

output_file = f"{ss.out_dir}/sections.json"

with open(output_file, "r") as f:
    ss.sections = json.loads(f.read())
    ss.titles = [section["header"] for section in ss.sections]

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

    # filtered_content = document_processor.extract_filtered_content(
    #     pdf_bytes=ss.guidelines.getvalue()
    # )
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
    output_file = f"{ss.out_dir}/sections.json"

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
        json_sections = json.loads(f.read())
        doc = "\n\n".join([section["content_md"] for section in json_sections])
        doc_images = list(
            {img for section in json_sections for img in section.get("images", [])}
        )
        doc_dict = {"text": doc, "images": doc_images}

    deviations = chain.invoke_chain(
        guidelines=ss.guideline_info,
        document_file=doc_dict,
        chat_id=f"guideline_{ss.chat_id}",
    )
    ss.result = deviations
    ss.time_taken = perf_counter() - start_time

if ss.result:
    final_result = ss.result
    with st.container():
        st.header(f"Comparison Summary")

    if len(final_result) > 0:
        for result in final_result:
            summary = result["summary"]
            table_data = [
                [
                    "**Complied**",
                    ", ".join(summary["complied"]) if summary["complied"] else "N/A",
                ],
                [
                    "**Not Complied**",
                    (
                        ", ".join(summary["nonComplied"])
                        if summary["nonComplied"]
                        else "N/A"
                    ),
                ],
                [
                    "**Not Applicable**",
                    (
                        ", ".join(summary["notApplicable"])
                        if summary["notApplicable"]
                        else "N/A"
                    ),
                ],
            ]  # Prepare data for the table

            # Create DataFrame
            st.markdown(
                f"<b style='font-size: 1rem;'>Summary for {result['title']}</b>",
                unsafe_allow_html=True,
            )
            df = pd.DataFrame(table_data, columns=["Status", "Clauses"])

            # Display as Markdown table (so bold works)
            st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)
            st.markdown("")

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
            st.header(f"Comparison Details")
            st.markdown("")

            for deviations in final_result:
                st.markdown(
                    f"<b style='font-size: 1.5rem;'>{deviations['title']}</b>",
                    unsafe_allow_html=True,
                )

                # Display attachments used for this section as pills
                section_attachments = []
                for guideline in ss.guideline_info:
                    if guideline["title"] == deviations["title"] and guideline.get(
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

                for deviation in deviations["results"]:
                    with st.container(border=True):
                        st.markdown(
                            f'<b style="font-size: 1.5rem;">{deviation["clause"]}</b>',
                            True,
                        )

                        match deviation["isComplied"]:
                            case "complied":
                                st.success("Complied", icon="✅")
                            case "non-complied":
                                st.error("Not Complied", icon="❌")
                            case _:
                                st.warning("Not Applicable", icon="⚠️")
                        st.markdown(
                            f'<p style="font-size: 1rem;">{deviation["reason"]}</p>',
                            True,
                        )
                st.divider()


with st.sidebar:
    st.selectbox(
        label="Models",
        options=chat_model_list,
        index=chat_model_list.index(ss.default_chat_model),
        key="chat_model",
    )

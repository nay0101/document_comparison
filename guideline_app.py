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
    ss.titles = None

if "compare_btn" in ss and ss.compare_btn:
    ss.chat_id = uuid4()

if ("guidelines" in ss and ss.guidelines is None) or ("doc" in ss and ss.doc is None):
    ss.result = None

if "guidelines" in ss and ss.guidelines is None:
    ss.formatted_guidelines = None
    ss.clauses = None
    ss.titles = None

if "doc" in ss and ss.doc is None:
    ss.formatted_document = None

if "sections" not in ss:
    ss.sections = None

if "time_taken" not in ss:
    ss.time_taken = None

ss.out_dir = Path("./guideline_app").resolve()
ss.compared_doc_dir = Path("./compared_doc").resolve()
ss.result = [
    {
        "results": [
            {
                "clause": 'S 16.1 A FSP shall provide a PDS (following the order and sequence of items as specified in the PDS templates provided in the Schedules) for financial consumers to make product comparisons and informed decisions. The FSP shall comply with the "Notes on PDS requirements" provided in the PDS templates.',
                "isComplied": "not-applicable",
                "reason": "Verification against the prescribed Schedules/templates and Notes is not possible as the Schedules are not provided. Sequence compliance cannot be confirmed.",
            },
            {
                "clause": "G 16.2 For the avoidance of doubt, a FSP may use appropriate infographics, illustrations or colours to draw the attention of financial consumers to important terms in the PDS.",
                "isComplied": "complied",
                "reason": "Document includes charts/figures and boxed notice; use of visuals/formatting aligns with guidance.",
            },
            {
                "clause": "G 16.3 A FSP is encouraged to provide a PDS containing relevant product information that is tailored to the needs of financial consumers at the pre-contractual stage to facilitate consumers in making informed financial choices.",
                "isComplied": "complied",
                "reason": "PDS contains tailored loan information (rates, obligations, scenarios, assistance/redress) and is labeled as pre-contractual.",
            },
            {
                "clause": "S 16.4 A FSP shall ensure the PDS does not exceed two A4 pages and ensure that the information is presented in an easily readable font size.",
                "isComplied": "non-complied",
                "reason": "The provided PDS spans multiple sections with page markers (e.g., “MG PDS ver1 Feb 2025” and “6”) and far exceeds two A4 pages.",
            },
            {
                "clause": "S 16.5 A FSP shall use plain language and active verbs to make the PDS easy to read and understand.",
                "isComplied": "non-complied",
                "reason": "Numerous long, complex sentences and legalistic phrasing (e.g., default rate tiers, lengthy conditions) reduce plain-language readability.",
            },
            {
                "clause": "G 16.6 In relation to paragraph 16.5, keeping sentences short will make the PDS easier to read. Most plain language writing guides recommend an average sentence length of not more than twenty words per sentence.",
                "isComplied": "non-complied",
                "reason": "Many sentences substantially exceed 20 words (e.g., default/penalty rate paragraphs), not aligning with the guidance.",
            },
            {
                "clause": "S 16.7 A FSP shall ensure the PDS is clearly distinguishable from other marketing materials to enable financial consumers to refer to the PDS for comparison and decision-making.",
                "isComplied": "complied",
                "reason": "Document is titled “PRODUCT DISCLOSURE SHEET,” includes formal sections and compliance notices, distinguishing it from marketing material.",
            },
            {
                "clause": "S 16.8 A FSP shall put in place adequate measures to ensure financial consumers are guided to read and understand the PDS prior to entering into a contract. The extent to which the FSP implements these measures shall be commensurate with the complexity of the financial product (i.e. adopting a risk-based approach). The level of measures that must be put in place by FSPs for more complex products would be higher as compared to less complex products. For complex products, the FSP must take additional steps, such as calling customers post-sales, to confirm that the customers are aware of all key terms and risks of the product.",
                "isComplied": "non-complied",
                "reason": "The PDS does not evidence measures guiding consumers to read/understand it (e.g., processes, confirmations, post-sales calls). Only content is provided.",
            },
            {
                "clause": "G 16.9 In complying with paragraph 16.8, a FSP may require its front-line sales staff and intermediaries to advise financial consumers to read the PDS and explain the key information in the PDS, such as their obligations and product risks.",
                "isComplied": "not-applicable",
                "reason": "The document does not describe sales staff/intermediary practices; no evidence to assess alignment with this guidance.",
            },
            {
                "clause": "S 16.10 A FSP shall provide a copy of the PDS to financial consumers at the pre-contractual stage.",
                "isComplied": "not-applicable",
                "reason": "Distribution timing is not evidenced in the document; cannot confirm provision at pre-contractual stage.",
            },
            {
                "clause": "S 16.11 If it is not practical to provide the PDS at the pre-contractual stage, particularly for telemarketing transactions, a FSP shall direct financial consumers to its website to view, read or obtain a copy of the PDS.",
                "isComplied": "not-applicable",
                "reason": "Telemarketing or inability to provide at pre-contract stage is not indicated; clause conditionality not evidenced.",
            },
            {
                "clause": "S 16.12 A FSP that distributes its financial products through intermediaries, including a digital channel, shall customise the information contained in the PDS according to the distribution channel. The FSP shall disclose specific charges to be borne by financial consumers for securing the sale through its intermediaries, such as the platform, processing or administrative fees, if any.",
                "isComplied": "not-applicable",
                "reason": "Use of intermediaries/digital platforms and related intermediary charges are not evidenced in the document.",
            },
            {
                "clause": "S 16.13 For riders to an insurance/takaful product offering a variety of benefits[^17], a FSP must provide a separate PDS for such riders. The FSP must provide the PDS for the riders together with the PDS for the basic insurance or takaful product.",
                "isComplied": "not-applicable",
                "reason": "The document concerns housing/property loans, not insurance/takaful riders.",
            },
            {
                "clause": "S 16.14 For financial products that are not set out in the Schedules, a FSP shall be guided by the format provided in the Schedules in producing a PDS on such products.",
                "isComplied": "not-applicable",
                "reason": "Whether these loans are covered by the Schedules cannot be determined without the Schedules; assessment not possible.",
            },
            {
                "clause": "S 16.15 A FSP offering an Islamic financial product must explain the applicable Shariah contract, including the key terms and conditions in the PDS.",
                "isComplied": "not-applicable",
                "reason": "The document is for conventional loans; no Islamic product or Shariah contract is presented.",
            },
            {
                "clause": "G 16.16 BNM reserves the right to require a FSP to make appropriate amendments to a PDS if information contained in the PDS is found to be inaccurate, incomplete or misleading.",
                "isComplied": "not-applicable",
                "reason": "This guidance states BNM’s right; the document cannot evidence acceptance or occurrence.",
            },
            {
                "clause": "S 16.17 A FSP shall immediately make appropriate amendments to the information contained in the PDS upon being informed by BNM in writing that the PDS is inaccurate or misleading.",
                "isComplied": "not-applicable",
                "reason": "No scenario or evidence of BNM notification is provided; cannot assess actual compliance.",
            },
        ],
        "summary": {
            "complied": ["G 16.2", "G 16.3", "S 16.7"],
            "nonComplied": ["S 16.4", "S 16.5", "G 16.6", "S 16.8"],
            "notApplicable": [
                "S 16.1",
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
    },
    {
        "results": [
            {
                "clause": "S 17.1 A FSP shall ensure that its intermediaries comply with the requirements under this Policy Document and take appropriate actions against any intermediary that fails to make the necessary product disclosure, including to provide the PDS to financial consumers. However, the FSP remains fully accountable for such failure by its intermediaries.",
                "isComplied": "not-applicable",
                "reason": "The provided document is a Product Disclosure Sheet template/content and does not evidence governance over intermediaries’ conduct or actions taken against them.",
            },
            {
                "clause": "S 17.2 A FSP shall conduct regular review to assess compliance with the requirements in this Policy Document as part of its internal audit, risk management or compliance processes.",
                "isComplied": "not-applicable",
                "reason": "The document contains product disclosures only; it does not evidence the FSP’s review cadence or IA/compliance processes.",
            },
            {
                "clause": "S 17.3 Senior management shall ensure that timely and appropriate actions are taken by the FSP to rectify any failure to comply or deficiencies detected in the implementation of the requirements in this Policy Document.",
                "isComplied": "not-applicable",
                "reason": "No information about senior management oversight, escalation, or remediation actions is present in the PDS.",
            },
            {
                "clause": "S 17.4 Notwithstanding paragraph 17.2, a FSP shall ensure an independent function such as its compliance, internal audit or risk management, assesses the FSP’s compliance with the requirements in this Policy Document within two years from the issuance date of this Policy Document.",
                "isComplied": "not-applicable",
                "reason": "The PDS does not provide evidence of an independent assessment timeline or function.",
            },
            {
                "clause": "S 17.5 A FSP must ensure that any non-compliance with the requirements in this Policy Document is properly documented. Upon completion of the independent review under paragraph 17.4, the FSP shall report material non-compliances and its proposed remedial actions to address the relevant non-compliances to the Board.",
                "isComplied": "not-applicable",
                "reason": "The document does not include internal documentation or reporting-to-Board practices.",
            },
            {
                "clause": "S 17.6 A copy of the report presented to the Board, as well as the minutes of the Board Meeting, shall be submitted to: Pengarah, Jabatan Konsumer dan Amalan Pasaran, Bank Negara Malaysia, within ten working days upon tabling of the report to the Board.",
                "isComplied": "not-applicable",
                "reason": "Submission requirements to BNM cannot be evidenced from the PDS content.",
            },
        ],
        "summary": {
            "complied": [],
            "nonComplied": [],
            "notApplicable": [
                "S 17.1",
                "S 17.2",
                "S 17.3",
                "S 17.4",
                "S 17.5",
                "S 17.6",
            ],
        },
        "title": "17 Compliance",
    },
]

output_file = f"{ss.out_dir}/sections.json"

with open(output_file, "r") as f:
    ss.sections = json.loads(f.read())
    ss.titles = [section["header"] for section in ss.sections]

st.header("Atenxion Guideline Compare Agent")
st.caption(f"Session ID: {ss.chat_id }")
st.divider()

st.file_uploader(
    label="Upload Central Bank Guideline Document", type=["pdf"], key="guidelines"
)
if ss.formatted_guidelines is None and ss.guidelines:
    try:
        # shutil.rmtree(ss.out_dir)
        ...
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
        max_workers=4,
        mode="image",
        progress_callback=update_progress,
    )

    # Clear progress indicators
    progress_bar.empty()
    output_file = f"{ss.out_dir}/sections.json"

    with open(output_file, "r") as f:
        ss.sections = json.loads(f.read())
        ss.titles = [section["header"] for section in ss.sections]

selected_titles = st.multiselect(
    "Choose guideline section(s) to compare", key="section_title", options=ss.titles
)

ss.clauses = [data for data in ss.sections if data["header"] in selected_titles]

if ss.clauses:
    for index, data in enumerate(ss.clauses):
        st.title(body=f"{data['header']}")
        ss[f"title_{index}"] = data["header"]
        st.text_area(
            label="Guideline",
            value=data["content_md"],
            key=f"section_{index}",
            label_visibility="hidden",
            height=300,
        )

st.file_uploader(label="Upload a Document to be Compared", type=["pdf"], key="doc")

if ss.formatted_document is None and ss.doc:
    try:
        # shutil.rmtree(ss.out_dir)
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
    guideline_info = []
    for i in range(len(ss.clauses)):
        image_urls = []
        clause = ss[f"section_{i}"]
        title = ss[f"title_{i}"]
        guideline_info.append(
            {"clause": clause, "title": title, "image_urls": image_urls}
        )

    chain = GuidelineComparisonChain(chat_model_name=ss.chat_model)
    start_time = perf_counter()

    with open(f"{ss.compared_doc_dir}/sections.json", "r") as f:
        json_sections = json.loads(f.read())
        doc = "\n\n".join([section["content_md"] for section in json_sections])

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
        for result in final_result:
            summary = result[
                "summary"
            ]  # {'complied': [], 'nonComplied': ['S 16.1', 'G 16.2'], 'notApplicable': []}
            # st.json(result)
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

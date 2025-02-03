import streamlit as st
from streamlit import session_state
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
session_state.default_chat_model = "gpt-4o"
chat_model_list = ["gpt-4o", "gemini-1.5-pro"]

if "result" not in session_state:
    session_state.result = None

if "chat_id" not in session_state:
    session_state.chat_id = uuid4()

if "chat_model" not in session_state:
    session_state.chat_model = session_state.default_chat_model

if "compare_btn" in session_state and session_state.compare_btn:
    session_state.chat_id = uuid4()


st.header("Atenxion Guideline Compare Agent")
st.caption(f"Session ID: {session_state.chat_id }")
st.divider()

guidelines_example = """
Example:\n
S 16.1 A FSP shall provide a PDS (following the order and sequence of items as specified in the PDS 
templates provided in the Schedules) for financial consumers to make product comparisons and 
informed decisions. The FSP shall comply with the “Notes on PDS requirements” provided in the PDS 
templates.\n
G 16.2 For the avoidance of doubt, a FSP may use appropriate infographics, illustrations or colours to 
draw the attention of financial consumers to important terms in the PDS.
"""

st.text_area(
    label="Enter Guidelines",
    key="guidelines",
    help=guidelines_example,
)
st.file_uploader(label="Upload a Document to be Compared", type=["pdf"], key="doc")

if session_state.guidelines is None or session_state.doc is None:
    session_state.result = None

compare_btn = st.button(label="Compare", type="secondary", key="compare_btn")

if compare_btn:
    chain = GuidelineComparisonChain(chat_model_name=session_state.chat_model)
    start_time = perf_counter()
    guidelines = session_state.guidelines
    doc = session_state.doc.getvalue()

    deviations = chain.invoke_chain(
        guidelines=guidelines,
        document_file=doc,
        chat_id=f"guideline_{session_state.chat_id}",
    )
    session_state.result = deviations
    session_state.time_taken = perf_counter() - start_time

if session_state.result:
    final_result = session_state.result
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
        chat_model_name=session_state.chat_model,
        chat_id=f"guideline_{session_state.chat_id}",
        result=session_state.result,
        time_taken=session_state.time_taken,
        document_name=session_state.doc.name,
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
        index=chat_model_list.index(session_state.default_chat_model),
        key="chat_model",
    )

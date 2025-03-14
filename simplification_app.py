import streamlit as st
from streamlit import session_state
from helpers.simplification import SimplificationChain
from helpers.reports import MarkdownPDFConverter
from time import perf_counter
from uuid import uuid4
import os
from dotenv import load_dotenv

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

if "simplify_btn" in session_state and session_state.simplify_btn:
    session_state.chat_id = uuid4()

st.header("Atenxion Document Simplification Agent")
st.caption(f"Session ID: {session_state.chat_id}")
st.divider()

st.text_area("Enter paragraph you want to simplify", key="paragraph")
st.selectbox("Number of variations", key="num_variations", options=[1, 2, 3, 4, 5])

if session_state.paragraph is None:
    session_state.result = None

simplify_btn = st.button(label="Simplify", type="secondary", key="simplify_btn")

if simplify_btn:
    chain = SimplificationChain(chat_model_name=session_state.chat_model)
    start_time = perf_counter()
    result = chain.invoke_chain(
        paragraph=session_state.paragraph,
        k=session_state.num_variations,
        chat_id=f"document_{session_state.chat_id}",
    )
    session_state.result = result
    session_state.time_taken = perf_counter() - start_time

if session_state.result:
    final_result_json = session_state.result
    # with st.container():
    #     st.header(f'Discrepancies found: {len(final_result_json["flags"])}')

    if len(final_result_json) > 0:
        with st.container():
            for flag in final_result_json["simplifiedVersions"]:
                with st.container(border=True):
                    st.markdown(
                        f'<b style="font-size: 1.5rem; margin-right: 0">Variation {flag["versionNumber"]}</b>',
                        True,
                    )
                    simplifiedText = flag["simplifiedText"]
                    st.markdown(simplifiedText, True)

    report_generator = MarkdownPDFConverter()

    # report = report_generator.generate_report(
    #     chat_model_name=session_state.chat_model,
    #     chat_id=f"document_{session_state.chat_id}",
    #     result=session_state.result,
    #     time_taken=session_state.time_taken,
    #     file1_name=session_state.doc1.name,
    #     file2_name=session_state.doc2.name,
    #     correct_results=(
    #         [
    #             session_state[f"check_{i}"]
    #             for i in range(len(final_result_json["flags"]))
    #         ]
    #         if environment == "development"
    #         else None
    #     ),
    # )
    # st.download_button(
    #     "Download Report",
    #     data=report,
    #     file_name=f"report.pdf",
    #     mime="application/pdf",
    # )

with st.sidebar:
    st.selectbox(
        label="Models",
        options=chat_model_list,
        index=chat_model_list.index(session_state.default_chat_model),
        key="chat_model",
    )

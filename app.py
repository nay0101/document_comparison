import streamlit as st
from streamlit import session_state
from helpers.comparison_chain import ComparisonChain
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

st.header("Atenxion Multiligual Document Compare Agent")
st.caption(f"Session ID: {session_state.chat_id}")
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.file_uploader(label="Upload First Document", type=["pdf"], key="doc1")
with col2:
    st.file_uploader(label="Upload Second Document", type=["pdf"], key="doc2")

if session_state.doc1 is None or session_state.doc2 is None:
    session_state.result = None

compare_btn = st.button(label="Compare", type="secondary")

if compare_btn:
    chain = ComparisonChain(chat_model_name=session_state.chat_model)
    start_time = perf_counter()
    doc1 = session_state.doc1.getvalue()
    doc2 = session_state.doc2.getvalue()

    result = chain.invoke_chain(
        doc1_file_bytes=doc1,
        doc2_file_bytes=doc2,
        xml_file_path=(
            f"./chunks/{session_state.chunks_file_name}.xml"
            if os.getenv("ENVIRONMENT") == "development"
            else None
        ),
        use_existing_file=(
            session_state.use_existing_chunks_file
            if os.getenv("ENVIRONMENT") == "development"
            else False
        ),
        chat_id=session_state.chat_id,
    )
    session_state.result = result
    session_state.time_taken = perf_counter() - start_time

if session_state.result:
    final_result_json = session_state.result
    with st.container():
        st.header(f'Discrepancies found: {len(final_result_json["flags"])}')

    if len(final_result_json) > 0:
        with st.container():
            for i, flag in enumerate(final_result_json["flags"]):
                with st.container(border=True):
                    st.markdown(
                        f'<b style="font-size: 1.5rem; margin-right: 0">No. {i+1}</b>',
                        True,
                    )
                    st.markdown(
                        f'<b style="font-size: 3rem;">{", ".join(flag["types"])}</b>',
                        True,
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        doc1 = flag["doc1"]
                        st.markdown(
                            "<b style='font-size: 1.5rem;'>Document 1</b>", True
                        )
                        st.markdown(doc1["content"], True)
                    with col2:
                        doc2 = flag["doc2"]
                        st.markdown(
                            "<b style='font-size: 1.5rem;'>Document 2</b>", True
                        )
                        st.markdown(doc2["content"], True)
                    st.markdown("<b style='font-size: 1.5rem;'>Explanation</b>", True)
                    st.markdown(flag["explanation"], True)
                    if environment == "development":
                        st.checkbox(label="Correct", key=f"check_{i}")

    report_generator = MarkdownPDFConverter()

    report = report_generator.generate_report(
        chat_model_name=session_state.chat_model,
        chat_id=session_state.chat_id,
        result=session_state.result,
        time_taken=session_state.time_taken,
        file1_name=session_state.doc1.name,
        file2_name=session_state.doc2.name,
        correct_results=(
            [
                session_state[f"check_{i}"]
                for i in range(len(final_result_json["flags"]))
            ]
            if environment == "development"
            else None
        ),
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
    if environment == "development":
        st.text_input(label="Chunks File Name", key="chunks_file_name", value="test")
        st.checkbox(
            label="Use Existing Chunks File",
            key="use_existing_chunks_file",
            value=False,
        )

import streamlit as st
from streamlit import session_state
from helpers.comparison_chain import ComparisonChain
from helpers.reports import MarkdownPDFConverter
from time import perf_counter
from uuid import uuid4

st.title("Document Comparer")

session_state.default_chat_model = "gpt-4o"

chat_model_list = ["gpt-4o", "gemini-2.0-flash-exp"]


col1, col2 = st.columns(2)

if "result" not in session_state:
    session_state.result = None

if "chat_id" not in session_state:
    session_state.chat_id = uuid4()

with col1:
    st.file_uploader(label="Upload First Document", type=["pdf"], key="doc1")
with col2:
    st.file_uploader(label="Upload Second Document", type=["pdf"], key="doc2")

compare_btn = st.button(label="Compare", type="secondary")
clear_btn = st.button(label="Clear", type="primary")


if clear_btn:
    session_state.chat_id = uuid4()
    session_state.result = None

if compare_btn:
    chain = ComparisonChain(chat_model_name=session_state.chat_model)
    start_time = perf_counter()
    doc1 = session_state.doc1.getvalue()
    doc2 = session_state.doc2.getvalue()

    result = chain.invoke_chain(
        doc1_file_bytes=doc1,
        doc2_file_bytes=doc2,
        xml_file_path=f"./chunks/{session_state.chunks_file_name}.xml",
        use_existing_file=session_state.use_existing_chunks_file,
        chat_id=session_state.chat_id,
    )
    session_state.result = result
    session_state.time_taken = perf_counter() - start_time

if session_state.result:
    final_result_json = session_state.result
    with st.container(border=True):
        st.title("Summary")
        st.markdown(f'Discrepancies found: {len(final_result_json["flags"])}')

    if len(final_result_json) > 0:
        with st.container(border=True):
            st.title("Discrepancies")
            for flag in final_result_json["flags"]:
                with st.container(border=True):
                    st.title(", ".join(flag["types"]))
                    col1, col2 = st.columns(2)
                    with col1:
                        doc1 = flag["doc1"]
                        st.markdown("<b style='font-size: 25px'>Document 1</b>", True)
                        # st.markdown(f'Page: {doc1["page"]}', True)
                        st.markdown(doc1["content"], True)
                    with col2:
                        doc2 = flag["doc2"]
                        st.markdown("<b style='font-size: 25px'>Document 2</b>", True)
                        # st.markdown(f'Page: {doc2["page"]}', True)
                        st.markdown(doc2["content"], True)
                    st.markdown(flag["explanation"], True)

with st.sidebar:
    st.text(f"Chat ID: {session_state.chat_id}")
    st.selectbox(
        label="Chat Models",
        options=chat_model_list,
        index=chat_model_list.index(session_state.default_chat_model),
        key="chat_model",
    )
    st.text_input(label="Chunks File Name", key="chunks_file_name", value="test")
    st.checkbox(
        label="Use Existing Chunks File", key="use_existing_chunks_file", value=False
    )

    st.text_input(label="Report File Name", key="report_file_name", value="test")
    print_btn = st.button(label="Generate Report")
    if print_btn:
        report_generator = MarkdownPDFConverter()
        report_generator.generate_report(
            chat_model_name=session_state.chat_model,
            chat_id=session_state.chat_id,
            result=session_state.result,
            time_taken=session_state.time_taken,
            path=f"./reports/{session_state.report_file_name}.pdf",
            file1_name=session_state.doc1.name,
            file2_name=session_state.doc2.name,
        )

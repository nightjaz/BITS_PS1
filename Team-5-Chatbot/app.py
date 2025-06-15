import streamlit as st
import os
import tempfile
import google.generativeai as genai
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import get_response_synthesizer
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.query_engine import RetrieverQueryEngine
from ragas import evaluate
from ragas.metrics import context_recall, faithfulness
from datasets import Dataset

# Configure page
st.set_page_config(page_title="PDF Q&A with BM25", page_icon="", layout="wide")

# Caching to avoid recomputation
@st.cache_resource
def get_llm():
    """Create and cache the Gemini LLM instance."""
    api_key = os.getenv("GEMINI_API_KEY")
    return GoogleGenAI(model="gemini-2.5-flash-preview-05-20", temperature=0.1, api_key=api_key)

@st.cache_resource
def process_pdf(_uploaded_file):
    """Process uploaded PDF and create query engine"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(_uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        reader = SimpleDirectoryReader(input_files=[tmp_path])
        documents = reader.load_data()

        text_parser = SentenceSplitter(chunk_size=750, chunk_overlap=50)
        nodes = text_parser.get_nodes_from_documents(documents)

        bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=3)

        response_synthesizer = get_response_synthesizer(
            llm=get_llm(),
            response_mode=ResponseMode.COMPACT
        )

        query_engine = RetrieverQueryEngine(
            retriever=bm25_retriever,
            response_synthesizer=response_synthesizer
        )

        return query_engine, len(nodes)

    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None, 0

    finally:
        os.unlink(tmp_path)

# Streamlit UI App

def main():
    st.title("AI Chatbot for your documents")
    st.markdown("""
    Upload a PDF and ask questions about it. 
    This app uses BM25 retrieval and Gemini for accurate answers.
    """)

    with st.sidebar:
        st.header("Upload Document")
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

        if uploaded_file:
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            st.info(f"File size: {uploaded_file.size / 1024:.1f} KB")

    col1, col2 = st.columns([2, 1])

    with col1:
        if uploaded_file:
            with st.spinner("🔄 Processing PDF with BM25..."):
                query_engine, num_chunks = process_pdf(uploaded_file)
                if not query_engine:
                    st.stop()

                st.session_state.query_engine = query_engine
                st.success(f"Document processed into {num_chunks} chunks")

            st.subheader("Ask Questions")
            question = st.text_input(
                "Enter your question:",
                placeholder="What is this document about?",
                key="question_input"
            )

            if st.button("Ask Question", type="primary") and question:
                enhanced_prompt = f"""
                Question: {question}

                Instructions: Answer based only on the PDF. 
                If not found, say so. Provide details and cite sections where possible.
                """
                try:
                    response = st.session_state.query_engine.query(enhanced_prompt)
                    st.subheader("Answer")
                    st.markdown(response.response)

                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
        else:
            st.info("Upload a PDF to get started.")

    with col2:
        st.subheader("How it works")
        st.markdown("""
        1. **Upload** a PDF document  
        2. **Text is chunked** for indexing  
        3. **BM25** makes it searchable  
        4. **Ask questions** from the document  
        5. **Gemini** generates answers  
        """)

if __name__ == "__main__":
    main()

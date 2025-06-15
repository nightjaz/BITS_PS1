import os
import streamlit as st
import fitz  # PyMuPDF
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine

# Set Gemini API key
os.environ["GOOGLE_API_KEY"] = "API_KEY"

# Configure LLM and embeddings
llm = Gemini(model="models/gemini-1.5-pro-latest")
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# PDF to text
def extract_text_from_pdf(file):
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text

# Ingest PDF and build index
def build_query_engine(text):
    # Wrap text as a document
    doc = Document(text=text)

    # Sentence splitter for chunking
    splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)
    nodes = splitter.get_nodes_from_documents([doc])

    # Use BM25 retriever instead of embedding search
    retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=5)

    

    # Create a response synthesizer using the LLM
    response_synthesizer = get_response_synthesizer(llm=llm)

    # Combine retriever and synthesizer
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer
    )
    return query_engine


# Streamlit UI
st.set_page_config(page_title="Gemini + LlamaIndex Chatbot")
st.title("📄 Chat with Your PDF")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
query_engine = None

if uploaded_file:
    with st.spinner("Reading and indexing PDF..."):
        text = extract_text_from_pdf(uploaded_file)
        query_engine = build_query_engine(text)
    st.success("PDF processed. You can now ask questions!")

if query_engine:
    user_query = st.text_input("Ask a question about the PDF:")
    if user_query:
        with st.spinner("Generating answer..."):
            response = query_engine.query(user_query)
            st.write("### Answer:")
            st.write(response.response)

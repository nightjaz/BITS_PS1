# app.py

import streamlit as st
import google.generativeai as genai
import os
import requests
import fitz # PyMuPDF is imported as fitz
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
import time # For initial setup delay if needed

# --- Configuration Constants ---
NCERT_URL = "https://ncert.nic.in/textbook/pdf/leps101.pdf"
PDF_PATH = "ncert.pdf"
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50
SIMILARITY_TOP_K = 5
DEFAULT_QUESTION = "What was the Soviet System?"

# --- Helper Function for PDF Text Extraction ---
def extract_text_from_pdf_app(file_path):
    """Extracts text from a given PDF file path."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

# --- RAG Component Setup (Cached) ---
@st.cache_resource
def setup_rag_components():
    """
    Downloads PDF, extracts text, chunks it, and sets up the BM25 retriever.
    This function is cached to run only once.
    """
    st.info("Initializing RAG components. This may take a moment...")

    # 1. PDF Download and Extraction
    if not os.path.exists(PDF_PATH):
        st.info(f"Downloading PDF from {NCERT_URL}...")
        try:
            response = requests.get(NCERT_URL)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            with open(PDF_PATH, "wb") as f:
                f.write(response.content)
            st.success("PDF downloaded successfully.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error downloading PDF from {NCERT_URL}: {e}. Please check the URL or network connectivity.")
            return None, None # Indicate failure for both
        except Exception as e:
            st.error(f"Unexpected error during PDF download: {e}")
            return None, None

    doc_text = extract_text_from_pdf_app(PDF_PATH)
    if doc_text is None:
        return None, None # Stop if PDF text extraction failed

    # 2. Chunking
    doc = Document(text=doc_text)
    splitter = SentenceSplitter(chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents([doc])
    st.success(f"Split PDF into {len(nodes)} chunks.")

    # 3. BM25 Retriever
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=SIMILARITY_TOP_K)
    st.success("BM25 Retriever ready.")
    return bm25_retriever, nodes # Return nodes for potential debugging

# --- Gemini API Setup (Cached) ---
@st.cache_resource
def get_gemini_model():
    """
    Configures the Gemini API and returns a GenerativeModel instance.
    This function is cached to run only once.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API Key not found. Please set the 'GEMINI_API_KEY' environment variable.")
        st.info("You can set it directly in your terminal before running: `export GEMINI_API_KEY='your_key_here'`")
        st.stop() # Stop the Streamlit app if API key is missing

    try:
        genai.configure(api_key=api_key)
        available_gemini_models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                if "gemini" in m.name.lower() and "vision" not in m.name.lower():
                    available_gemini_models.append(m.name)

        priority_models = [
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        model_to_use = None
        for p_model in priority_models:
            if p_model in available_gemini_models:
                model_to_use = p_model
                break

        if model_to_use:
            st.success(f"Using Gemini model: **{model_to_use}**")
            return genai.GenerativeModel(model_to_use)
        else:
            st.error("No suitable text-only Gemini model found. Please check your API key and model access.")
            st.stop()
    except Exception as e:
        st.error(f"Error configuring Gemini API or verifying models: {e}. Please check your API key and network.")
        st.stop()

# --- Main Streamlit UI Layout ---
st.set_page_config(page_title="📚 NCERT RAG Chatbot", layout="centered")

st.title("📚 NCERT RAG Chatbot")
st.write("This chatbot answers questions about the NCERT textbook 'Politics in India Since Independence'.")

# -----------------------------------------------------
# Sidebar for Setup Information (Optional but good practice)
# -----------------------------------------------------
with st.sidebar:
    st.header("App Status")
    st.info("Ensure your `GEMINI_API_KEY` environment variable is set.")
    st.write("Current `PDF_PATH`: `ncert.pdf`")
    st.write(f"Chunk Size: `{DEFAULT_CHUNK_SIZE}`")
    st.write(f"Chunk Overlap: `{DEFAULT_CHUNK_OVERLAP}`")
    st.write(f"BM25 `similarity_top_k`: `{SIMILARITY_TOP_K}`")

    # Display a button to clear cache if needed during development
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
        st.success("Cache cleared. Rerunning app.")

# -----------------------------------------------------
# Initialize RAG and Gemini Model
# -----------------------------------------------------
bm25_retriever, all_nodes = setup_rag_components() # Get all_nodes for 'Show All Chunks'
gemini_model = get_gemini_model()

# Ensure components are ready before proceeding
if bm25_retriever is None or gemini_model is None:
    st.warning("RAG components or Gemini model failed to initialize. Please check logs above.")
    st.stop() # Stop execution if setup failed

# -----------------------------------------------------
# Main Chat Interface
# -----------------------------------------------------
st.subheader("Ask a Question")
user_question = st.text_input("Enter your question here:", DEFAULT_QUESTION)

if st.button("Get Answer", use_container_width=True):
    if user_question:
        with st.spinner("Searching and generating response..."):
            try:
                retrieved_nodes = bm25_retriever.retrieve(user_question)

                if not retrieved_nodes:
                    st.warning("I couldn't find relevant information in the document for your question. Please try rephrasing or asking something else related to the NCERT textbook.")
                else:
                    context = "\n\n".join([n.get_content() for n in retrieved_nodes])
                    prompt = f"Context:\n{context}\n\nQuestion: {user_question}\nAnswer:"

                    response = gemini_model.generate_content(prompt)
                    st.subheader("Answer:")
                    st.success(response.text)

                    # Store for "Show Retrieved Context"
                    st.session_state['last_retrieved_nodes'] = retrieved_nodes

            except Exception as e:
                st.error(f"An error occurred during response generation: {e}")
                st.write("Please check your input or try a different question. Ensure your API key is valid and has access to the selected Gemini model.")
    else:
        st.warning("Please enter a question to get an answer.")

# -----------------------------------------------------
# Debugging / Context Display Options
# -----------------------------------------------------
st.markdown("---")
st.subheader("Debugging & Context (Optional)")

if st.checkbox("Show Last Retrieved Context Chunks"):
    if 'last_retrieved_nodes' in st.session_state and st.session_state['last_retrieved_nodes']:
        st.write("Context chunks used for the last answer:")
        for i, node in enumerate(st.session_state['last_retrieved_nodes']):
            st.text_area(f"Chunk {i+1}", node.get_content(), height=200, key=f"retrieved_chunk_{i}")
    else:
        st.info("No context retrieved yet. Ask a question first.")

if st.checkbox("Show All Chunks (Warning: Can be very long!)"):
    if all_nodes:
        st.write(f"Displaying all {len(all_nodes)} chunks:")
        for i, node in enumerate(all_nodes):
            st.text_area(f"Original Chunk {i+1}", node.get_content(), height=150, key=f"all_chunk_{i}")
    else:
        st.info("Nodes not available. RAG setup might have failed.")
import streamlit as st
import google.generativeai as genai
import os
import requests, fitz  # Needed for PDF handling in app
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core.retrievers import QueryFusionRetriever
import chromadb
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini  # Import Gemini LLM
import nest_asyncio
nest_asyncio.apply()
import asyncio

db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("ncert_physics_rag")
vector_store = ChromaVectorStore(chroma_collection=collection)

ncert_url = "https://ncert.nic.in/textbook/pdf/leps101.pdf"
pdf_path = "ncert.pdf"

# Store pdf_path in session state
if "pdf_path" not in st.session_state:
    st.session_state["pdf_path"] = pdf_path

if not os.path.exists(st.session_state["pdf_path"]):
    st.write("Downloading PDF...")
    ncert_url = "https://ncert.nic.in/textbook/pdf/leps101.pdf"
    response = requests.get(ncert_url)
    with open(st.session_state["pdf_path"], "wb") as f:
        f.write(response.content)
    st.write("✅ PDF downloaded.")
else:
    st.write("✅ PDF already exists.")

Settings.llm = Gemini(
    api_key=os.getenv("GEMINI_API_KEY"),
    model_name="models/gemini-1.5-flash"
)

def extract_text_from_pdf_app(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

@st.cache_resource
def setup_rag_components():
    st.write("Initializing RAG components...")

    doc_text = ""  # Initialize here to avoid NameError
    try:
        doc_text = extract_text_from_pdf_app(pdf_path)
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None  # Return early on failure
    doc = Document(text=doc_text)
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents([doc])

    # --- BM25 Retriever (keep existing) ---
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=5)

    # --- Vector Retriever Setup (NEW) ---
    embed_model = GoogleGenAIEmbedding(
        model_name="models/embedding-001",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection("ncert_physics_rag")
    vector_store = ChromaVectorStore(collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    vector_index = VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=False
    )
    vector_retriever = vector_index.as_retriever(similarity_top_k=5)

    # --- Hybrid Retriever (NEW) ---
    fusion_retriever = QueryFusionRetriever(
        [bm25_retriever, vector_retriever],
        llm=Settings.llm,
        mode="reciprocal_rerank",
        num_queries=4,
        verbose=True
    )

    st.success("Hybrid (BM25 + Vector) Retriever ready.")
    return fusion_retriever

@st.cache_resource
def get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API Key not found. Please set GEMINI_API_KEY in Colab Secrets or as an environment variable.")
        st.stop()

    genai.configure(api_key=api_key)

    model_to_use = None
    try:
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

        for p_model in priority_models:
            if p_model in available_gemini_models:
                model_to_use = p_model
                break

        if model_to_use:
            st.success(f"Using Gemini model: {model_to_use}")
            return genai.GenerativeModel(model_to_use)
        else:
            st.error("No suitable text-only Gemini model found. Please check your API key and model access.")
            st.stop()
    except Exception as e:
        st.error(f"Error verifying Gemini model: {e}. Please check your API key.")
        st.stop()

async def main():
    st.title("📚 NCERT RAG Chatbot")
    st.write("Ask questions about the NCERT textbook.")

    if "hybrid_retriever" not in st.session_state:
        with st.spinner("Initializing RAG components..."):
            st.session_state.hybrid_retriever = setup_rag_components()

    hybrid_retriever = st.session_state.hybrid_retriever

    gemini_model = get_gemini_model()
    if gemini_model is None:
        st.stop()

    user_question = st.text_input('Your Question:', 'What was the Soviet System?')

    if st.button('Get Answer'):
        if user_question:
            with st.spinner('Searching and generating response...'):
                try:
                    retrieved_nodes = await hybrid_retriever.aretrieve(user_question)
                    if not retrieved_nodes:
                        st.warning("I don't have information on that topic. Please ask about the NCERT textbook.")
                    else:
                        context = '\n\n'.join([n.get_content() for n in retrieved_nodes])
                        prompt = f'Context:\n{context}\n\nQuestion: {user_question}\nAnswer:'
                        response = gemini_model.generate_content(prompt)
                        st.subheader('Answer:')
                        st.write(response.text)
                except Exception as e:
                    st.error(f'An error occurred during response generation: {e}')
        else:
            st.warning('Please enter a question.')

    if st.checkbox('Show Retrieved Context'):
        if user_question:
            with st.spinner('Retrieving context...'):
                try:
                    retrieved_nodes = await hybrid_retriever.aretrieve(user_question)
                    if retrieved_nodes:
                        st.subheader('Retrieved Context:')
                        for i, node in enumerate(retrieved_nodes):
                            st.text_area(f'Context Chunk {i+1}', node.get_content(), height=150)
                    else:
                        st.info('No relevant context found.')
                except Exception as e:
                    st.error(f'Context retrieval error: {e}')
        else:
            st.info('Enter a question first.')

if __name__ == '__main__':
    asyncio.run(main())

import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

# Load Google API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# LlamaIndex imports for embeddings, indexing, and querying
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import get_response_synthesizer
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine

# Initialize FastAPI app
app = FastAPI()

# Directory where uploaded PDFs will be stored
pdf_dir = "./uploaded_pdf"
os.makedirs(pdf_dir, exist_ok=True)

# Globals to hold the index and query engine instances
document_index = None
query_engine = None

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Save an uploaded PDF locally and build a searchable index
    using Google GenAI embeddings and BM25 retrieval.
    """
    # Store the incoming PDF to disk
    file_path = os.path.join(pdf_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Set up the embedding model for later use
    embed_model = GoogleGenAIEmbedding(
        model_name="models/embedding-001",
        api_key=GOOGLE_API_KEY
    )
    Settings.embed_model = embed_model

    # Read all PDFs, split into chunks, and create nodes
    docs = SimpleDirectoryReader(pdf_dir).load_data()
    splitter = SentenceSplitter(chunk_size=750, chunk_overlap=150)
    nodes = splitter.get_nodes_from_documents(docs)

    # Build or overwrite the vector store index
global document_index, query_engine
    document_index = VectorStoreIndex(nodes)

    # Configure BM25 retriever on the new index
    bm25 = BM25Retriever.from_defaults(
        index=document_index,
        similarity_top_k=3
    )

    # Initialize the LLM for answer generation
    llm = GoogleGenAI(
        model="gemini-2.0-flash",
        api_key=GOOGLE_API_KEY
    )
    Settings.llm = llm

    # Combine retriever with a compact response synthesizer
    synth = get_response_synthesizer(response_mode="compact")
    query_engine = RetrieverQueryEngine(
        retriever=bm25,
        response_synthesizer=synth
    )

    return {"message": "PDF uploaded and indexed successfully."}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    """
    Answer a user question based on the indexed PDF content.
    """
    global query_engine
    if not query_engine:
        return JSONResponse(
            status_code=400,
            content={"error": "No PDF indexed. Upload first."}
        )

    # Query the engine and return the result
    resp = query_engine.query(question)
    answer = getattr(resp, "response", str(resp))
    return {"question": question, "answer": answer}

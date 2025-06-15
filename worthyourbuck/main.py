import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import get_response_synthesizer
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine

GOOGLE_API_KEY = "AIzaSyAw7-i9vNUeavJkpDoliiegpdeVmt1MzwI"  # Replace with yours if needed

app = FastAPI()

pdf_dir = "./uploaded_pdf"
os.makedirs(pdf_dir, exist_ok=True)

index = None
query_engine = None

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(pdf_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    embed_model = GoogleGenAIEmbedding(
        model_name="models/embedding-001",
        api_key=GOOGLE_API_KEY
    )
    Settings.embed_model = embed_model

    documents = SimpleDirectoryReader(pdf_dir).load_data()
    splitter = SentenceSplitter(chunk_size=750, chunk_overlap=150)
    nodes = splitter.get_nodes_from_documents(documents)

    global index, query_engine
    index = VectorStoreIndex(nodes)

    bm25_retriever = BM25Retriever.from_defaults(index=index, similarity_top_k=3)
    llm = GoogleGenAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY)
    Settings.llm = llm

    response_synthesizer = get_response_synthesizer(response_mode="compact")
    query_engine = RetrieverQueryEngine(retriever=bm25_retriever, response_synthesizer=response_synthesizer)

    return {"message": "PDF uploaded and indexed successfully."}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    global query_engine
    if query_engine is None:
        return JSONResponse(status_code=400, content={"error": "No PDF indexed."})

    response = query_engine.query(question)
    answer = response.response if hasattr(response, "response") else str(response)
    return {"question": question, "answer": answer}


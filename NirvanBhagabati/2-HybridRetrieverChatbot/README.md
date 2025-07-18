# NCERT RAG Chatbot

A Streamlit chatbot that answers questions about NCERT textbooks using hybrid retrieval (BM25 + Vector) and Google Gemini.

---

## Features

- **Hybrid Retrieval:** Combines BM25 and vector search for accurate context retrieval
- **Gemini Integration:** Uses Google's Gemini 1.5 Flash for answer generation
- **PDF Processing:** Automatically downloads and processes NCERT PDFs
- **Context Display:** Shows retrieved text chunks for transparency

---

## Installation

1. **Install requirements:** pip install streamlit google-generativeai requests pymupdf llama-index chromadb nest-asyncio
2. **Set Gemini API key:** export GEMINI_API_KEY='your-api-key'

---

## Project Structure

- `HybridRetrieverChatbot.py` - Main application script
- `chroma_db/` - Persistent vector storage directory (auto-created)
- `ncert.pdf` - Downloaded textbook (auto-created)

---

## Usage

1. **Run the app:** streamlit run HybridRetrieverChatbot.py
2. **Ask a question:** Ask questions about the NCERT textbook content

---

## Technical Components

- **Retrieval:** Hybrid BM25 + ChromaDB vector search
- **LLM:** Google Gemini 1.5 Flash
- **Text Processing:** PyMuPDF for PDF extraction
- **Caching:** Streamlit cache for efficient RAG component initialization

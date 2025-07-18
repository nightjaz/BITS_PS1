# NCERT RAG Chatbot

A Streamlit chatbot that answers questions about the NCERT textbook "Politics in India Since Independence" using retrieval-augmented generation (RAG) with BM25 and Google Gemini.

---

## Features

- **PDF Extraction:** Downloads and extracts text from the NCERT PDF.
- **BM25 Retrieval:** Finds relevant content using the BM25 algorithm.
- **Gemini AI:** Generates answers with Google’s Gemini model.
- **Streamlit UI:** Simple web interface with sidebar for setup info and cache controls.
- **Context Display:** Shows retrieved text chunks for transparency.

---

## Installation

1. **Install dependencies:** pip install streamlit google-generativeai requests pymupdf llama-index llama-index-retrievers-bm25
2. **Set your Gemini API key:** export GEMINI_API_KEY='your-api-key-here'

---

## Usage

1. **Run the app:** streamlit run Week1CommonTask.py
2. **Ask a question:** Enter a question about the textbook and click "Get Answer."

---

## Project Structure

- `Week1CommonTask.py:` Main application script.
- `requirements.txt:` List of required packages.

import os  
import streamlit as st  
import requests  

# Backend URL where FastAPI is running (update as needed)
backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
st.sidebar.write(f"📢 Using backend: {backend_url}")  # debug info

# Page configuration
st.set_page_config(
    page_title="Gemini PDF Q&A",
    page_icon="📄",
)

# Main app header
st.title("📄 Document Q&A (Streamlit + FastAPI + Gemini)")

# --- Sidebar: Upload and index PDF ---
st.sidebar.header("1) Upload & Index PDF")
# File uploader widget (only PDFs allowed)
uploaded_file = st.sidebar.file_uploader(
    label="Choose a PDF file",
    type=["pdf"],
)

# When a file is selected, send it to FastAPI for indexing
def index_pdf(file):
    """
    Send the uploaded PDF to /upload-pdf endpoint for embedding and indexing.
    Returns the response object.
    """
    files = {"file": (file.name, file, "application/pdf")}
    return requests.post(
        f"{backend_url}/upload-pdf",
        files=files,
        timeout=120,  # allow longer for indexing
    )

if uploaded_file:
    if st.sidebar.button("Index PDF"):
        with st.sidebar.spinner("Indexing PDF..."):
            try:
                res = index_pdf(uploaded_file)
                res.raise_for_status()
                st.sidebar.success("✅ PDF indexed successfully!")
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Indexing error: {e}")

# Main area: Ask questions 
st.header("2) Ask a Question")
# Text input for user queries
query = st.text_input("Enter your question about the PDF:")

# Send query when button clicked
def ask_question(text):
    """
    Send the user's question to /ask endpoint and return JSON.
    """
    data = {"question": text}
    return requests.post(
        f"{backend_url}/ask",
        data=data,
        timeout=30,
    )

if query:
    if st.button("Get Answer"):
        with st.spinner("Fetching answer..."):
            try:
                resp = ask_question(query)
                resp.raise_for_status()
                answer = resp.json().get("answer", "(no answer)")
                st.markdown(f"**Answer:** {answer}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching answer: {e}")

# When no PDF uploaded yet, show info
if not uploaded_file:
    st.info("Upload a PDF first to start asking questions.")

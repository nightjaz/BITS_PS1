import streamlit as st
import requests

# 🔁 This will be replaced in Cell 5 automatically
backend_url = "http://localhost:8000"
print("📢 Using backend:", backend_url)  # 🧪 Debug print

st.set_page_config(page_title="Gemini PDF Q&A", page_icon="📄")
st.title("📄 Document Q&A (Streamlit + FastAPI + Gemini)")

with st.sidebar:
    st.header("Upload a PDF")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf"])
    if uploaded_file:
        res = requests.post(f"{backend_url}/upload-pdf", files={"file": uploaded_file})
        if res.ok:
            st.success("✅ PDF uploaded and indexed.")
        else:
            st.error(f"❌ Upload failed: {res.status_code} - {res.text}")

if uploaded_file:
    user_input = st.text_input("Ask a question:")
    if user_input:
        with st.spinner("Thinking..."):
            res = requests.post(f"{backend_url}/ask", data={"question": user_input})
            if res.ok:
                answer = res.json()["answer"]
                st.markdown(f"**Answer:** {answer}")
            else:
                st.error(f"❌ Failed: {res.status_code} - {res.text}")
else:
    st.info("Upload a PDF to start asking questions.")

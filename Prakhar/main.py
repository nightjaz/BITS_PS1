from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename
import os
import dotenv
dotenv.load_dotenv()

gemini_api_key = os.getenv("GOOGLE_API_KEY")

import google.generativeai as genai
genai.configure(api_key=gemini_api_key)

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import get_response_synthesizer
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.query_engine import RetrieverQueryEngine
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

HTML_FORM = """
<!doctype html>
<html lang="en">
<head><title>Upload PDF & Query</title></head>
<body>
    <h1>Upload a PDF File</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="pdf_file" accept="application/pdf" required>
        <input type="submit" value="Upload">
    </form>
    {% if filename %}
        <p>Uploaded: {{ filename }}</p>
        <hr>
        <h2>Ask a Query</h2>
        <form method="post">
            <input type="hidden" name="filename" value="{{ filename }}">
            <input type="text" name="query" placeholder="Enter your question" required>
            <input type="submit" value="Ask">
        </form>
    {% endif %}
    {% if answer %}
        <hr>
        <h3>Answer:</h3>
        <p>{{ answer }}</p>
    {% endif %}
</body>
</html>
"""

llm = GoogleGenAI(model="gemini-2.0-flash", temperature=0.1)

def process_pdf(pdf_path):
    reader = SimpleDirectoryReader(input_files=[pdf_path])
    documents = reader.load_data()
    text_parser = SentenceSplitter(chunk_size=750, chunk_overlap=50)
    nodes = text_parser.get_nodes_from_documents(documents)
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=3)
    response_synthesizer = get_response_synthesizer(
        llm=llm, response_mode=ResponseMode.COMPACT
    )
    query_engine = RetrieverQueryEngine(
        retriever=bm25_retriever, response_synthesizer=response_synthesizer
    )
    return query_engine

@app.route('/', methods=['GET', 'POST'])
def upload_pdf():
    filename = None
    answer = None

    if request.method == 'POST':
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                return render_template_string(HTML_FORM, filename=filename)
        elif request.form.get('query') and request.form.get('filename'):
            query = request.form.get('query')
            filename = request.form.get('filename')
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                query_engine = process_pdf(file_path)
                response = query_engine.query(query)
                answer = response.response
            except Exception as e:
                answer = f"Error: {e}"
            return render_template_string(HTML_FORM, filename=filename, answer=answer)

    return render_template_string(HTML_FORM, filename=filename)

if __name__ == '__main__':
    app.run(debug=True)

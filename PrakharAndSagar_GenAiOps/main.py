from flask import Flask, render_template_string, request, session
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

import markdown
from markupsafe import Markup

"""
Library Dependencies and Their Purposes:
• Flask: Web framework for building the application's interface and handling HTTP requests
• werkzeug: Provides utilities for secure file handling and web development
• os: Handles file system operations and environment variables
• dotenv: Manages environment variables and API key security
• google.generativeai: Enables integration with Google's Gemini AI model
• llama_index: Core components for document processing and retrieval:
  - SimpleDirectoryReader: Reads and processes PDF documents
  - SentenceSplitter: Breaks documents into manageable chunks
  - GoogleGenAI: Integrates with Google's AI models
  - BM25Retriever: Implements BM25 algorithm for document retrieval
  - ResponseSynthesizer: Generates coherent responses from retrieved information
• markdown: Converts markdown text to HTML for better response formatting
• markupsafe: Ensures safe HTML rendering in templates
"""

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

HTML_FORM = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Q&A</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {
                --primary: #8ab4f8;
                --primary-dark: #5c8ee6;
                --bg-dark: #181a20;
                --bg-card: #23272f;
                --text: #e0e0e0;
                --text-muted: #a0a0a0;
                --border: #333;
            }
            body { 
                font-family: 'Segoe UI', system-ui, sans-serif; 
                margin: 0; 
                background: var(--bg-dark); 
                color: var(--text);
                line-height: 1.6;
                padding-bottom: 2rem;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 0 1.5rem;
            }
            header {
                padding: 1.5rem 0;
                text-align: center;
                border-bottom: 1px solid var(--border);
                margin-bottom: 2rem;
            }
            h1, h2, h3 { 
                color: var(--primary);
                font-weight: 600;
            }
            h1 { 
                font-size: 2rem; 
                margin-bottom: 0.5rem;
            }
            h2 { font-size: 1.5rem; }
            h3 { font-size: 1.25rem; }
            
            .card {
                background: var(--bg-card);
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
            }
            
            input[type="file"] {
                width: 0.1px;
                height: 0.1px;
                opacity: 0;
                overflow: hidden;
                position: absolute;
                z-index: -1;
            }
            .file-label {
                display: inline-block;
                cursor: pointer;
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                color: #fff;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-weight: 600;
                text-align: center;
                transition: all 0.2s;
            }
            .file-label:hover {
                background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
                transform: translateY(-2px);
            }
            .file-label i {
                margin-right: 8px;
            }
            
            .input-group {
                position: relative;
                margin-bottom: 1rem;
            }
            input[type="text"] {
                width: 90%;
                padding: 1rem;
                font-size: 1rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border);
                border-radius: 8px;
                color: var(--text);
                transition: all 0.3s;
            }
            input[type="text"]:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(138, 180, 248, 0.25);
            }
            
            button, input[type="submit"] {
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            button:hover, input[type="submit"]:hover {
                background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(138, 180, 248, 0.3);
            }
            
            .chat-history {
                margin-top: 2rem;
            }
            .chat-entry {
                margin-bottom: 1.5rem;
                padding: 1.5rem;
                border-radius: 12px;
                background: rgba(35, 39, 47, 0.7);
                backdrop-filter: blur(10px);
                border-left: 4px solid var(--primary);
            }
            .chat-question {
                color: var(--primary);
                font-weight: 600;
                margin-bottom: 0.75rem;
                display: flex;
                align-items: center;
            }
            .chat-question i {
                margin-right: 10px;
                font-size: 1.2rem;
            }
            .chat-answer {
                color: var(--text);
                padding-left: 28px;
            }
            
            .file-info {
                display: flex;
                align-items: center;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            .file-info i {
                color: var(--primary);
                font-size: 1.5rem;
                margin-right: 1rem;
            }
            
            .spinner {
                display: none;
                margin: 1.5rem auto;
                width: 40px;
                height: 40px;
                border: 4px solid rgba(138, 180, 248, 0.1);
                border-left: 4px solid var(--primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .answer-container {
                padding: 1.5rem;
                background: rgba(138, 180, 248, 0.1);
                border-radius: 12px;
                margin-top: 2rem;
            }
            /* Markdown styles */
            .markdown-body {
                color: var(--text);
                font-size: 1rem;
                line-height: 1.7;
            }
            .markdown-body code {
                background: #23272f;
                color: #8ab4f8;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 0.95em;
            }
            .markdown-body pre {
                background: #23272f;
                color: #8ab4f8;
                padding: 1em;
                border-radius: 8px;
                overflow-x: auto;
            }
            .markdown-body h1, .markdown-body h2, .markdown-body h3 {
                color: var(--primary);
            }
            .markdown-body ul, .markdown-body ol {
                margin-left: 1.5em;
            }
            @media (max-width: 768px) {
                .container { padding: 0 1rem; }
                h1 { font-size: 1.75rem; }
                .card { padding: 1.25rem; }
            }
        </style>
        <script>
            function showSpinner() {
                document.getElementById('spinner').style.display = 'block';
                document.querySelector('input[type="submit"], button[type="submit"]').disabled = true;
            }
            
            function hideSpinner() {
                document.getElementById('spinner').style.display = 'none';
                document.querySelector('input[type="submit"], button[type="submit"]').disabled = false;
            }
            
            window.onload = function() {
                var form = document.getElementById('question-form');
                if (form) {
                    form.onsubmit = function() {
                        showSpinner();
                    }
                }
                
                // Display name of file selected
                var fileInput = document.querySelector('input[type="file"]');
                var fileLabel = document.querySelector('.file-name');
                
                if (fileInput && fileLabel) {
                    fileInput.addEventListener('change', function(e) {
                        if (fileInput.files.length > 0) {
                            fileLabel.textContent = fileInput.files[0].name;
                        }
                    });
                }
            }
        </script>
    </head>
    <body>
        <header>
            <div class="container">
                <h1><i class="fas fa-robot"></i> PDF Q&A Assistant</h1>
                <p>Upload a PDF and ask questions about its content</p>
            </div>
        </header>
        
        <div class="container">
            <div class="card">
                <form method="post" enctype="multipart/form-data">
                    <h2><i class="fas fa-file-pdf"></i> Upload Document</h2>
                    <div class="input-group">
                        <label for="pdf-upload" class="file-label">
                            <i class="fas fa-cloud-upload-alt"></i> Choose PDF File
                        </label>
                        <input id="pdf-upload" type="file" name="pdf_file" accept="application/pdf" required>
                        <p class="file-name"></p>
                    </div>
                    <button type="submit"><i class="fas fa-upload"></i> Upload PDF</button>
                </form>
            </div>

            {% if filename %}
                <div class="file-info">
                    <i class="fas fa-file-pdf"></i>
                    <strong>{{ filename }}</strong>
                </div>
                
                <div class="card">
                    <h2><i class="fas fa-question-circle"></i> Ask a Question</h2>
                    <form method="post" id="question-form">
                        <input type="hidden" name="filename" value="{{ filename }}">
                        <div class="input-group">
                            <input type="text" name="query" placeholder="What would you like to know about this document?" required autocomplete="off">
                        </div>
                        <button type="submit"><i class="fas fa-paper-plane"></i> Ask Question</button>
                    </form>
                    <div id="spinner" class="spinner"></div>
                </div>

                {% if chat_history and chat_history|length > 0 %}
                    {% set last_chat = chat_history[-1] %}
                    <div class="card answer-container markdown-body" style="margin-top: 0;">
                        <h3><i class="fas fa-comment-dots"></i> Latest Answer:</h3>
                        <div class="chat-question">
                            <i class="fas fa-user"></i> {{ last_chat.question }}
                        </div>
                        <div class="chat-answer">
                            <i class="fas fa-robot"></i> {{ last_chat.answer|safe }}
                        </div>
                    </div>
                {% endif %}
            {% endif %}

            {% if chat_history %}
                <div class="chat-history">
                    <h2><i class="fas fa-history"></i> Conversation History</h2>
                    {% for chat in chat_history %}
                        <div class="chat-entry">
                            <div class="chat-question">
                                <i class="fas fa-user"></i> {{ chat.question }}
                            </div>
                            <div class="chat-answer markdown-body">
                                <i class="fas fa-robot"></i> {{ chat.answer|safe }}
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}

            {% if answer and not chat_history %}
                <div class="answer-container markdown-body">
                    <h3><i class="fas fa-comment-dots"></i> Answer:</h3>
                    <p>{{ answer|safe }}</p>
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """

# No prompt injection
llm = GoogleGenAI(
    model="gemini-2.0-flash",
    temperature=0.1
)

def markdown_to_html(md_text):
    """
    Converts markdown text to HTML with proper safety measures.
    
    Args:
        md_text (str): The markdown text to be converted
        
    Returns:
        Markup: A safe HTML string that can be rendered in templates
        
    How it works:
    - Uses the markdown library to convert markdown syntax to HTML
    - Enables 'fenced_code' and 'tables' extensions for better formatting
    - Wraps the output in Markup to mark it as safe for Jinja templates
    """
    return Markup(markdown.markdown(md_text, extensions=['fenced_code', 'tables']))

def process_pdf(pdf_path):
    """
    Processes a PDF file and creates a query engine for document-based question answering.
    
    Args:
        pdf_path (str): Path to the PDF file to be processed
        
    Returns:
        RetrieverQueryEngine: A configured query engine ready to answer questions
        
    How it works:
    1. Uses SimpleDirectoryReader to load the PDF document
    2. Splits the document into smaller chunks using SentenceSplitter
    3. Creates a BM25Retriever for efficient document retrieval
    4. Configures a response synthesizer with the Gemini model
    5. Combines retriever and synthesizer into a query engine
    """
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
def upload_and_query_pdf():
    """
    Main route handler for the PDF Q&A application.
    
    GET Method:
    - Retrieves the current session state
    - Displays the upload form if no file is uploaded
    - Shows the question form and chat history if a file exists
    
    POST Method:
    Handles two types of POST requests:
    1. PDF Upload:
       - Validates the uploaded file is a PDF
       - Securely saves the file
       - Resets chat history
       - Returns the question form interface
    
    2. Question Query:
       - Processes the user's question about the PDF
       - Uses the query engine to find relevant information
       - Formats the response in markdown
       - Updates chat history
       - Returns the answer with updated interface
    
    Session Management:
    - Maintains chat history across requests
    - Stores the current filename
    - Handles error cases gracefully
    
    Returns:
        str: Rendered HTML template with appropriate content
    """
    filename = None
    answer = None
    chat_history = session.get('chat_history', [])

    if request.method == 'POST':
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                session['filename'] = filename
                session['chat_history'] = []
                chat_history = []
                return render_template_string(HTML_FORM, filename=filename, chat_history=chat_history)
            else:
                answer = markdown_to_html("**Please upload a valid PDF file.**")
                return render_template_string(HTML_FORM, filename=None, answer=answer, chat_history=chat_history)

        elif request.form.get('query') and request.form.get('filename'):
            query_text = request.form.get('query')
            PROMPT_INJECTION = "You are a helpful assistant. \n Answer using information from the provided PDF document. If the answer is clearly not present in the PDF, reply with 'I don't know based on the PDF. Do not use external knowledge or assumptions. Format your answers using proper Markdown."
            query_text2 = query_text+"\n\n" + PROMPT_INJECTION

            filename = request.form.get('filename')
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(file_path):
                answer = markdown_to_html(f"**Error:** File `{filename}` not found. Try re-uploading?")
                return render_template_string(HTML_FORM, filename=filename, answer=answer, chat_history=chat_history)
            try:
                query_engine = process_pdf(file_path)
                response = query_engine.query(query_text2)
                md_answer = response.response
                html_answer = markdown_to_html(md_answer)
                chat_history.append({'question': query_text, 'answer': html_answer})
                session['chat_history'] = chat_history
                answer = html_answer
            except Exception as e:
                answer = markdown_to_html(f"**Oops! Something went wrong:** `{e}`. Maybe try a different query or PDF?")
            return render_template_string(HTML_FORM, filename=filename, answer=answer, chat_history=chat_history)
    else:
        filename = session.get('filename')
        chat_history = session.get('chat_history', [])

    return render_template_string(HTML_FORM, filename=filename, answer=answer, chat_history=chat_history)

if __name__ == '__main__':    
    print("Starting Flask app on http://127.0.0.1:5000")
    app.run(debug=True)

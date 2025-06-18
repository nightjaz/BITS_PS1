# PDF Q&A Assistant with Gemini AI

A powerful web application that allows users to upload PDF documents and ask questions about their content using Google's Gemini AI model. The application uses advanced document processing and retrieval techniques to provide accurate and context-aware answers.

## Demo

![PDF Q&A Assistant Interface](image.png)

### Watch the Demo Video
[Click here to watch the demo video](demo.mp4)

*The demo shows the complete workflow of uploading a PDF and asking questions about its content*

## Features

- PDF Document Upload
- AI-Powered Question Answering
- Interactive Chat Interface
- Markdown Support for Rich Text Formatting
- Smart Document Retrieval using BM25 Algorithm
- Session-based Chat History
- Modern, Responsive UI

## Technical Stack

- **Backend**: Flask (Python)
- **AI Model**: Google Gemini 2.0 Flash
- **Document Processing**: LlamaIndex
- **Text Retrieval**: BM25 Algorithm
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with modern design principles

## How It Works

1. **Document Processing**
   - PDF is uploaded and processed using LlamaIndex
   - Document is split into manageable chunks
   - BM25 algorithm indexes the content for efficient retrieval

2. **Question Answering**
   - User submits a question
   - System retrieves relevant document chunks
   - Gemini AI generates a context-aware response
   - Response is formatted in Markdown and displayed

3. **Chat History**
   - Conversations are maintained in session
   - Previous Q&A pairs are displayed
   - Context is preserved throughout the session
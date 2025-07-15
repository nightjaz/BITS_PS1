# PDF Q&A Assistant with Gemini AI

A powerful web application that allows users to upload PDF documents and ask questions about their content using Google's Gemini AI model. The application uses advanced document processing and retrieval techniques to provide accurate and context-aware answers.

## Demo

![PDF Q&A Assistant Interface](image.png)

### Watch the Demo Video
<video width="100%" controls>
  <source src="demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

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

## Technical Concepts Explained

### RAG (Retrieval-Augmented Generation)
RAG is an advanced AI architecture that combines retrieval-based and generative approaches. It works by:
- First retrieving relevant information from a knowledge base
- Then using that information to generate more accurate and contextually relevant responses
- This approach helps reduce hallucinations and improves answer quality by grounding responses in actual document content

### LLMs (Large Language Models)
Large Language Models are AI systems trained on vast amounts of text data that can:
- Understand and generate human-like text
- Process and respond to natural language queries
- Learn patterns and relationships in language
- Perform various language tasks like summarization, translation, and question answering
- We're using the gemini 2.0 flash model here

### Retrievers
Retrievers are components that:
- Search through document collections to find relevant information
- Use algorithms like BM25 to rank and select the most relevant text chunks
- Help bridge the gap between raw documents and AI model responses
- Improve answer quality by providing precise context to the AI model

## How These Components Work Together

Imagine you're trying to answer a question about a book, but you can't remember everything. Here's how our system works:

1. **The Retriever is like your memory index**
   - When you ask a question, it quickly scans through the PDF
   - It's like having a smart librarian who knows exactly which pages to look at
   - Uses BM25 algorithm to find the most relevant pieces of text
   - Think of it as a "context finder" that helps narrow down where the answer might be

2. **RAG is like having a conversation with a friend who has the book**
   - Instead of making up answers (like some AI systems do)
   - It first looks up the relevant information (using the Retriever)
   - Then uses that information to give you a proper answer
   - It's like saying "Let me check the book first" before answering

3. **The LLM (Gemini 2.0 Flash) is like a super-smart reader**
   - It can understand your questions in natural language
   - Takes the context from the Retriever
   - Combines it with its knowledge to give you a complete answer
   - It's like having a friend who's really good at explaining things

The whole process is like:
1. You ask a question
2. The Retriever finds the relevant parts of the PDF
3. RAG combines this with the LLM's knowledge
4. You get an answer that's both accurate and well-explained

This approach helps avoid "hallucinations" (making up answers) and ensures responses are grounded in the actual document content.

## Deep Dive: How RAG Actually Works

### 1. Document Processing Pipeline

#### Chunking Strategy
- Documents are split into smaller "chunks" of text
- Each chunk is typically 512-1024 tokens long
- Chunks can overlap to maintain context
- Different chunking strategies:
  - Fixed-size chunks (like cutting a document into equal pieces)
  - Semantic chunks (splitting at natural boundaries like paragraphs)
  - Sliding window chunks (overlapping chunks for better context)

#### Embedding Generation
- Each chunk is converted into a numerical vector (embedding)
- These vectors capture the semantic meaning of the text
- Similar content will have similar vector representations
- We use advanced embedding models to ensure high-quality representations

### 2. Retrieval Process

#### Query Processing
1. User's question is converted into an embedding
2. This embedding is compared with all document chunk embeddings
3. Similarity scores are calculated using:
   - Cosine similarity
   - Dot product
   - Other distance metrics

#### Context Selection
- Top-k most relevant chunks are selected
- k is typically between 3-5 chunks
- Chunks are ranked by relevance score
- Selected chunks form the context window

### 3. Generation Process

#### Prompt Engineering
- Selected chunks are formatted into a prompt
- Prompt template includes:
  - System instructions
  - Retrieved context
  - User's question
  - Response format guidelines

#### Response Generation
- LLM processes the prompt
- Generates response based on:
  - Retrieved context
  - Its pre-trained knowledge
  - Question understanding
- Response is formatted and returned to user

# 🤖 General AI Assistant with Memory

This project implements a conversational AI assistant using Streamlit, powered by Large Language Models (LLMs) and a sophisticated multi-layered memory system. The assistant can remember past conversations, extract key entities, store long-term facts, track user-defined topics in a graph database, and maintain a global user profile that persists across different chat sessions.

## ✨ Features

* **Conversational AI**: Engage in natural language conversations with an LLM-powered assistant.
* **Multi-Layered Memory**:
    * **Short-Term Context Buffer**: Remembers recent conversation turns (last 5 by default) for immediate context.
    * **Long-Term Vector Store (ChromaDB)**: Stores important facts and conversation summaries as embeddings, allowing for semantic recall.
    * **Conversation Entity Memory (LangChain)**: Automatically identifies and tracks entities (people, places, things) mentioned in the dialogue.
    * **Neo4j Graph Database**: Stores user-defined topics and relationships (e.g., topics the user has "DISCUSSED") for structured memory and querying.
    * **Global User Profile**: A shared dictionary that stores extracted personal details (name, location, hobbies, occupation, birthday) about the user, persistent across all chat sessions in a single application run.
* **LLM-Powered Information Extraction**: Uses a dedicated LLM to extract structured data for the Global User Profile.
* **Multi-Session Support**: Create and switch between different chat sessions, each with its own specific memory (context, facts, entities, topics) while sharing a common global user profile.
* **Interactive Web UI**: Built with Streamlit for an easy-to-use and visually appealing interface.

## 🚀 Technologies Used

* **Python**: The core programming language.
* **Streamlit**: For building the interactive web application.
* **LangChain**: Framework for developing LLM-powered applications, especially for memory management.
    * `ChatOpenAI` (used with Groq API): For Large Language Model interactions.
    * `ConversationEntityMemory`: LangChain's specific memory type for entity tracking.
    * `HuggingFaceEmbeddings`: For generating text embeddings.
* **ChromaDB**: A lightweight, open-source vector database used for long-term semantic memory.
* **Neo4j**: A graph database used for structured memory of topics and relationships.
* **`python-dotenv`**: (Implicit, but good practice for env vars) For loading environment variables.
* `regex` (`re` module): For robust parsing of LLM outputs.

## ⚙️ Setup Instructions

### Prerequisites

* Python 3.8+
* Docker (recommended for running Neo4j and potentially ChromaDB if not using local persistence)
* A Groq API Key
* Access to a Neo4j database instance (can be local Docker, AuraDB, etc.)

### 1. Install the dependencies 

### 2. 5. Configure Environment Variables
Create a .env file in the root of your project:
GROQ_API_KEY="your_groq_api_key_here"
NEO4J_URL="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="password"

# 🚀 Usage
Chat Interface: Type your questions, statements, or anything you want to discuss in the input box at the bottom of the screen.

Memory in Action:

Try telling the AI about yourself (e.g., "My name is [Your Name]", "I live in [City]", "My hobbies are [hobby1], [hobby2]"). Observe the "Global User Profile" in the sidebar update. This information will persist even if you switch sessions.

Ask follow-up questions or refer to previous topics. The AI will use its various memory components to provide contextually relevant answers.

Discuss specific topics (e.g., "Tell me about quantum physics," "What's the capital of France?"). The Neo4j graph may track these as discussed topics.

Multi-Session:

Use the "Select a session" radio buttons in the sidebar to switch between existing sessions.

Type a name in the "Create a new session" input box and click "Add Session" to start a fresh chat while still benefiting from the shared global user profile.

You can delete sessions, but remember you need at least one active session.

Memory Status: The sidebar also shows conceptual memory status like the number of entities tracked and recent turns in the buffer for the active session.

# 📂 Project Structure
app.py: The main Streamlit application file. It sets up the UI, manages chat sessions, and orchestrates calls to the MemoryManager.

mem_file.py: Defines the MemoryManager class, which encapsulates all the logic for managing the various types of memory (context buffer, vector store, entity memory, Neo4j graph, and global user profile).

requirements.txt: Lists all Python dependencies.
## 🧠 Smart Learning Platform

An interactive AI-powered learning platform built with **Streamlit**, **Gemini Pro**, and **Supabase** that enables students to:

* 🧾 Chat with course materials using an LLM
* 📊 Analyze question types and topic focus
* 📌 Classify user proficiency level
* 📝 Practice future questions generated from their own interactions

---

## Features

### 🔹 1. Course Chatbot

* Select a course (PDF-based) and chat with an AI assistant trained on that document.
* Questions are classified by:

  * **Type**: Fact / Reasoning / Memory
  * **Topic**: Mapped from PDF headings
* Answers include follow-up suggestions (e.g., diagram or video).
* Interactions are stored in Supabase for analysis.

### 🔹 2. Interaction Analysis

* Analyzes chat history to:

  * Detect **most frequent topics** and **question types**
  * Classify user as Beginner / Intermediate / Advanced
  * Suggest new questions for practice based on dominant topics

### 🔹 3. Practice Questions

* Presents personalized practice questions generated from your chat.
* Supports answer evaluation with:

  * Score (0–5)
  * Feedback
  * Correct answer

---

## 🧩 Code Structure

```
├── app.py              # Main app entry point (UI switcher)
├── chatbot.py          # Course chatbot mode logic
├── quiz.py             # Practice question mode
├── utils.py            # Core LLM logic, PDF parsing, classification
├── database.py         # Supabase interaction functions
├── courses/            # PDF course documents
└── .env                # Environment variables (Supabase and Gemini API keys)
```

---

## ⚙️ Requirements

Install dependencies:

```bash
pip install streamlit PyMuPDF google-generativeai python-dotenv supabase
```

Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_key
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🚀 Running the App

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 🛠️ Tech Stack

* **Frontend/UI**: [Streamlit](https://streamlit.io)
* **LLM**: [Gemini Flash 2.5 Preview](https://ai.google.dev)
* **Database**: [Supabase](https://supabase.com)
* **PDF Parsing**: [PyMuPDF](https://pymupdf.readthedocs.io)

---

## 📚 How It Works

### ✅ Topic Detection

* PDF is parsed using `PyMuPDF` and headings are extracted by font size.
* Gemini is prompted to match user question to one of the extracted headings.

### ✅ Question Classification

* Gemini classifies question as **Fact**, **Memory**, or **Reasoning** based on patterns.
* Sentiment and structure help determine user proficiency.

### ✅ Answering Questions

* Gemini answers based on the full document content with embedded instructions to be concise.
* Optional follow-ups suggested for further learning.

---

## ✨ Example Workflow

1. **Select** a course PDF from the dropdown
2. **Chat** with the AI — questions and answers appear in minimal chat layout
3. **Analyze** once 4+ questions are asked — see your top topic, question type, and level
4. **Practice** auto-generated questions from your own learning pattern

---

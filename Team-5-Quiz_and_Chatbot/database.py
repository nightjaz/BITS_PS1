import os
from dotenv import load_dotenv
from supabase import create_client, Client
import streamlit as st

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def load_chat_history(session_id, course):
    try:
        results = supabase.table("interactions").select("*")\
            .eq("session_id", session_id)\
            .eq("course", course)\
            .order("created_at", desc=True)\
            .execute()
        return results.data if results.data else []
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
        return []

def fetch_user_questions(session_id):
    try:
        response = supabase.table("future_questions").select("*")\
            .eq("session_id", session_id)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching practice questions: {e}")
        return []

def evaluate_answer(question, user_answer):
    prompt = f"""
Question: {question}
Student Answer: {user_answer}

Evaluate and provide:
1. Score (0–5)
2. Feedback
3. Correct Answer

Be concise and helpful."""
    try:
        from utils import gemini_interact
        return gemini_interact(prompt)
    except Exception as e:
        return f"Evaluation error: {e}"

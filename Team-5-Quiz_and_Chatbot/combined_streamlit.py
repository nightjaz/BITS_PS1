import os
from dotenv import load_dotenv
from google import genai
import google.generativeai as genai_eval
import streamlit as st
import PyPDF2 
import pathlib
from supabase import create_client, Client
import uuid

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.5-flash-preview-05-20"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# CHATBOT FUNCTIONS
@st.cache_data(show_spinner="Extracting text...")
def extract_pdf_text(file_path):
    """Extract text from PDF using PyPDF2"""
    texts = []
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                texts.append(page.extract_text())
        return "\n".join(texts)
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
        return ""

def gemini_interact(prompt):
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        st.error(f"Error interacting with Gemini: {e}")
        return ""

@st.cache_data(show_spinner=False)
def get_response(question, course_content):
    prompt = f"""Answer the given question based on the document provided. Be short and to the point. 
    
    ---DOCUMENT---
    {course_content}
    ---END---

    Question: {question}
    """
    return gemini_interact(prompt)

def classify_question(question):
    prompt = f"Classify the question as Fact, Reasoning or Memory. Just return the label. \nQuestion: {question}"
    return gemini_interact(prompt).strip().lower()

def extract_topic(question):
    prompt = f"Identify the topic of the question from the document provided in 4-5 words. Just return the topic name.\nQuestion: {question}"
    return gemini_interact(prompt).strip()

def determine_user_level(interactions):
    questions = "\n".join(f"- {i['question']}" for i in interactions)
    prompt = f"""
        You are a tutor assessing a student based on the questions they asked.
        Here are the questions:
        {questions}

        Based on the complexity, topic depth, and reasoning involved, classify the user's skill level as one of the following:
        Beginner, Intermediate, Advanced.

        Return only:
        Level: <Beginner/Intermediate/Advanced>"""

    result = gemini_interact(prompt)
    return result.strip()

def generate_future_question(most_freq_topic, most_freq_type, user_level):
    prompt = f"""
        Based on the above interactions, generate 3 questions which user might ask in future. The questions should be from 
        {most_freq_topic} and should be {most_freq_type} based. The level of questions should be at par with user level: {user_level}.
        Return as a list with each question on a new line.
        Do not return any other text."""
    raw_response = gemini_interact(prompt)
    if not raw_response:
        return []
    return [q.strip() for q in raw_response.split('\n') if q.strip()]

def load_chat_history(session_id, course):
    results = supabase.table("interactions").select("*")\
        .eq("session_id", session_id)\
        .eq("course", course)\
        .order("created_at", desc=True)\
        .execute()
    return results.data if results.data else []

# PRACTICE FUNCTIONS
def fetch_user_questions(session_id):
    """Fetch questions generated for current user session"""
    try:
        response = supabase.table("future_questions").select("*")\
            .eq("session_id", session_id)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching questions: {e}")
        return []

def evaluate_answer(question, user_answer):
    """Evaluate user's answer using Gemini"""
    prompt = f"""
    Question: {question}
    Student Answer: {user_answer}
    
    Evaluate this answer and provide:
    1. Score (0-5): Rate the answer quality
    2. Feedback: Brief explanation of the evaluation
    3. Correct Answer: What the ideal answer should be
    
    Keep it concise and helpful.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error evaluating answer: {e}"

# Streamlit app configuration
st.set_page_config(page_title="Smart Course Learning Platform", layout="wide")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox(
    "Choose App Mode",
    ["Course Chatbot", "Practice Questions"]
)

if app_mode == "Course Chatbot":
    st.title("Smart Course Chatbot")
    st.subheader("Get answers to your course-related questions along with interactive analysis!")

    # List of courses with PDF files
    courses = {
        "Current Electricity": "courses/current-electricity-ncert.pdf",
        "Ray Optics": "courses/ray-optics-ncert.pdf",
        "Solutions": "courses/solutions-ncert.pdf",
        "Matrices and Determinants": "courses/matrices-ncert.pdf",
    }

    selected_course = st.selectbox(
        "Select a Course to study!", 
        list(courses.keys()), 
        index=None
    )

    if selected_course:
        course_file = courses[selected_course]
        with open(course_file, "rb") as f:
            course_content = extract_pdf_text(course_file)
        st.session_state.course_content = course_content

        # Load chat history if not already
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = load_chat_history(st.session_state.session_id, selected_course)

        # Show chat history
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history:
                st.markdown(f"**You:** {chat['question']}")
                st.markdown(f"**Bot:** {chat['response']}")
                st.markdown("---")

        # Ask question
        question = st.text_input("Ask a question", key="question_input", placeholder="Type your question here...")

        if st.button("Get Answer"):
            question = st.session_state.question_input
            if question.strip() == "":
                st.warning("Please enter a question.")
            else:
                # Getting response from Gemini
                response = get_response(question, course_content)
                question_type = classify_question(question)
                topic = extract_topic(question)

                # Storing in Supabase
                supabase.table("interactions").insert({
                    "session_id": st.session_state.session_id,
                    "course": selected_course,
                    "question": question,
                    "response": response,
                    "question_type": question_type,
                    "topic": topic
                }).execute()

                # Updating session state chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "response": response,
                    "question_type": question_type,
                    "topic": topic
                })

                # An option to clear question input
                del st.session_state.question_input
                st.rerun()

        st.markdown("---")
        st.subheader("Analysis of Interactions")
        if st.button("Analyze Interactions"):
            history = st.session_state.chat_history
            if len(history) < 4:
                st.warning("You need at least 4 interactions to analyze.")
            else:
                topic_count = {}
                type_count = {}
                user_level = determine_user_level(history)

                for chat in history:
                    topic = chat.get("topic", "").strip()
                    q_type = chat.get("question_type", "").strip()
                    topic_count[topic] = topic_count.get(topic, 0) + 1
                    type_count[q_type] = type_count.get(q_type, 0) + 1

                # Finding most frequent topic and type
                most_freq_topic = max(topic_count, key=topic_count.get)
                most_freq_type = max(type_count, key=type_count.get)

                st.info(f"Most Frequent Topic: {most_freq_topic}")
                st.info(f"Most Frequent Question Type: {most_freq_type}")
                st.info(f"User Skill Level: {user_level}")

                # Generating future questions
                future_questions = generate_future_question(most_freq_topic, most_freq_type, user_level)

                # Saving each future question to Supabase
                for q in future_questions:
                    supabase.table("future_questions").insert({
                        "session_id": st.session_state.session_id,
                        "course": selected_course,
                        "question": q,
                        "topic": most_freq_topic,
                        "question_type": most_freq_type
                    }).execute()
                
                st.success("Future questions generated and saved! You can now practice them in the 'Practice Questions' section.")

elif app_mode == "Practice Questions":
    st.title("Q&A Practice")
    st.subheader("Practice with questions generated based on your learning patterns")

    # Initialize session state for practice
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'practice_questions' not in st.session_state:
        st.session_state.practice_questions = []
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'show_evaluation' not in st.session_state:
        st.session_state.show_evaluation = False

    # Loading questions for current user
    if not st.session_state.practice_questions:
        with st.spinner("Loading your practice questions..."):
            st.session_state.practice_questions = fetch_user_questions(st.session_state.session_id)

    if st.session_state.practice_questions:
        total_questions = len(st.session_state.practice_questions)
        current_index = st.session_state.current_question_index
        
        # Current question
        current_question = st.session_state.practice_questions[current_index]
        question_text = current_question['question']
        question_id = current_question['id']
        
        st.write("### Question:")
        st.write(question_text)
        
        # Answer input
        user_answer = st.text_area("Your Answer:", key=f"answer_{question_id}", height=150)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        # Submit answer button
        with col2:
            if st.button("Submit Answer", type="primary"):
                if user_answer.strip():
                    # Store answer
                    st.session_state.user_answers[question_id] = user_answer
                    st.session_state.show_evaluation = True
                    
                    # Evaluate answer
                    with st.spinner("Evaluating your answer..."):
                        evaluation = evaluate_answer(question_text, user_answer)
                        st.session_state.current_evaluation = evaluation
                    
                    st.rerun()
                else:
                    st.warning("Please enter an answer before submitting.")
        
        # Show evaluation if available
        if st.session_state.show_evaluation and 'current_evaluation' in st.session_state:
            st.write("### Evaluation:")
            st.write(st.session_state.current_evaluation)
            
            # Next question button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if current_index < total_questions - 1:
                    if st.button("Next Question", type="secondary"):
                        st.session_state.current_question_index += 1
                        st.session_state.show_evaluation = False
                        if 'current_evaluation' in st.session_state:
                            del st.session_state.current_evaluation
                        st.rerun()
                else:
                    st.success("You've completed all practice questions!")
                    if st.button("Restart Practice", type="secondary"):
                        st.session_state.current_question_index = 0
                        st.session_state.show_evaluation = False
                        if 'current_evaluation' in st.session_state:
                            del st.session_state.current_evaluation
                        st.rerun()

    else:
        st.info("No practice questions available yet!")
        st.write("To generate practice questions:")
        st.write("1. Go to 'Course Chatbot' mode")
        st.write("2. Select a course and ask at least 4 questions")
        st.write("3. Click 'Analyze Interactions' to generate practice questions")
        st.write("4. Return here to practice!")

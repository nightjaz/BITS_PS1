import os
from dotenv import load_dotenv
import streamlit as st
from google import genai
from google.genai import types
from pathlib import Path

load_dotenv()

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.5-flash-preview-05-20"

# Define course files
courses = {
    "Current Electricity": "courses/current-electricity-ncert-1-3.pdf",
    "Ray Optics": "courses/ray-optics-ncert.pdf",
    "Solutions": "courses/solutions-ncert.pdf",
    "Matrices and Determinants": "courses/matrices-ncert.pdf",
}

# Streamlit UI
st.title('Take your Learning Method to Next Level!')
selected_course = st.selectbox(
    "What course would you like to be assessed for?",
    list(courses.keys()),
    index=None,
    placeholder="Select a course...",
)
st.write("You selected course:", selected_course)

def get_course_content(selected_course, courses):
    # Retrieve and Encode the PDF byte
    if not selected_course:
        st.warning("Please select a course!")

    course_path = Path(courses[selected_course])

    return types.Part.from_bytes(
            data= course_path.read_bytes(),
            mime_type='application/pdf',
    ) 

course_content = None
if selected_course:
    course_content = get_course_content(selected_course, courses)

def generate_question(course_content):
    # Generate question using Gemini
    prompt = f"Create a short question (fact-based, memory-based or reasoning based) by reading the document provided:\n\n{course_content}"
    try:
        response = client.models.generate_content(
            model = model,
            contents= [course_content, prompt],
        )
        question = response.text
        return question
    
    except Exception as e:
        st.error(f"Error generating question: {e}")
        return None

def evaluate_answer(question, user_answer):
    if not question:
        st.warning("No question available for evaluation.")
        return None
    
    if not user_answer:
        st.warning("Please enter your answer before evaluation.")
        return None

    eval_prompt = ("Evaluate the answer based on the course content. The evaluation componets should include whether the answer"
    "was correct or not with a short reason, type of question(fact-based, memory-based or reasoning-based) and topic of question"
    "from the course. Be short and consise.\n\n"f"Question:{question}\nUser Answer:{user_answer}\n")
    try:
        eval_response = client.models.generate_content(
            model= model,
            contents= [eval_prompt]
        )
        feedback = eval_response.text
        st.write("### Evaluation and analysis:")
        st.write(feedback)
        return feedback
    
    except Exception as e:
        st.error(f"Error evaluating answer:{e}")
        return None


question_button = st.button("Generate Question")
if 'question' not in st.session_state:
    st.session_state.question = None

if question_button or st.session_state.question is None:
    if st.session_state.question is None:
        st.session_state.question = generate_question(course_content)

    if st.session_state.question:
        st.write("### Question:")
        st.write(st.session_state.question)
        user_answer = st.text_input("Answer here:", key="user_answer")
        eval_button = st.button("Evaluate Answer")

        if eval_button:
            # st.session_state.evaluate = True
            st.write("Following analysis")
    
        # if eval_button and user_answer:
            evaluate_answer(st.session_state.question, user_answer)
            # st.session_state.evaluate = False 
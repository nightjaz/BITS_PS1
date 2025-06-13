import os
from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
import PyPDF2
from google import genai

# Gemini API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.5-flash-preview-05-20"


# Text extraction from PDF
def extract_pdf_text(pdf_file) -> str:
    text = ""
    with open(pdf_file, "rb") as f:
        pdf = PyPDF2.PdfReader(f)
        for page in pdf.pages:
            text += page.extract_text()
    return text


# Streamlit UI
st.title("Welcome to your personalized study mentor!")

# Display instructions
st.info(
    """
     **Instructions:**  
    1. Select a course from the list.  
    2. Generate a practice question based on its content.  
    3. Provide your answer in the text box.  
    4. Get automated evaluation and feedback from Gemini!  
    """
)

# List of courses with PDF files
courses = {
    "Current Electricity": "courses/current-electricity-ncert-1-3.pdf",
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
    st.success(f"✅ {selected_course} selected.")
    course_file = courses[selected_course]
    course_content = extract_pdf_text(course_file)


    # Generate Question
    if st.button("Generate Question") or st.session_state.get("generated", False):
        st.session_state["generated"] = True

        if "generated_question" not in st.session_state:
            # Generate question with Gemini
            prompt = f"""Create a short question (fact-based, memory-based or reasoning based) by reading the document provided:"\n\n{course_content}"""    

            response = client.models.generate_content(
                model = model,
                contents = [prompt],
            )
            st.session_state.generated_question = response.text.strip()

        st.write("### Question:")
        st.write(st.session_state.generated_question)


        # User Answer
        user_answer = st.text_input("Enter your answer here:")

        if st.button("Evaluate Answer") or st.session_state.get("evaluation_done", False):
            st.session_state["evaluation_done"] = True

            if user_answer:
                eval_prompt = f"""Evaluate the answer based on the course content. Provide whether it is correct or not with a short reason, the type of question (fact-based, memory-based or reasoning-based) and the topic of the question. Be short and concise.
                    Question: {st.session_state.generated_question}
                    User Answer: {user_answer}
                    Course Content: {course_content}
                    """
                response = client.models.generate_content(
                    model = model,
                    contents = [eval_prompt],
                )
                st.write("### Evaluation and Analysis:")
                st.write(response.text)
            else:
                st.error("⚡ Please provide your answer first.")

import os
import PyPDF2
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
from unstructured.partition.pdf import partition_pdf
import fitz  # PyMuPDF

load_dotenv()

# Gemini initialization
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# Text extraction from PDF
@st.cache_data(show_spinner="Extracting PDF text...")

def extract_content_and_headings(file_path, heading_font_size_threshold=14):
    """
    Extracts full text and headings from a PDF using PyMuPDF.

    Returns:
        full_text (str): Concatenated text from all pages.
        headings (List[str]): Unique headings detected by font size.
    """
    doc = fitz.open(file_path)
    full_text = []
    headings = set()

    for page in doc:
        page_text = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            for line in block.get("lines", []):
                line_text = ""
                max_font_size = 0

                for span in line.get("spans", []):
                    line_text += span["text"]
                    max_font_size = max(max_font_size, span["size"])

                line_text = line_text.strip()
                if line_text:
                    page_text.append(line_text)

                    # If font size is large enough, treat as heading
                    if max_font_size >= heading_font_size_threshold:
                        headings.add(line_text)

        full_text.append("\n".join(page_text))

    return "\n".join(full_text), list(headings)


# Gemini interaction function
def gemini_interact(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return ""

@st.cache_data(show_spinner=False)

def get_response(question, course_content):
    prompt = f"""Answer the given question based on the document provided. Don't be verbose, just answer the question directly. Try to 
    be concise and to the point.
    
    ---DOCUMENT---
    {course_content}
    ---END---

    Question: {question}
    
    If the question is related to course content, provide a direct answer based on the document.
    If the question is about the chatbot itself, provide a brief explanation of its capabilities.
    If the question is related to the course but not directly answerable from the document, give a brief answer based on your knowledge 
    and state that it is out of syllabus.
    If the question does not fall into any of the above categories, politely inform the user to ask questions related to the 
    course content.
    After answering the question, ask whether the user would like a diagram or a video explanation for the answer.

    """
    # Also, it should find preferred learning style of user: if visual then give diagrams, if auditory then
    # Follow up question functionality needs to be improved.
    return gemini_interact(prompt)

def classify_question(question):
    prompt = f"""Classify the question as Fact, Reasoning or Memory. Just return the label. \nQuestion: {question}
    To identify the type of question, consider the following:
    - Fact: Questions that require a direct answer from the document. If you find a direct line in the chapter which answers the 
        question, classify it as Fact.
    - Reasoning: Questions that require logical deduction or inference. If the question is too long and involves mathematical 
        calculations or multiple steps, classify it as Reasoning. But if it is long and has direct lines in the chapter, classify 
        it as Fact.
    - Memory: Questions that require recalling information like any formula. If the question is about a formula or a chemical
        compound which is supposed to be memorized, classify it as Memory. If the formula is directly given in the chapter, classify 
        it as Memory, but if it requires derivation from give formulas, classify it as Reasoning.

    """
     
    return gemini_interact(prompt).strip().lower()

def extract_topic(question, course_content):
    prompt = f"""Identify the topic of the question by reading the list of headings returned from the document provided.

    ---DOCUMENT---
    {course_content}
    ---END---

    \nQuestion: {question}.

    Do not make up a topic, it should be the one from the document under which the question falls. If the question is about the chatbot
    itself, classify it as "Chatbot queries". If the question is related to the course but not directly answerable from the document,
    classify it as "Out of syllabus". If the question does not fall into any of the above categories, classify it as "General queries".
    Just return the topic without any additional text.
    """
    
    return gemini_interact(prompt).strip()

def determine_user_level(interactions):
    questions = "\n".join(f"- {i['question']}" for i in interactions)
    prompt = f"""
        You are a tutor who needs to determine student level based on the questions they asked.
        Here are the questions:
        {questions}
    
        To determine the user level, consider the following algorithm:
            - Assign a score to each question based on its type:
                - Single line Fact: 1 point
                - Multiple line Fact: 2 points
                - Memory based the formula for which is directly given in the chapter: 1 point
                - Memory based the formula for which is not directly given in the chapter but can be derived: 2 points
                - Reasoning based: 3 points
                - Out of syllabus but fact based: 1.5 points for single line, 2.5 points for multiple line
                - Out of syllabus but memory based: 2 points only if part of the formula/derivation is given in the chapter, else 0.5 points
                - Out of syllabus but reasoning based: 3 points only if part of the solution is given in the chapter, else 1 point
                - Chatbot queries: 0 points
                - General queries: -1 point
                - Follow-up questions: +1 point for each follow-up question. If the follow-up is after a reasoning based question, 
                  then +2 points.
                - Identify the question's sentiment whether it is positive, negative or neutral.
                    - If the question is positive, add 1 point, if negative, subtract 1 point, else no change.
                - Calculate the average score based on the questions asked.
                - If the average score is:
                    - below 1: Beginner
                    - 1-2.5: Intermediate
                    - 2.5 above: Advanced
            
        Return:
            Level: <Beginner/Intermediate/Advanced> and a brief explanation of why you think the user is at that level.
    """
    # We can use NLP and sentiment analysis to detect state of user. If the user is easliy frustrated or confused by memory/fact based
    # questions, then the user cannot be at advanced level.
        # The explanation should not include entire algorithm, just the reasoning behind the level. For example, if the user is at
        # advanced level, you can say "The user has asked multiple reasoning based questions and has a good understanding of the 
        # course content."


    result = gemini_interact(prompt)
    return result.strip()
    

def generate_future_question(most_freq_topic, most_freq_type, user_level, second_most_freq_topic):
    prompt = f"""
        Based on the above interactions, generate 3 questions which user might ask in future.
        Keep the following in mind while generating questions:
        - If there are n questions from {most_freq_topic} and n-1 questions from {second_most_freq_topic}, then 1 of the questions 
        should be from {second_most_freq_topic} and the rest from {most_freq_topic}. 
        - If the most frequent topic is "Chatbot queries" or "General queries", then do not generate any questions.
        - If the most frequent topic is "Out of syllabus", then find whether the user has asked questions related to that topic or not.
        If yes, then generate questions from that topic.
        - The questions should be of {most_freq_type} type.
        - The questions should be of appropriate difficulty level based on the user level: {user_level}.
        
        Return:
        - 3 questions, each on a new line.
        - If you cannot generate questions based on the above criteria, return an empty list.
    """
    raw_response = gemini_interact(prompt)
    if not raw_response:
        return []
    return [q.strip() for q in raw_response.split('\n') if q.strip()]

import os
import google.generativeai as genai 
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from collections import Counter

load_dotenv()

# Supabase Credentials  
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

def fetch_chat_logs():
    response = (
        supabase.table("course_chat_logs")
        .select("*")
        .execute()
    )
    return response.data if response.data else []

def classify_question(question):
    prompt = f"Classify the following question into a topic related to current electricity(e.g., Electric Currents in Conductors, Ohm’s Law, etc.). Answer in least possible words:\n\nQuestion: {question}\n\nTopic:\n\n"
    response = model.generate_content(prompt)
    return response.text.strip() if response.text else "This is out of scope of the chapter"

def classify_user_level(questions):
    formatted_prompts = "/n".join(questions)
    prompt = f"Classify the user as beginner, intermediate or advanced based on the type of questions asked. Answer in one word.\n\nQuestion: {formatted_prompts}\n\nLevel:"
    response = model.generate_content(prompt)
    return response.text.strip() if response.text else "Unable to judge"

def classify_chat_logs():
    chat_logs = fetch_chat_logs()
    classified_logs = []

    for log in chat_logs:
        chat_history = json.loads(log["chat_history"])
        questions = [q["prompt"] for q in chat_history["chat_history"]]
        topics = [classify_question(q) for q in questions]
        classified_logs.append({"id": log["id"], "chat_history": questions, "time_spent": log["time_spent"], "topics": topics})

    return classified_logs

def extract_questions(chat_logs):
    """Extract questions from JSONB format for each user."""
    questions_per_user = {}

    for log in chat_logs:
        chat_history = json.loads(log["chat_history"])  # Convert JSON string to dictionary
        questions = [q["prompt"] for q in chat_history["chat_history"]]  # Extract questions
        
        questions_per_user[log["id"]] = questions  # Store questions per user ID

    return questions_per_user

classified_logs = classify_chat_logs()
topics_list = [log["topics"] for log in classified_logs]
print(f"{topics_list}\n")

chat_logs = fetch_chat_logs()
questions_per_user = extract_questions(chat_logs)

for index, questions in enumerate(questions_per_user.values(), start=1):
    if not questions:
        print(f"Most common topic for user {index} is: No topic")
        print(f"User {index} is classified as: Unknown")
        continue
    
    # Classify topics for each question
    topics = [classify_question(q) for q in questions]
   
    if all(count == 1 for count in Counter(topics).values()):
        most_common_topic = "No topic"
    else:
         most_common_topic = Counter(topics).most_common(1)[0][0]

    # Determine user level
    user_level = classify_user_level(questions)

    print(f"Most common topic for user {index} is: {most_common_topic}")
    print(f"User {index} is classified as: {user_level}\n")

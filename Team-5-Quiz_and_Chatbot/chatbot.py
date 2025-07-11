import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st
from llama_index.core import SimpleDirectoryReader
import fitz  # PyMuPDF
import pathlib
from supabase import create_client, Client
import uuid
from utils import extract_content_and_headings, get_response, classify_question, extract_topic, determine_user_level, generate_future_question
from database import load_chat_history, supabase

def render_chat(chat):
    user_msg = f"""
    <div style="
        padding: 5px 10px;
        margin: 8px 0;
        text-align: right;
        font-weight: 500;
    ">
        You: {chat['question']}
    </div>
    """

    bot_msg = f"""
    <div style="
        padding: 5px 10px;
        margin: 8px 0;
        text-align: left;
    ">
        <strong>Bot:</strong> {chat['response']}
    </div>
    """

    st.markdown(user_msg, unsafe_allow_html=True)
    st.markdown(bot_msg, unsafe_allow_html=True)

def course_chatbot(session_id):
    def get_user_feedback():
        st.subheader("User Feedback")
        feedback = st.text_area("Please provide your feedback on the chatbot's performance and suggestions for improvement:")
        if st.button("Submit Feedback"):
            if feedback.strip() == "":
                st.warning("Please provide some feedback.")
            else:
                # Store feedback in Supabase
                supabase.table("feedback").insert({
                    "session_id": st.session_state.session_id,
                    "feedback": feedback
                }).execute()
                st.success("Thank you for your feedback!")
                del st.session_state.feedback


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
        # st.success(f"✅ {selected_course} selected.")
        course_file = courses[selected_course]
        with open(course_file, "rb") as f:
            course_content = extract_content_and_headings(course_file)
        st.session_state.course_content = course_content

        # Load chat history if not already
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = load_chat_history(st.session_state.session_id, selected_course)

        # Show chat history
        if st.session_state.chat_history:
            # st.subheader("🧾 Chat History")
            for chat in st.session_state.chat_history:
                render_chat(chat)

        # Ask question
        question = st.text_input("Ask a question", key="question_input", placeholder="Type your question here...")

        if st.button("Get Answer"):
            question = st.session_state.question_input.strip()
            if question == "":
                    st.warning("Please enter a question.")
            else:
                with st.spinner("Getting answer..."):
                    # Get response from Gemini
                    response = get_response(question, course_content)
                    question_type = classify_question(question)
                    topic = extract_topic(question, course_content)

                    # Store in Supabase
                    supabase.table("interactions").insert({
                        "session_id": st.session_state.session_id,
                        "course": selected_course,
                        "question": question,
                        "response": response,
                        "question_type": question_type,
                        "topic": topic
                    }).execute()

                    # Update session state chat history
                    st.session_state.chat_history.append({
                        "question": question,
                        "response": response,
                        "question_type": question_type,
                        "topic": topic
                    })

                    # Clear question input
                    st.session_state.question_input = ""

        st.markdown("---")
        st.subheader("Analysis of Interactions")
        if st.button("🧠 Analyze Interactions"):
            history = st.session_state.chat_history
            if len(history) < 4:
                st.warning("You need at least 4 interactions to analyze.")
            else:
            # Count frequency of topics and question types
                topic_count = {}
                type_count = {}
                user_level = determine_user_level(history)

                for chat in history:
                    topic = chat.get("topic", "").strip()
                    q_type = chat.get("question_type", "").strip()
                    topic_count[topic] = topic_count.get(topic, 0) + 1
                    type_count[q_type] = type_count.get(q_type, 0) + 1

                # Find most frequent topic and type
                most_freq_topic = max(topic_count, key=topic_count.get)
                most_freq_type = max(type_count, key=type_count.get)

                if not most_freq_topic or not most_freq_type:
                    st.warning("Not enough data to analyze. Please ask more questions.")
                
                # Check if the most frequent topic is valid
                if most_freq_topic in ["Chatbot queries", "Out of syllabus", "General queries"]:
                    st.warning("We cannot generate future questions for the most frequent topic as it is not related to the course content. " \
                    "Please ask more questions related to the course content.")

                st.info(f"\nMost Frequent Topic: {most_freq_topic}")
                st.info(f"\nMost Frequent Question Type: {most_freq_type}")
                st.info(f"\nUser Skill Level: {user_level}")
                
                # Second most frequnet topic
                second_most_freq_topic = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[1][0] if len(topic_count) > 1 else None

                # Generate future questions
                future_questions = generate_future_question(most_freq_topic, most_freq_type, user_level, second_most_freq_topic)

                # Save each future question to Supabase table
                if future_questions:
                    for q in future_questions:
                        # Assign topic based on which topic name appears in the question, fallback to most_freq_topic
                        if second_most_freq_topic and second_most_freq_topic.lower() in q.lower():
                            topic_for_q = second_most_freq_topic
                        else:
                            topic_for_q = most_freq_topic
                        supabase.table("future_questions").insert({
                            "session_id": st.session_state.session_id,
                            "course": selected_course,
                            "question": q,
                            "topic": topic_for_q,
                            "question_type": most_freq_type
                        }).execute()
                
                st.success("Future questions generated and saved to database.")

                # Get user feedback
                get_user_feedback()

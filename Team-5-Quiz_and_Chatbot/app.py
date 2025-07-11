import streamlit as st
import uuid
from chatbot import course_chatbot
from quiz import practice_mode

st.set_page_config(page_title="Smart Learning Platform", layout="wide")

# Session init
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Mode selection
st.markdown("# Smart Learning Platform")
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox(
    "Choose App Mode",
    ["Course Chatbot", "Practice Questions"]
)

# Display selected mode
if app_mode == "Course Chatbot":
    st.sidebar.success("You are in Course Chatbot mode.")
    st.markdown("## Course Chatbot")
    st.markdown("Ask questions about the course content and get answers along with an interactive analysis.")
    course_chatbot(st.session_state.session_id)

elif app_mode == "Practice Questions":
    st.sidebar.success("You are in Practice Questions mode.")
    practice_mode(st.session_state.session_id)

else:
    st.sidebar.warning("Please select a mode from the sidebar.")
    st.markdown("## Welcome to the Smart Learning Platform")
    st.markdown("Please select a mode from the sidebar to get started.")

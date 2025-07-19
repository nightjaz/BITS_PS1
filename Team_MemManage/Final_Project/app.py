import os
import random
import json
import streamlit as st
from mem_file import MemoryManager # Import your MemoryManager

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# --- Configuration for your General Chatbot ---
GENERAL_CHATBOT_TOPICS = {
    "personal_preferences", "facts", "questions", "history", "future_plans",
    "feedback", "general_knowledge", "current_events", "opinions", "suggestions"
}
GENERAL_MEMORIZABLE_KEYWORDS = [
    "my name is", "i am", "i like", "i dislike", "i prefer", "my goal", "remember that",
    "always", "never", "important", "need to", "must", "my opinion is", "can you tell me about"
]

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="General AI Assistant", layout="wide")
st.title("🤖 General AI Assistant with Memory")
st.markdown("I can remember our conversations to give you more personalized and relevant answers!")

# --- Initialize LLMs in Streamlit's Session State (once globally) ---
if 'llm_main' not in st.session_state:
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            st.error("GROQ_API_KEY environment variable not set. Please set it and rerun the app.")
            st.stop()

        st.session_state.llm_main = ChatOpenAI(
            openai_api_base="https://api.groq.com/openai/v1",
            openai_api_key=groq_api_key,
            model_name="llama3-8b-8192", # Changed model for consistency, you can adjust this.
            temperature=0.7
        )
        st.session_state.llm_entity_extraction = ChatOpenAI(
            openai_api_base="https://api.groq.com/openai/v1",
            openai_api_key=groq_api_key,
            model_name="llama3-8b-8192", # Changed model for consistency, you can adjust this.
            temperature=0.1 # Lower temperature for more factual entity extraction
        )
        st.success("Language Models initialized.")

    except Exception as e:
        st.error(f"Error initializing Language Models: {e}")
        st.error("Please ensure your GROQ_API_KEY environment variable is correctly set.")
        st.stop()

# --- Initialize Global User Profile (once globally for the app run) ---
if 'global_user_profile' not in st.session_state:
    st.session_state.global_user_profile = {} # Stores shared info like name, across all sessions

# --- Multi-Session State Initialization and MemoryManager Creation ---
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
    st.session_state.active_session = "Session 1"

    # Initialize the first session's memory and messages
    st.session_state.sessions["Session 1"] = {
        "messages": [{"role": "assistant", "content": "Hello! How can I help you today in Session 1?"}],
        "memory_manager": MemoryManager(
            llm_for_entity_extraction=st.session_state.llm_entity_extraction,
            chroma_collection_name="chatbot_facts_Session_1",
            graph_user_node_label="StreamParticipant",
            graph_user_node_id_property="session_id",
            graph_user_node_id_value="Session_1",
            graph_topic_node_label="ConversationCategory",
            graph_topic_name_property="category_name",
            graph_relationship_type="DISCUSSED",
            domain_topics=GENERAL_CHATBOT_TOPICS,
            memorizable_keywords=GENERAL_MEMORIZABLE_KEYWORDS,
            global_user_profile_ref=st.session_state.global_user_profile # PASS GLOBAL PROFILE HERE
        )
    }

# Ensure memory manager exists for current active session when switching or on app reload
if st.session_state.active_session not in st.session_state.sessions:
    cleaned_session_name = st.session_state.active_session.replace(' ', '_').replace('.', '').replace('-', '')
    st.session_state.sessions[st.session_state.active_session] = {
        "messages": [{"role": "assistant", "content": f"Hello! This is a new chat session: {st.session_state.active_session}"}],
        "memory_manager": MemoryManager(
            llm_for_entity_extraction=st.session_state.llm_entity_extraction,
            chroma_collection_name=f"chatbot_facts_{cleaned_session_name}",
            graph_user_node_label="StreamParticipant",
            graph_user_node_id_property="session_id",
            graph_user_node_id_value=cleaned_session_name,
            graph_topic_node_label="ConversationCategory",
            graph_topic_name_property="category_name",
            graph_relationship_type="DISCUSSED",
            domain_topics=GENERAL_CHATBOT_TOPICS,
            memorizable_keywords=GENERAL_MEMORIZABLE_KEYWORDS,
            global_user_profile_ref=st.session_state.global_user_profile # PASS GLOBAL PROFILE HERE
        )
    }
    st.success(f"MemoryManager initialized for session: {st.session_state.active_session}")


# --- Define the Chatbot's Response Generation Logic (as a function) ---
def get_chatbot_response(user_input: str, recalled_memory_data: dict) -> str:
    """
    Generates a chatbot's response by sending the user's input and all recalled memory
    data to the Large Language Model.
    """
    entities = recalled_memory_data.get("entities", "No specific entities remembered yet.")
    facts = recalled_memory_data.get("facts", "No relevant facts found.")
    topics = recalled_memory_data.get("topics", "No particular topics identified yet.")
    context_buffer = recalled_memory_data.get("context_buffer", "No recent context.")
    global_user_profile = recalled_memory_data.get("global_user_profile", "No global user profile set.")

    prompt_template = f"""
    You are a friendly, helpful, and knowledgeable general-purpose AI assistant.
    Your goal is to understand the user's queries across various topics and provide
    accurate, relevant, and concise answers. You can answer questions, provide information,
    summarize, elaborate, or engage in general conversation.

    **Crucially, you have access to a memory of our past interactions, including a shared
    profile for the user.** Use this memory to provide personalized, coherent, and
    context-aware responses.

    --- Current User Input ---
    {user_input}

    --- Recalled Memory Data ---
    * **Shared User Profile (across sessions):** {global_user_profile}
    * **Key Entities/Details (this session):** {entities}
    * **Relevant Past Facts (this session):** {facts}
    * **Identified Conversation Categories/Topics (this session):** {topics}
    * **Recent Conversation Flow (this session):**
        {context_buffer}
    ---

    Based on the above information, please provide a helpful and relevant response.
    **Do NOT explicitly mention that you are storing or recalling information, or updating your memory.**
    Instead, seamlessly integrate remembered details into your answers to show you understand and remember.
    For example, if the user says "My name is Alice", just use "Alice" in subsequent responses, don't say "Okay, I've stored your name as Alice."
    """

    messages = [
        SystemMessage(content="You are a friendly, general-purpose AI assistant that remembers past conversations and user preferences."),
        HumanMessage(content=prompt_template)
    ]

    response = st.session_state.llm_main.invoke(messages)
    return response.content

# --- Streamlit Chat UI Logic ---

# Get the current active session's data
active_session_data = st.session_state.sessions[st.session_state.active_session]
messages = active_session_data["messages"]
current_memory_manager = active_session_data["memory_manager"] # Use this instance!

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(f"Ask me anything in {st.session_state.active_session}..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            recalled_info = current_memory_manager.recall_information(prompt)
            response = get_chatbot_response(prompt, recalled_info)
            st.markdown(response)
        current_memory_manager.save_context(prompt, response)
        if random.random() < 0.3:
            current_memory_manager.periodic_refresh()

    messages.append({"role": "assistant", "content": response})

st.sidebar.header("How to Use:")
st.sidebar.markdown(
    """
    Type your questions or statements in the chat box below.
    I will try to answer and remember details from our conversation.
    """
)
st.sidebar.subheader("Global User Profile:")
if st.session_state.global_user_profile:
    for key, value in st.session_state.global_user_profile.items():
        if isinstance(value, list):
            st.sidebar.markdown(f"- **{key.replace('_', ' ').title()}:** {', '.join(value)}")
        else:
            st.sidebar.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")
else:
    st.sidebar.markdown("- No global profile data yet.")


st.sidebar.subheader(f"Memory Status (Conceptual) for '{st.session_state.active_session}':")
# CORRECTED LINES: Use current_memory_manager instead of st.session_state.memory_manager
st.sidebar.markdown(f"- Entities tracked: {len(current_memory_manager.entity_memory.entity_store.store)}")
st.sidebar.markdown(f"- Recent turns in buffer: {len(current_memory_manager.context_buffer)}")

session_names = list(st.session_state.sessions.keys())
if session_names:
    selected_session = st.sidebar.radio("Select a session:", session_names,
                                        index=session_names.index(st.session_state.active_session))
    if selected_session != st.session_state.active_session:
        st.session_state.active_session = selected_session
        st.rerun()

new_session_name = st.sidebar.text_input("Create a new session")
if st.sidebar.button("Add Session") and new_session_name and new_session_name not in st.session_state.sessions:
    cleaned_session_name = new_session_name.replace(' ', '_').replace('.', '').replace('-', '')
    st.session_state.sessions[new_session_name] = {
        "messages": [{"role": "assistant", "content": f"Hello! This is a new chat session: {new_session_name}"}],
        "memory_manager": MemoryManager(
            llm_for_entity_extraction=st.session_state.llm_entity_extraction,
            chroma_collection_name=f"chatbot_facts_{cleaned_session_name}",
            graph_user_node_label="StreamParticipant",
            graph_user_node_id_property="session_id",
            graph_user_node_id_value=cleaned_session_name,
            graph_topic_node_label="ConversationCategory",
            graph_topic_name_property="category_name",
            graph_relationship_type="DISCUSSED",
            domain_topics=GENERAL_CHATBOT_TOPICS,
            memorizable_keywords=GENERAL_MEMORIZABLE_KEYWORDS,
            global_user_profile_ref=st.session_state.global_user_profile # PASS GLOBAL PROFILE HERE
        )
    }
    st.session_state.active_session = new_session_name
    st.rerun()

if st.sidebar.button("Delete Current Session") and len(st.session_state.sessions) > 1:
    del st.session_state.sessions[st.session_state.active_session]
    st.session_state.active_session = list(st.session_state.sessions.keys())[0]
    st.rerun()
import streamlit as st
from database import fetch_user_questions, evaluate_answer

def practice_mode(session_id):
    st.markdown("## Practice Questions")
    st.markdown("Practice with questions based on your learning!")

    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'practice_questions' not in st.session_state:
        st.session_state.practice_questions = fetch_user_questions(session_id)
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'show_evaluation' not in st.session_state:
        st.session_state.show_evaluation = False

    if st.session_state.practice_questions:
        total = len(st.session_state.practice_questions)
        idx = st.session_state.current_question_index
        question = st.session_state.practice_questions[idx]

        st.write(f"### Q{idx + 1}: {question['question']}")
        user_answer = st.text_area("Your Answer:", key=f"answer_{question['id']}", height=150)

        if st.button("Submit Answer"):
            if user_answer.strip():
                st.session_state.user_answers[question['id']] = user_answer
                st.session_state.show_evaluation = True
                with st.spinner("Evaluating..."):
                    evaluation = evaluate_answer(question['question'], user_answer)
                    st.session_state.current_evaluation = evaluation
                st.rerun()
            else:
                st.warning("Answer cannot be empty.")

        if st.session_state.show_evaluation and 'current_evaluation' in st.session_state:
            st.write("### Evaluation:")
            st.write(st.session_state.current_evaluation)

            if idx < total - 1:
                if st.button("Next Question"):
                    st.session_state.current_question_index += 1
                    st.session_state.show_evaluation = False
                    st.rerun()
            else:
                st.success("🎉 You've completed all questions!")
                if st.button("Restart"):
                    st.session_state.current_question_index = 0
                    st.session_state.show_evaluation = False
                    st.rerun()
    else:
        st.info("No practice questions available yet!")
        st.write("To generate practice questions:")
        st.write("1. Go to 'Course Chatbot' mode")
        st.write("2. Select a course and ask at least 4 questions")
        st.write("3. Click 'Analyze Interactions' to generate practice questions")
        st.write("4. Return here to practice!")
import streamlit as st
import time
import os
import pandas as pd
import subprocess
import ast

# Set session state variables
if "start_time" not in st.session_state:
    st.session_state.start_time = None  # Timer starts after login
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "submitted_code" not in st.session_state:
    st.session_state.submitted_code = ""
if "time_taken" not in st.session_state:
    st.session_state.time_taken = "00:00.000"
if "execution_result" not in st.session_state:
    st.session_state.execution_result = ""
if "user_details" not in st.session_state:
    st.session_state.user_details = ""
if "code_input" not in st.session_state:
    st.session_state.code_input = ""
if "score" not in st.session_state:
    st.session_state.score = 0

# Custom CSS for modern UI
st.markdown(
    """
    <style>
        .title { color: #6A0DAD; font-size: 32px; font-weight: bold; text-align: center; padding: 10px 0; }
        .description { color: #374151; font-size: 18px; text-align: center; margin-bottom: 15px; }
        .timer-box { color: red; font-size: 20px; font-weight: bold; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True
)

# Sidebar Instructions
st.sidebar.header("📌 Instructions")
st.sidebar.markdown("""
1. Enter your full details.
2. Choose your programming language.
3. Start typing your code.
4. Timer will run from login till submission.
5. Your code will be evaluated, and you’ll see your score.
""")

# Title and description
st.markdown('<div class="title">👨‍💻 Blind Coding Challenge</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Write your code **without seeing it**! It will be revealed after submission.</div>', unsafe_allow_html=True)

# User details input
st.subheader("📝 Enter Your Details:")
user_details = st.text_input("Full Name, Roll No, Semester, Department:", key="user_details")

# Start timer when user enters details
if user_details and st.session_state.start_time is None:
    st.session_state.start_time = time.time()

# Timer Display (updates only if not submitted)
timer_placeholder = st.empty()

def format_time(elapsed_time):
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    milliseconds = int((elapsed_time % 1) * 1000)
    return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

# If not submitted, show the live timer
if st.session_state.start_time and not st.session_state.submitted:
    elapsed_time = time.time() - st.session_state.start_time
    formatted_time = format_time(elapsed_time)
    timer_placeholder.markdown(f'<div class="timer-box">⏳ Timer: {formatted_time}</div>', unsafe_allow_html=True)

# If submitted, show final recorded time
if st.session_state.submitted:
    timer_placeholder.markdown(f'<div class="timer-box">⏱️ Final Time: {st.session_state.time_taken}</div>', unsafe_allow_html=True)

# Language selection
st.subheader("🔍 Choose Your Programming Language:")
language = st.selectbox("Select language:", ["Python", "C"], key="language")

# Code input area (Hidden while typing)
st.markdown("""
    <style>
        textarea {
            color: transparent !important;
            text-shadow: 0 0 0 rgba(0,0,0,0);
            caret-color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

masked_input = st.text_area(
    "Enter your code (Hidden while typing!):",
    height=250,
    key="masked_code",
    help="Your code is hidden as you type."
)

# Store actual input separately
if masked_input:
    st.session_state.code_input = masked_input

# Function to evaluate code
def evaluate_code(code_text, language):
    score = 0
    feedback = []

    if language == "Python":
        try:
            exec(code_text)
            score += 50
        except Exception as e:
            feedback.append(f"Execution Error ❌: {str(e)}")

        try:
            tree = ast.parse(code_text)
            num_nodes = sum(1 for _ in ast.walk(tree))
            if num_nodes < 50:
                score += 20
            else:
                feedback.append("Code may be inefficient or too complex.")
        except Exception:
            feedback.append("Could not analyze efficiency.")

        if "for" in code_text or "while" in code_text:
            score += 10
        if "def" in code_text:
            score += 10

        if "\n    " in code_text or "    " in code_text:
            score += 10

    elif language == "C":
        with open("temp.c", "w") as f:
            f.write(code_text)
        compile_process = subprocess.run(["gcc", "temp.c", "-o", "temp.out"], capture_output=True, text=True)

        if compile_process.returncode == 0:
            score += 50
        else:
            feedback.append(f"Compilation Error ❌: {compile_process.stderr}")

        if len(code_text) < 1000:
            score += 20
        else:
            feedback.append("Code might be too long or inefficient.")

        if "for" in code_text or "while" in code_text:
            score += 10
        if "void" in code_text or "int main()" in code_text:
            score += 10  

        if "\n    " in code_text or "    " in code_text:
            score += 10  

    return score, feedback

# Submit button
if st.button("🚀 Submit Code") and not st.session_state.submitted:
    if not st.session_state.code_input.strip():
        st.error("Code cannot be empty!")
    elif not user_details.strip():
        st.error("Please enter your full details!")
    else:
        # Stop timer and record final time
        elapsed_time = time.time() - st.session_state.start_time
        formatted_time = format_time(elapsed_time)
        st.session_state.time_taken = formatted_time
        st.session_state.submitted = True

        # Evaluate code
        score, feedback = evaluate_code(st.session_state.code_input, language)
        st.session_state.submitted_code = st.session_state.code_input
        st.session_state.score = score

        # Display results
        st.success(f"🏆 Your Final Score: {score}/100")
        st.info(f"⏱️ Time Taken: {formatted_time}")

        if feedback:
            st.subheader("📝 Feedback:")
            for item in feedback:
                st.warning(item)

        # Save to leaderboard
        leaderboard_file = "leaderboard.csv"
        if os.path.exists(leaderboard_file):
            leaderboard_df = pd.read_csv(leaderboard_file)
        else:
            leaderboard_df = pd.DataFrame(columns=["Username", "Score", "Time Taken"])

        new_entry = pd.DataFrame([[user_details, score, formatted_time]], columns=["Username", "Score", "Time Taken"])
        leaderboard_df = pd.concat([leaderboard_df, new_entry], ignore_index=True)
        leaderboard_df.to_csv(leaderboard_file, index=False)

        # Refresh UI
        st.rerun()

# Show leaderboard
if st.session_state.submitted:
    st.sidebar.header("🏆 Leaderboard")
    leaderboard_df = pd.read_csv("leaderboard.csv")
    st.sidebar.dataframe(leaderboard_df.sort_values(by="Score", ascending=False), use_container_width=True)

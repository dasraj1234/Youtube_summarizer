# streamlit_youtube_summary_v3.py

# Import required libraries
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from openai import OpenAI
from dotenv import load_dotenv
import os

# ------------------- LOAD ENVIRONMENT VARIABLES -------------------
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# ------------------- HELPER FUNCTIONS -------------------
def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed_url.query).get('v', [None])[0]
    return None

def fetch_transcript(video_id):
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry['text'] for entry in transcript_list])

def generate_summary(prompt, transcript, model="gpt-3.5-turbo"):
    full_prompt = (
        f"{prompt}\n\n"
        f"Here is the transcript of the video:\n{transcript}\n\n"
        f"Generate a compact, descriptive summary with key points."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes video transcripts."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.5,
        max_tokens=800
    )
    return response.choices[0].message.content

def answer_question_from_summary(summary, question, model="gpt-3.5-turbo"):
    question_prompt = (
        f"Based on the following summary of a YouTube video, answer the question:\n\n"
        f"Summary: {summary}\n\n"
        f"Question: {question}\n"
        f"Answer clearly and concisely."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an assistant that answers questions based on video summaries."},
            {"role": "user", "content": question_prompt}
        ],
        temperature=0.5,
        max_tokens=400
    )
    return response.choices[0].message.content

# ------------------- STREAMLIT UI -------------------
st.title("📽️ YouTube Video Summarizer & Q&A")

st.markdown("""
This tool fetches the transcript of a YouTube video and uses **OpenAI GPT models**  
to generate a **clean and focused summary** with key points.  
You can also **ask questions** about the video content!
""")

youtube_url = st.text_input("🔗 YouTube Video URL")
user_prompt = st.text_area("✍️ Your Prompt", "Summarize this video for a blog post.")
selected_model = st.selectbox("🤖 Choose Model", ["gpt-3.5-turbo", "gpt-4"])

# Session state for summary and QA control
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "qa_active" not in st.session_state:
    st.session_state.qa_active = False
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# Generate summary logic
if st.button("🚀 Generate Summary"):
    if not youtube_url.strip():
        st.warning("Please enter a YouTube video URL.")
    else:
        try:
            video_id = extract_video_id(youtube_url)
            if not video_id:
                st.error("Invalid YouTube URL format.")
            else:
                with st.spinner("Fetching transcript and generating summary..."):
                    transcript = fetch_transcript(video_id)
                    st.session_state.summary = generate_summary(user_prompt, transcript, model=selected_model)
                    st.session_state.qa_active = True
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

# Display summary if available
if st.session_state.summary:
    st.subheader("📝 Summary")
    st.success(st.session_state.summary)

# Q&A interface
if st.session_state.qa_active and st.session_state.summary:
    st.markdown("---")
    st.subheader("❓ Ask a Question about the Video")
    with st.form(key="qa_form", clear_on_submit=True):
        user_question = st.text_input("Type your question here")
        submit_question = st.form_submit_button("💬 Get Answer")

    if submit_question and user_question.strip():
        with st.spinner("Thinking..."):
            answer = answer_question_from_summary(st.session_state.summary, user_question, model=selected_model)
            st.session_state.qa_history.append((user_question, answer))

    # Display all Q&A pairs
    for i, (q, a) in enumerate(reversed(st.session_state.qa_history)):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"**A{i+1}:** {a}")
        st.markdown("---")

    # Done button to end session
    if st.button("✅ Done"):
        st.session_state.qa_active = False
        st.session_state.qa_history.clear()
        st.success("Question & Answer session ended. You can generate a new summary if you like.")

st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, OpenAI, and YouTube Transcript API")
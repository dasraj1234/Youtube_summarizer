# streamlit_youtube_summary_v3.py

# Import required libraries
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from openai import OpenAI
from dotenv import load_dotenv
import os

# ------------------- LOAD ENVIRONMENT VARIABLES -------------------
# Load variables from .env file into the environment
load_dotenv()

# Retrieve the OpenAI API key from the environment
openai_api_key = os.getenv("OPENAI_API_KEY")

# Instantiate the OpenAI client using the API key
client = OpenAI(api_key=openai_api_key)

# ------------------- HELPER FUNCTIONS -------------------

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    Supports both standard (youtube.com) and short (youtu.be) URLs.
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed_url.query).get('v', [None])[0]
    return None

def fetch_transcript(video_id):
    """
    Fetches the full transcript of a YouTube video using its ID.
    Returns the transcript as a single concatenated string.
    """
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry['text'] for entry in transcript_list])

def generate_summary(prompt, transcript, model="gpt-3.5-turbo"):
    """
    Uses OpenAI Chat API to generate a compact summary from the transcript.
    """
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

# ------------------- STREAMLIT UI -------------------

# Streamlit app title
st.title("📽️ YouTube Video Summarizer")

# App description
st.markdown("""
This tool fetches the transcript of a YouTube video and uses **OpenAI GPT models**  
to generate a **clean and focused summary** with key points. Great for learning, notes, or writing blog content!
""")

# Input: YouTube video URL
youtube_url = st.text_input("🔗 YouTube Video URL")

# Input: User-defined prompt
user_prompt = st.text_area("✍️ Your Prompt", "Summarize this video for a blog post.")

# Dropdown to select OpenAI model
selected_model = st.selectbox("🤖 Choose Model", ["gpt-3.5-turbo", "gpt-4"])

# Button to trigger summary generation
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
                    summary = generate_summary(user_prompt, transcript, model=selected_model)
                st.subheader("📝 Summary")
                st.success(summary)
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, OpenAI, and YouTube Transcript API")

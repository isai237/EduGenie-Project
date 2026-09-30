import logging
import os
import time

import streamlit as st
from google import genai
from google.genai.errors import APIError


MODEL_NAME = "gemini-3.8-flash"
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 2
TRANSIENT_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
ANSWER_LENGTHS = {
    "Short": "Keep the response concise and focused, using only the key points.",
    "Medium": "Give a clear explanation with enough detail to understand the key ideas.",
    "Detailed": "Give a thorough explanation with structure, context, and useful examples.",
}


class MissingAPIKeyError(Exception):
    pass


class GeminiTemporarilyUnavailableError(Exception):
    pass


logger = logging.getLogger(__name__)


def build_prompt(messages, subject, learning_level, answer_length):
    conversation = "\n".join(
        f"{message['role'].capitalize()}: {message['content']}"
        for message in messages[:-1]
    )
    latest_question = messages[-1]["content"]
    history = f"Previous conversation:\n{conversation}\n\n" if conversation else ""

    return (
        "You are EduGenie, a patient and encouraging learning assistant. "
        "Help students understand ideas rather than merely memorize them. "
        "Explain difficult topics step by step when useful, use examples, and "
        "adapt your vocabulary to the student's level. If a request asks for "
        "a summary, exam answer, example, or practice questions, provide that format. "
        "Be accurate and say when you are uncertain.\n\n"
        f"Subject: {subject}\n"
        f"Student's learning level: {learning_level}\n"
        f"Answer length: {answer_length}. {ANSWER_LENGTHS[answer_length]}\n\n"
        f"{history}Student: {latest_question}\nEduGenie:"
    )


def generate_response(messages, subject, learning_level, answer_length):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "GEMINI_API_KEY is not set. Add it to your environment, then restart the app."
        )

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(messages, subject, learning_level, answer_length)
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            break
        except APIError as error:
            status_code = error.code
            if status_code not in TRANSIENT_HTTP_STATUS_CODES:
                logger.error("Gemini API request failed with HTTP status %s.", status_code)
                raise

            if attempt == MAX_RETRIES:
                logger.warning(
                    "Gemini API request still unavailable after %s retries (HTTP %s).",
                    MAX_RETRIES,
                    status_code,
                )
                raise GeminiTemporarilyUnavailableError(
                    "Gemini is temporarily busy. Please try again in a few moments."
                ) from None

            delay = INITIAL_RETRY_DELAY_SECONDS * (2 ** attempt)
            logger.warning(
                "Gemini API returned temporary HTTP status %s; retry %s/%s in %s seconds.",
                status_code,
                attempt + 1,
                MAX_RETRIES,
                delay,
            )
            time.sleep(delay)

    if not response.text:
        raise RuntimeError("Gemini returned an empty response. Please try again.")
    return response.text


st.set_page_config(
    page_title="EduGenie | Learning Assistant",
    page_icon="📘",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #24213f;
        --muted: #686781;
        --purple: #7057d9;
        --blue: #438ce2;
        --line: #e7e7f1;
        --paper: #f7f8fc;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(225, 222, 255, .45), transparent 34rem),
            var(--paper);
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0efff 0%, #f8f8ff 55%, #f5f8ff 100%);
        border-right: 1px solid rgba(93, 81, 170, .09);
    }
    [data-testid="stSidebar"] h2 {
        color: var(--ink);
        font-family: Georgia, 'Times New Roman', serif;
    }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.25rem 2.5rem;
        border-radius: 22px;
        color: #fff;
        background: linear-gradient(118deg, #5944bd 0%, #7659d8 48%, #4188d7 100%);
        box-shadow: 0 18px 40px rgba(74, 64, 156, .2);
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 240px;
        height: 240px;
        right: -68px;
        top: -138px;
        border: 1px solid rgba(255, 255, 255, .2);
        border-radius: 50%;
        box-shadow: 0 0 0 30px rgba(255, 255, 255, .06), 0 0 0 62px rgba(255, 255, 255, .04);
    }
    .hero-kicker {
        position: relative;
        z-index: 1;
        margin-bottom: .6rem;
        color: rgba(255, 255, 255, .82);
        font-size: .75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .12em;
    }
    .hero h1 {
        position: relative;
        z-index: 1;
        margin: 0;
        color: #fff;
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 3rem;
        line-height: 1.08;
    }
    .hero p {
        position: relative;
        z-index: 1;
        margin: .55rem 0 0;
        color: rgba(255, 255, 255, .9);
        font-size: 1.08rem;
    }
    .welcome { padding: 2rem 0 .5rem; }
    .welcome-label {
        color: var(--purple);
        font-size: .76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .1em;
    }
    .welcome h2 {
        margin: .35rem 0 .3rem;
        color: var(--ink);
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 1.8rem;
    }
    .welcome-copy { margin: 0 0 1.2rem; color: var(--muted); }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: .85rem;
    }
    .feature-card {
        min-height: 150px;
        padding: 1rem;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, .88);
        box-shadow: 0 5px 18px rgba(48, 45, 93, .045);
        transition: transform .18s ease, box-shadow .18s ease;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(48, 45, 93, .1);
    }
    .feature-icon { margin-bottom: .65rem; font-size: 1.55rem; }
    .feature-title { margin-bottom: .3rem; color: var(--ink); font-weight: 700; }
    .feature-copy { color: var(--muted); font-size: .83rem; line-height: 1.45; }
    .stButton > button {
        min-height: 2.8rem;
        border: 0;
        border-radius: 10px;
        color: #fff;
        background: linear-gradient(110deg, var(--purple), var(--blue));
        font-weight: 650;
        box-shadow: 0 5px 14px rgba(97, 78, 195, .16);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover {
        border: 0;
        color: #fff;
        box-shadow: 0 8px 18px rgba(97, 78, 195, .25);
        transform: translateY(-1px);
    }
    [data-testid="stChatMessage"] {
        margin-bottom: .75rem;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, .92);
        box-shadow: 0 4px 16px rgba(48, 45, 93, .04);
    }
    [data-testid="stChatInput"] {
        border: 1px solid #d9d7ed;
        border-radius: 14px;
        background: #fff;
        box-shadow: 0 5px 20px rgba(48, 45, 93, .06);
    }
    [data-testid="stChatInput"]:focus-within { border-color: var(--purple); }
    [data-testid="stSelectbox"] > div > div {
        border-color: #dedcf0;
        border-radius: 10px;
        background: rgba(255, 255, 255, .9);
    }
    @media (max-width: 900px) {
        .feature-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (max-width: 600px) {
        [data-testid="stMainBlockContainer"] { padding: 1rem 1rem 3rem; }
        .hero { padding: 1.6rem 1.35rem; border-radius: 17px; }
        .hero h1 { font-size: 2.35rem; }
        .hero p { font-size: 1rem; }
        .welcome { padding-top: 1.5rem; }
        .welcome h2 { font-size: 1.55rem; }
        .feature-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; }
        .feature-card { min-height: 140px; padding: .85rem; }
    }
    </style>
    <div class="hero">
        <div class="hero-kicker">Your personal study companion</div>
        <h1>EduGenie</h1>
        <p>Your AI-Powered Learning Assistant</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Learning settings")
    subject = st.selectbox(
        "Subject",
        ["General", "Mathematics", "Science", "Computer Science", "History", "Literature", "Languages"],
    )
    learning_level = st.selectbox(
        "Learning level",
        ["Beginner", "Middle school", "High school", "College", "Advanced"],
    )
    answer_length = st.selectbox("Answer length", list(ANSWER_LENGTHS))
    st.divider()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <section class="welcome">
            <div class="welcome-label">Welcome to your study space</div>
            <h2>Make a little progress on a big topic.</h2>
            <p class="welcome-copy">Choose a learning mode to get started, or ask anything in the chat below.</p>
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">📚</div>
                    <div class="feature-title">Explain Topics</div>
                    <div class="feature-copy">Unpack challenging ideas step by step.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📝</div>
                    <div class="feature-title">Exam Answers</div>
                    <div class="feature-copy">Shape clear, structured study answers.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💡</div>
                    <div class="feature-title">Examples</div>
                    <div class="feature-copy">Connect new ideas to useful examples.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-title">Practice Questions</div>
                    <div class="feature-copy">Test your understanding as you learn.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📖</div>
                    <div class="feature-title">Summarize</div>
                    <div class="feature-copy">Turn complex topics into key takeaways.</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("What would you like to learn today?"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking through that with you..."):
            try:
                answer = generate_response(
                    st.session_state.messages,
                    subject,
                    learning_level,
                    answer_length,
                )
            except MissingAPIKeyError as error:
                logger.error("Gemini credentials are not configured (%s).", type(error).__name__)
                st.error("EduGenie is not available right now. Please try again later.")
            except GeminiTemporarilyUnavailableError as error:
                st.error(str(error))
            except Exception as error:
                logger.error("Gemini request failed (%s).", type(error).__name__)
                st.error("EduGenie couldn't complete that request. Please try again later.")
            else:
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
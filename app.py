import os
import tempfile
import streamlit as st

from dotenv import load_dotenv

from main import run_pipeline
from core.rag_engine import ask_question


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- Global ---------- */

    .stApp {
        background: #0e1117;
        color: #f5f7fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {
        background: #11151d;
        border-right: 1px solid #262b36;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* ---------- Header ---------- */

    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }

    .app-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }

    .app-subtitle {
        color: #9ca3af;
        margin-top: 0.25rem;
        font-size: 0.95rem;
    }

    .status-badge {
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        background: #16231b;
        border: 1px solid #245c39;
        color: #67d391;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ---------- Cards ---------- */

    .info-card {
        background: #151922;
        border: 1px solid #262b36;
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .card-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8b95a7;
        font-weight: 700;
        margin-bottom: 0.65rem;
    }

    .metric-value {
        font-size: 1.15rem;
        font-weight: 600;
        color: #ffffff;
    }

    /* ---------- Section titles ---------- */

    .section-title {
        font-size: 1.25rem;
        font-weight: 650;
        color: #ffffff;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    /* ---------- Empty state ---------- */

    .empty-state {
        text-align: center;
        padding: 5rem 2rem;
        border: 1px dashed #303642;
        border-radius: 16px;
        background: #11151d;
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .empty-state-title {
        font-size: 1.4rem;
        font-weight: 650;
        color: #ffffff;
    }

    .empty-state-text {
        color: #8b95a7;
        margin-top: 0.5rem;
    }

    /* ---------- Buttons ---------- */

    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 2.6rem;
    }

    /* ---------- Text areas / inputs ---------- */

    textarea,
    input {
        border-radius: 9px !important;
    }

    /* ---------- Chat ---------- */

    [data-testid="stChatMessage"] {
        border-radius: 12px;
    }

    /* ---------- Divider ---------- */

    hr {
        border-color: #262b36;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "result" not in st.session_state:
    st.session_state.result = None

if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "processing" not in st.session_state:
    st.session_state.processing = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🎥 AI Video Assistant")

    st.caption(
        "Transform meetings and videos into searchable knowledge."
    )

    st.divider()

    st.markdown("### Input")

    source_type = st.radio(
        "Choose source",
        ["YouTube URL", "Local File"],
        index=0,
    )

    source = None
    uploaded_file = None

    if source_type == "YouTube URL":

        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
        )

        if youtube_url.strip():
            source = youtube_url.strip()

    else:

        uploaded_file = st.file_uploader(
            "Upload video or audio",
            type=[
                "mp4",
                "mkv",
                "avi",
                "mov",
                "webm",
                "mp3",
                "wav",
                "m4a",
                "flac",
            ],
            help="Upload a video or audio file for processing.",
        )

    st.markdown("### Language")

    language = st.selectbox(
        "Transcription language",
        ["English", "Hinglish"],
        index=0,
    )

    language_value = language.lower()

    st.divider()

    process_clicked = st.button(
        "🚀 Process Video",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.processing,
    )

    clear_clicked = st.button(
        "🗑️ Clear Session",
        use_container_width=True,
    )

    st.divider()

    st.caption("AI Video Assistant")
    st.caption("Whisper / Sarvam • Groq • Chroma")


# ============================================================
# CLEAR SESSION
# ============================================================

if clear_clicked:

    st.session_state.result = None
    st.session_state.rag_chain = None
    st.session_state.chat_history = []

    st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <div>
            <div class="app-title">AI Video Assistant</div>
            <div class="app-subtitle">
                Understand, summarize and query your video content.
            </div>
        </div>
        <div class="status-badge">
            ● System Ready
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PROCESS INPUT
# ============================================================

if process_clicked:

    if source_type == "YouTube URL":

        if not source:
            st.sidebar.error("Please enter a YouTube URL.")

        else:

            st.session_state.processing = True

            try:

                with st.status(
                    "Processing your video...",
                    expanded=True,
                ) as status:

                    st.write("🎵 Extracting and preparing audio...")
                    st.write("🎙️ Transcribing the audio...")
                    st.write("🧠 Generating summary and meeting insights...")
                    st.write("🔎 Building the searchable knowledge base...")

                    result = run_pipeline(
                        source=source,
                        language=language_value,
                    )

                    status.update(
                        label="Processing complete!",
                        state="complete",
                        expanded=False,
                    )

                st.session_state.result = result
                st.session_state.rag_chain = result["rag_chain"]
                st.session_state.chat_history = []

                st.success("Video processed successfully.")

            except Exception as e:

                st.error(
                    f"Processing failed: {str(e)}"
                )

            finally:

                st.session_state.processing = False


    else:

        if uploaded_file is None:

            st.sidebar.error("Please upload a video or audio file.")

        else:

            st.session_state.processing = True

            temp_path = None

            try:

                suffix = os.path.splitext(
                    uploaded_file.name
                )[1]

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                ) as temp_file:

                    temp_file.write(
                        uploaded_file.getbuffer()
                    )

                    temp_path = temp_file.name

                with st.status(
                    "Processing your file...",
                    expanded=True,
                ) as status:

                    st.write("🎵 Extracting and preparing audio...")
                    st.write("🎙️ Transcribing the audio...")
                    st.write("🧠 Generating summary and meeting insights...")
                    st.write("🔎 Building the searchable knowledge base...")

                    result = run_pipeline(
                        source=temp_path,
                        language=language_value,
                    )

                    status.update(
                        label="Processing complete!",
                        state="complete",
                        expanded=False,
                    )

                st.session_state.result = result
                st.session_state.rag_chain = result["rag_chain"]
                st.session_state.chat_history = []

                st.success("File processed successfully.")

            except Exception as e:

                st.error(
                    f"Processing failed: {str(e)}"
                )

            finally:

                st.session_state.processing = False

                if temp_path and os.path.exists(temp_path):

                    try:
                        os.remove(temp_path)

                    except OSError:
                        pass


# ============================================================
# EMPTY STATE
# ============================================================

if st.session_state.result is None:

    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">🎬</div>
            <div class="empty-state-title">
                No video processed yet
            </div>
            <div class="empty-state-text">
                Add a YouTube URL or upload a video/audio file
                from the sidebar to get started.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# RESULT
# ============================================================

result = st.session_state.result


# ============================================================
# TITLE
# ============================================================

st.markdown(
    f"""
    <div class="info-card">
        <div class="card-title">Meeting Title</div>
        <div class="metric-value">
            {result["title"]}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">📝 Summary</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

    st.markdown(result["summary"])


# ============================================================
# INSIGHTS
# ============================================================

st.markdown(
    '<div class="section-title">📊 Meeting Insights</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)


with col1:

    st.markdown("### ✅ Action Items")

    with st.container(border=True):

        st.markdown(
            result["action_items"]
        )


with col2:

    st.markdown("### 🎯 Key Decisions")

    with st.container(border=True):

        st.markdown(
            result["key_decisions"]
        )


with col3:

    st.markdown("### ❓ Open Questions")

    with st.container(border=True):

        st.markdown(
            result["open_questions"]
        )


# ============================================================
# TRANSCRIPT
# ============================================================

st.markdown(
    '<div class="section-title">📜 Transcript</div>',
    unsafe_allow_html=True,
)

with st.expander("View full transcript"):

    st.text_area(
        "Transcript",
        value=result["transcript"],
        height=450,
        label_visibility="collapsed",
    )


# ============================================================
# ASK QUESTIONS
# ============================================================

st.markdown(
    '<div class="section-title">💬 Ask About This Video</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Ask questions based on the processed meeting transcript."
)


# Display previous messages

for message in st.session_state.chat_history:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# Chat input

question = st.chat_input(
    "Ask something about this video..."
)


if question:

    # User message

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    # Assistant response

    with st.chat_message("assistant"):

        with st.spinner("Searching the transcript..."):

            try:

                answer = ask_question(
                    st.session_state.rag_chain,
                    question,
                )

                st.markdown(answer)

            except Exception as e:

                answer = (
                    "Sorry, I couldn't answer that question. "
                    f"Error: {str(e)}"
                )

                st.error(answer)


    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )
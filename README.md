# 🎥 AI Video Assistant

### AI-Powered Video Summarization, Meeting Insights & Intelligent Question Answering

AI Video Assistant is an AI-powered web application that converts video and audio content into meaningful, structured information. It allows users to generate summaries, extract important meeting insights, and ask questions about video content using Retrieval-Augmented Generation (RAG).

Built using **Python, Streamlit, Whisper, Groq, LangChain, and ChromaDB**, the application helps users understand lengthy videos without manually reviewing the entire content.

## 🚀 Key Features

- **YouTube Video Processing:** Extracts and processes audio from YouTube videos.
- **Audio/Video Transcription:** Converts spoken content into text using Whisper and supported speech-to-text services.
- **AI-Powered Summarization:** Generates concise summaries using LLMs with chunk-based map-reduce summarization.
- **Meeting Insights Extraction:** Automatically identifies action items, key decisions, and open questions.
- **Intelligent Question Answering:** Allows users to ask questions about the processed video using RAG.
- **Semantic Search:** Retrieves relevant transcript sections using embeddings and ChromaDB.
- **Interactive Interface:** Provides a user-friendly Streamlit interface.
- **Error Handling:** Includes retry mechanisms and fallback handling for unreliable API responses.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Streamlit | Web application interface |
| Whisper | Speech-to-text transcription |
| Sarvam AI | Supported transcription integration |
| Groq API | Fast LLM inference |
| GPT-OSS 20B | Text summarization and information extraction |
| LangChain | LLM integration and RAG pipeline |
| ChromaDB | Vector database for semantic search |
| Embeddings | Numerical representations of transcript chunks |
| yt-dlp | YouTube audio downloading |
| FFmpeg / Pydub | Audio processing and conversion |
| GitHub | Version control |
| Streamlit Community Cloud | Application deployment |

## ⚙️ How It Works

The application follows this workflow:

**Step 1 — Video Input**

The user provides a YouTube URL or supported media input.

**Step 2 — Audio Processing**

The application extracts audio and prepares it for transcription.

**Step 3 — Speech-to-Text**

Whisper or the configured transcription service converts the audio into a text transcript.

**Step 4 — AI Summarization**

The transcript is divided into smaller chunks. Each chunk is summarized, and the partial summaries are combined to produce a final summary.

**Step 5 — Meeting Insights**

The LLM analyzes the transcript and extracts:

- Action items with tasks, owners, and deadlines when available
- Key decisions made during the discussion
- Open questions and unresolved issues

**Step 6 — RAG Pipeline**

The transcript is divided into chunks, converted into embeddings, and indexed in ChromaDB.

**Step 7 — Intelligent Question Answering**

When the user asks a question, the application retrieves relevant transcript chunks and uses them as context for generating an answer.

### Architecture

```text
            YouTube URL / Media Input
                       |
                       v
                Audio Extraction
                       |
                       v
               Audio Processing
                       |
                       v
                Transcription
                       |
                       v
                Text Transcript
                       |
          +------------+------------+
          |            |            |
          v            v            v
     Summarization   Meeting       RAG
                     Insights     Pipeline
          |            |            |
          v            v            v
       Summary     Action Items   Embeddings
                   Decisions          |
                   Questions          v
                                  ChromaDB
                                      |
                                      v
                               Relevant Chunks
                                      |
                                      v
                              LLM-Based Answers
```

## 📂 Project Structure

```text
AI-Video-Assisstant/
|
|-- app.py
|-- main.py
|
|-- core/
|   |-- transcriber.py
|   |-- summarizer.py
|   |-- extractor.py
|   |-- rag_engine.py
|
|-- utils/
|   |-- audio_processor.py
|
|-- requirements.txt
|-- README.md
```

*The structure above highlights the main application components.*

## 💻 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Bishal-20/AI-Video-Assisstant.git
cd AI-Video-Assisstant
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Audio processing may also require FFmpeg and other system dependencies.

### 4. Configure API Keys

Create a `.env` file in the project root and add the API credentials required by your configuration.

```env
GROQ_API_KEY=your_groq_api_key
```

If using Sarvam AI or another external transcription service, configure its credentials according to the project's transcription setup.

**Never commit API keys or your `.env` file to GitHub.**

### 5. Run the Application

```bash
streamlit run app.py
```

Open the local Streamlit URL displayed in your terminal.

## 📖 How to Use

1. Launch the Streamlit application.
2. Provide a YouTube video URL or supported media input.
3. Select the available transcription language or mode.
4. Start processing and wait for transcription and AI analysis to finish.
5. Read the generated title, summary, and meeting insights.
6. Ask questions about the video using the AI-powered chat interface.

## 🧠 Understanding the RAG Implementation

Retrieval-Augmented Generation (RAG) combines information retrieval with large language models to produce context-aware responses.

In this project:

1. The transcript is divided into smaller text chunks.
2. An embedding model converts the chunks into numerical vectors.
3. ChromaDB stores and indexes the embeddings.
4. The user's question is used to retrieve semantically relevant transcript chunks.
5. The retrieved text is provided to the LLM to generate an answer.

This reduces the need to send the entire transcript for every question and helps ground answers in the video's content.

## ⚡ Challenges and Solutions

### 1. Processing Long Transcripts

**Challenge:** Long transcripts can exceed practical LLM input limits and increase token usage.

**Solution:** Implemented chunk-based map-reduce summarization to process transcripts in smaller sections.

### 2. Inconsistent LLM Responses

**Challenge:** Some LLM requests returned empty or incomplete responses, resulting in missing summaries or meeting insights.

**Solution:** Improved response validation, retry handling, debugging logs, and fallback behavior to make processing more reliable.

### 3. Retrieving Relevant Video Information

**Challenge:** Sending an entire transcript for every question is inefficient.

**Solution:** Implemented RAG with embeddings and ChromaDB to retrieve relevant transcript sections.

## ⚠️ Current Limitations

- Processing time increases for longer videos.
- Transcription accuracy depends on audio quality, language, and background noise.
- AI-generated summaries may occasionally omit important details.
- Meeting-insight extraction may be less accurate when speakers, owners, or deadlines are unclear.
- Some extraction operations use a limited portion of the transcript.
- RAG reduces hallucinations but cannot guarantee completely accurate answers.
- External API availability and rate limits can affect performance.

## 🔮 Future Improvements

- Speaker diarization to identify different speakers
- Timestamp-based navigation to important video segments
- Exporting summaries and meeting insights as PDF
- Improved handling of very long transcripts
- More detailed multilingual transcription support
- Background processing and progress tracking
- Improved citation of transcript sections in generated answers

## 🎯 Learning Outcomes

Through this project, I gained practical experience in:

- Integrating LLM APIs into Python applications
- Building AI-powered text-processing pipelines
- Implementing Retrieval-Augmented Generation
- Working with embeddings and vector databases
- Processing audio and generating transcriptions
- Designing interactive applications with Streamlit
- Handling API failures, rate limits, and incomplete model responses
- Debugging and deploying AI applications

## 👨‍💻 Author

**Bishal Barman**

B.Tech — Computer Science and Engineering

[GitHub](https://github.com/Bishal-20)

---

⭐ If you find this project useful, consider giving the repository a star!

AI Video Assistant
An AI-powered application that turns video and audio content into searchable, actionable information. It transcribes speech, generates meeting summaries, identifies action items and decisions, and lets users ask questions about the content using retrieval-augmented generation (RAG).

Built with Python, Streamlit, Whisper, Groq, LangChain, and ChromaDB.
Features
- YouTube and file input: Process supported YouTube links and local media files.
- Speech-to-text: Transcribe audio using Whisper; the project also includes a Sarvam AI transcription path for supported language workflows.
- AI summaries: Generate summaries of longer transcripts using a chunk-based map-reduce approach.
- Meeting insights: Extract action items (including owners and deadlines when mentioned), key decisions, and open questions.
- Ask questions about a video: Retrieve relevant transcript passages with RAG and generate context-aware answers.
- Interactive interface: View transcripts, summaries, insights, and answers in a Streamlit app.
How It Works
YouTube URL / Media File
          |
          v
  Audio Extraction & Chunking
          |
          v
  Speech-to-Text Transcription
          |
          v
        Transcript
          |
          +----------------------+-----------------------+
          |                      |                       |
          v                      v                       v
  AI Summarization      Meeting Insight Extraction   Text Chunking
          |                      |                       |
          v                      v                       v
       Summary         Actions / Decisions /         Embeddings
                        Open Questions                 |
                                                      v
                                                   ChromaDB
                                                      |
                                               User Question
                                                      |
                                                      v
                                              Relevant Chunks
                                                      |
                                                      v
                                                LLM Answer
Processing pipeline
1. The app accepts a video URL or supported file.
2. The audio processor downloads or extracts audio and prepares it for transcription.
3. A speech-to-text model produces a transcript.
4. A Groq-hosted language model generates a title, summary, and structured meeting insights.
5. The transcript is divided into chunks and indexed in ChromaDB for semantic retrieval.
6. When the user asks a question, relevant chunks are retrieved and supplied as context to the language model.
Tech Stack
Technology	Purpose
Python	Application and processing logic
Streamlit	Web interface
yt-dlp / pydub	YouTube audio download and audio processing
Whisper	Speech transcription
Sarvam AI	Additional transcription workflow
Groq (openai/gpt-oss-20b)	LLM inference for summaries and insights
LangChain	Prompt chains and RAG orchestration
ChromaDB	Vector storage and similarity search


Getting Started
Prerequisites
- Python installed
- Git
- FFmpeg available on your system for audio conversion
- API credentials for the services enabled in your configuration
Installation
git clone https://github.com/Bishal-20/AI-Video-Assisstant.git
cd AI-Video-Assisstant
python -m venv .venv
Activate the environment:

Windows (PowerShell)
.venv\Scripts\Activate.ps1
macOS / Linux
source .venv/bin/activate
Install dependencies:
pip install -r requirements.txt
Environment variables
Create a .env file in the project root for local development and provide the credentials required by the transcription and LLM services you use:
GROQ_API_KEY=your_groq_api_key
Additional keys or YouTube access configuration may be required depending on the selected transcription method and deployment environment. Check the corresponding modules before running.

Never commit API keys, .env files, or browser cookies to GitHub. On Streamlit Community Cloud, store secrets in the app's Secrets settings.
Run the app
streamlit run app.py
Open the local Streamlit URL shown in your terminal, supply a supported YouTube URL or media file, and start processing. Once the transcript is ready, explore the summary, meeting insights, and transcript-based Q&A.
Reliability and Limitations
- LLM responses can occasionally be empty or incomplete; the project uses retry and fallback handling in parts of the generation pipeline.
- Very long transcripts require chunking. Summaries may omit details, so users should consult the transcript for critical information.
- The current meeting-insight extraction uses a limited portion of the transcript, so insights from later sections of long meetings may be missed.
- RAG retrieves relevant context but cannot guarantee that every generated answer is correct.
- Processing time depends on video length, transcription, model/API latency, and hosting resources.
- YouTube processing may depend on upstream platform changes and access restrictions.
Future Improvements
- Cover entire long transcripts when extracting meeting insights.
- Add timestamps and clickable references to relevant video segments.
- Add speaker diarization and speaker-linked action items.
- Provide export options for summaries and meeting notes.
- Add stronger response validation and evaluation on different meeting types.
What I Learned
This project provided hands-on experience integrating speech recognition, hosted LLMs, prompt engineering, text chunking, semantic search, vector databases, RAG, Streamlit deployment, and debugging unreliable API responses.

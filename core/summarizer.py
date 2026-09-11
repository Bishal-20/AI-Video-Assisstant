from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os
import time


# ============================================================
# Groq LLM
# ============================================================

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set in the environment."
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.3,
        max_tokens=500,
        api_key=api_key,
    )


# ============================================================
# Safe Groq request with retry
# ============================================================

def invoke_with_retry(chain, data, max_retries=4):
    """
    Invoke a Groq chain with retry handling for rate limits.
    """

    for attempt in range(max_retries):
        try:
            return chain.invoke(data)

        except Exception as e:
            error_text = str(e)

            if "429" not in error_text and "rate_limit" not in error_text:
                raise

            wait_time = 3 * (attempt + 1)

            print(
                f"Groq rate limit reached. "
                f"Waiting {wait_time} seconds..."
            )

            time.sleep(wait_time)

    raise RuntimeError(
        "Groq rate limit persisted after multiple retries."
    )


# ============================================================
# Split transcript
# ============================================================

def split_transcript(transcript: str) -> list:
    """
    Split transcript into manageable chunks.

    Smaller chunks reduce Groq token usage.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2200,
        chunk_overlap=100,
    )

    return splitter.split_text(transcript)


# ============================================================
# Summarize transcript
# ============================================================

def summarize(transcript: str) -> str:
    """
    Generate a concise meeting summary.

    Uses map-reduce style summarization while keeping
    requests small enough for Groq's free-tier limits.
    """

    llm = get_llm()

    # --------------------------------------------------------
    # Step 1: Summarize each transcript chunk
    # --------------------------------------------------------

    map_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a meeting summarizer. "
                "Summarize the transcript portion briefly. "
                "Keep only important topics, decisions, "
                "and relevant discussion points. "
                "Use concise bullet points."
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)

    chunk_summaries = []

    for i, chunk in enumerate(chunks):

        print(
            f"Summarizing chunk {i + 1}/{len(chunks)}..."
        )

        summary = invoke_with_retry(
            map_chain,
            {"text": chunk}
        )

        chunk_summaries.append(summary)

        # Give Groq time to recover from TPM limits
        if i < len(chunks) - 1:
            time.sleep(2)


    # --------------------------------------------------------
    # Step 2: Combine chunk summaries
    # --------------------------------------------------------

    combined = "\n\n".join(chunk_summaries)

    # Prevent the final request from becoming too large
    combined = combined[:7000]

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. "
                "Combine the provided partial summaries into "
                "one concise professional meeting summary. "
                "Use bullet points. "
                "Focus on the most important information. "
                "Do not repeat points."
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    combined_chain = (
        combined_prompt
        | llm
        | StrOutputParser()
    )

    return invoke_with_retry(
        combined_chain,
        {"text": combined}
    )


# ============================================================
# Generate meeting title
# ============================================================

def generate_title(transcript: str) -> str:
    """
    Generate a short professional meeting title.
    """

    llm = get_llm()

    title_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Based on the meeting transcript, generate "
                "a short professional meeting title. "
                "Maximum 8 words. "
                "Return only the title."
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    title_chain = (
        title_prompt
        | llm
        | StrOutputParser()
    )

    # Only send a small portion of the transcript
    text = transcript[:1500]

    return invoke_with_retry(
        title_chain,
        {"text": text}
    )
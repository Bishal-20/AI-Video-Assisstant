from dotenv import load_dotenv

from utils.audio_processor import process_input

from core.transcriber import transcribe_all

from core.summarizer import (
    summarize,
    generate_title,
)

from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)

from core.rag_engine import build_rag_chain


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline(
    source: str,
    language: str = "english",
) -> dict:

    # --------------------------------------------------------
    # 1. Process input
    # --------------------------------------------------------

    chunks = process_input(source)

    if not chunks:
        raise RuntimeError(
            "No audio chunks were generated."
        )


    # --------------------------------------------------------
    # 2. Transcription
    # --------------------------------------------------------

    transcript = transcribe_all(
        chunks,
        language,
    )

    if not transcript.strip():
        raise RuntimeError(
            "Transcription returned empty text."
        )


    # --------------------------------------------------------
    # 3. Generate title
    # --------------------------------------------------------
    print("Generating title...")
    title = generate_title(
        transcript
    )
    print("Title generated.")


    # --------------------------------------------------------
    # 4. Generate summary
    # --------------------------------------------------------

    summary = summarize(
        transcript
    )


    # --------------------------------------------------------
    # 5. Extract action items
    # --------------------------------------------------------

    action_items = extract_action_items(
        transcript
    )


    # --------------------------------------------------------
    # 6. Extract decisions
    # --------------------------------------------------------

    decisions = extract_key_decisions(
        transcript
    )


    # --------------------------------------------------------
    # 7. Extract questions
    # --------------------------------------------------------

    questions = extract_questions(
        transcript
    )


    # --------------------------------------------------------
    # 8. Build RAG system
    # --------------------------------------------------------

    rag_chain = build_rag_chain(
        transcript
    )


    # --------------------------------------------------------
    # Return everything required by UI
    # --------------------------------------------------------

    return {
        "title": title.strip(),
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ============================================================
# OPTIONAL CLI TEST
# ============================================================

if __name__ == "__main__":

    source = input(
        "Enter YouTube URL or local file path: "
    ).strip()

    language = input(
        "Language (english/hinglish): "
    ).strip() or "english"

    result = run_pipeline(
        source,
        language,
    )

    print("\n")
    print("=" * 60)
    print("TITLE")
    print("=" * 60)
    print(result["title"])

    print("\n")
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(result["summary"])

    print("\n")
    print("=" * 60)
    print("ACTION ITEMS")
    print("=" * 60)
    print(result["action_items"])

    print("\n")
    print("=" * 60)
    print("KEY DECISIONS")
    print("=" * 60)
    print(result["key_decisions"])

    print("\n")
    print("=" * 60)
    print("OPEN QUESTIONS")
    print("=" * 60)
    print(result["open_questions"])

    print("\n")
    print("=" * 60)
    print("TRANSCRIPT")
    print("=" * 60)
    print(result["transcript"])
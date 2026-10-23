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

    print("DEBUG: Starting action-item extraction", flush=True)

    action_items = extract_action_items(transcript)

    print("DEBUG: Action-item extraction finished", flush=True)
    print("DEBUG: Action items empty?", not bool(action_items), flush=True)


    # --------------------------------------------------------
    # 6. Extract decisions
    # --------------------------------------------------------

    print("DEBUG: Starting decision extraction", flush=True)

    decisions = extract_key_decisions(transcript)

    print("DEBUG: Decision extraction finished", flush=True)
    print("DEBUG: Decisions empty?", not bool(decisions), flush=True)


    # --------------------------------------------------------
    # 7. Extract questions
    # --------------------------------------------------------

    print("DEBUG: Starting open-question extraction", flush=True)

    questions = extract_questions(transcript)

    print("DEBUG: Open-question extraction finished", flush=True)
    print("DEBUG: Questions empty?", not bool(questions), flush=True)


    # --------------------------------------------------------
    # 8. Build RAG system
    # --------------------------------------------------------

    print("DEBUG: Starting RAG chain creation", flush=True)

    rag_chain = build_rag_chain(transcript)

    print("DEBUG: RAG chain creation finished", flush=True)


    # --------------------------------------------------------
    # Return everything required by UI
    # --------------------------------------------------------
    
    # --------------------------------------------------------
    # DEBUG: Inspect actual results before sending to the UI
    # --------------------------------------------------------

    print("\n========== PIPELINE OUTPUT CHECK ==========", flush=True)

    for name, value in [
        ("SUMMARY", summary),
        ("ACTION ITEMS", action_items),
        ("KEY DECISIONS", decisions),
        ("OPEN QUESTIONS", questions),
    ]:
        value = value if isinstance(value, str) else str(value)

        print(
            f"\n{name}: length={len(value)}",
            flush=True,
        )
        print(
            f"{name} preview: {value[:500]!r}",
            flush=True,
        )

    print("\n========== END PIPELINE OUTPUT CHECK ==========", flush=True)


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

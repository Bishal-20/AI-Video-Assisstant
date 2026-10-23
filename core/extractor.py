
# ============================================================
# Actionable Items, Decisions, Questions
# ============================================================

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
        temperature=0.2,
        max_tokens=2500,
        api_key=api_key,
    )


# ============================================================
# Validate Groq response
# ============================================================

def is_valid_response(result: str) -> bool:
    """Check that Groq returned text containing all sections."""

    if not result or not result.strip():
        return False

    response = result.upper()

    required_sections = [
        "ACTION ITEMS:",
        "KEY DECISIONS:",
        "OPEN QUESTIONS:",
    ]

    return all(
        section in response
        for section in required_sections
    )


# ============================================================
# Safe Groq request with retry
# ============================================================

def invoke_with_retry(chain, data, max_retries=4):
    """
    Retry rate-limited, empty, or incomplete responses.
    """

    for attempt in range(max_retries):
        try:
            result = chain.invoke(data)

            if is_valid_response(result):
                return result.strip()

            print(
                f"Groq returned an empty or incomplete response "
                f"(attempt {attempt + 1}/{max_retries}).",
                flush=True,
            )

        except Exception as e:
            error_text = str(e).lower()

            is_rate_limit = (
                "429" in error_text
                or "rate_limit" in error_text
                or "rate limit" in error_text
            )

            if not is_rate_limit:
                raise

            print(
                f"Groq rate limit reached "
                f"(attempt {attempt + 1}/{max_retries}).",
                flush=True,
            )

        if attempt < max_retries - 1:
            wait_time = 3 * (attempt + 1)

            print(
                f"Retrying in {wait_time} seconds...",
                flush=True,
            )

            time.sleep(wait_time)

    raise RuntimeError(
        "Groq did not return a complete extraction response "
        "after multiple attempts."
    )


# ============================================================
# Combined extraction
# ============================================================

def extract_all(transcript: str) -> dict:
    """
    Extract all three meeting-insight sections
    using one Groq request.
    """

    if not transcript or not transcript.strip():
        return {
            "action_items": "No transcript available for extraction.",
            "key_decisions": "No transcript available for extraction.",
            "open_questions": "No transcript available for extraction.",
        }

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an expert meeting analyst.

Analyze the supplied meeting transcript.

Extract:

1. ACTION ITEMS
For each task, include:
- Task
- Owner
- Deadline

If the owner or deadline is not mentioned, write:
Not specified

2. KEY DECISIONS
List decisions actually made during the meeting.
Do not include suggestions that were not agreed upon.

3. OPEN QUESTIONS
List unresolved questions, pending issues, or topics
requiring follow-up.

Return all three headings exactly as written below,
even if a section has no relevant information:

ACTION ITEMS:
1. Task: ...
   Owner: ...
   Deadline: ...

KEY DECISIONS:
1. ...

OPEN QUESTIONS:
1. ...

For an empty section, write:
None found.

Be concise. Do not invent information.
""",
            ),
            ("human", "{text}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    # Keep the existing input limit to control token usage.
    text = transcript[:12000]

    try:
        result = invoke_with_retry(
            chain,
            {"text": text},
        )

        print(
            "\n========== RAW EXTRACTION RESPONSE ==========",
            flush=True,
        )
        print(repr(result), flush=True)
        print(
            "========== END EXTRACTION RESPONSE ==========\n",
            flush=True,
        )

        parsed = parse_extraction_result(result)

        print(
            "Extraction completed. "
            f"Action items: {bool(parsed['action_items'])}, "
            f"Decisions: {bool(parsed['key_decisions'])}, "
            f"Questions: {bool(parsed['open_questions'])}",
            flush=True,
        )

        return parsed

    except Exception as e:
        print(
            f"ERROR: Meeting-insight extraction failed: {e}",
            flush=True,
        )

        message = (
            "Could not generate this section. "
            "Please process the video again."
        )

        return {
            "action_items": message,
            "key_decisions": message,
            "open_questions": message,
        }


# ============================================================
# Parse combined result
# ============================================================

def parse_extraction_result(result: str) -> dict:
    """Split the Groq response into three sections."""

    if not result:
        result = ""

    # Normalize heading capitalization.
    result = result.replace(
        "Action Items:", "ACTION ITEMS:"
    ).replace(
        "Key Decisions:", "KEY DECISIONS:"
    ).replace(
        "Open Questions:", "OPEN QUESTIONS:"
    )

    action_items = "No action items found."
    decisions = "No key decisions found."
    questions = "No open questions found."

    if "ACTION ITEMS:" in result:
        section = result.split("ACTION ITEMS:", 1)[1]

        if "KEY DECISIONS:" in section:
            section = section.split("KEY DECISIONS:", 1)[0]

        section = section.strip()

        if section and section.lower() != "none found.":
            action_items = section

    if "KEY DECISIONS:" in result:
        section = result.split("KEY DECISIONS:", 1)[1]

        if "OPEN QUESTIONS:" in section:
            section = section.split("OPEN QUESTIONS:", 1)[0]

        section = section.strip()

        if section and section.lower() != "none found.":
            decisions = section

    if "OPEN QUESTIONS:" in result:
        section = result.split("OPEN QUESTIONS:", 1)[1]
        section = section.strip()

        if section and section.lower() != "none found.":
            questions = section

    return {
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
    }


# ============================================================
# Cached extraction
# ============================================================

_cached_extraction = None
_cached_transcript = None


def _get_cached_extraction(transcript: str) -> dict:
    """Run extraction only once for the same transcript."""

    global _cached_extraction
    global _cached_transcript

    if (
        _cached_extraction is not None
        and _cached_transcript == transcript
    ):
        return _cached_extraction

    _cached_extraction = extract_all(transcript)
    _cached_transcript = transcript

    return _cached_extraction


# ============================================================
# Public functions used by main.py
# ============================================================

def extract_action_items(transcript: str) -> str:
    result = _get_cached_extraction(transcript)
    return result["action_items"]


def extract_key_decisions(transcript: str) -> str:
    result = _get_cached_extraction(transcript)
    return result["key_decisions"]


def extract_questions(transcript: str) -> str:
    result = _get_cached_extraction(transcript)
    return result["open_questions"]

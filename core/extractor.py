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
        max_tokens=700,
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

            if (
                "429" not in error_text
                and "rate_limit" not in error_text
            ):
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
# Combined extraction
# ============================================================

def extract_all(transcript: str) -> dict:
    """
    Extract action items, key decisions and open questions
    using ONE Groq request.
    """

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an expert meeting analyst.

Analyze the meeting transcript and extract:

1. ACTION ITEMS
For each action item provide:
- Task
- Owner
- Deadline

If an owner or deadline is not mentioned, write:
Not specified

2. KEY DECISIONS
List the important decisions that were actually made
during the meeting.

3. OPEN QUESTIONS
List unresolved questions, pending issues, or topics
that require follow-up.

Use exactly this format:

ACTION ITEMS:
1. Task: ...
   Owner: ...
   Deadline: ...

2. Task: ...
   Owner: ...
   Deadline: ...

KEY DECISIONS:
1. ...

2. ...

OPEN QUESTIONS:
1. ...

2. ...

If a section has nothing relevant, write:
None found.

Be concise and do not invent information.
"""
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    # Limit the input size to reduce TPM usage.
    # Keep the beginning of the transcript where possible.
    text = transcript[:12000]

    result = invoke_with_retry(
        chain,
        {"text": text}
    )

    return parse_extraction_result(result)


# ============================================================
# Parse combined result
# ============================================================

def parse_extraction_result(result: str) -> dict:
    """
    Convert the combined Groq response into separate sections.
    """

    action_items = "No action items found."
    decisions = "No key decisions found."
    questions = "No open questions found."

    if "ACTION ITEMS:" in result:

        action_section = result.split(
            "ACTION ITEMS:",
            1
        )[1]

        if "KEY DECISIONS:" in action_section:
            action_section = action_section.split(
                "KEY DECISIONS:",
                1
            )[0]

        action_section = action_section.strip()

        if (
            action_section
            and action_section.lower() != "none found."
        ):
            action_items = action_section


    if "KEY DECISIONS:" in result:

        decision_section = result.split(
            "KEY DECISIONS:",
            1
        )[1]

        if "OPEN QUESTIONS:" in decision_section:
            decision_section = decision_section.split(
                "OPEN QUESTIONS:",
                1
            )[0]

        decision_section = decision_section.strip()

        if (
            decision_section
            and decision_section.lower() != "none found."
        ):
            decisions = decision_section


    if "OPEN QUESTIONS:" in result:

        question_section = result.split(
            "OPEN QUESTIONS:",
            1
        )[1]

        question_section = question_section.strip()

        if (
            question_section
            and question_section.lower() != "none found."
        ):
            questions = question_section


    return {
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
    }


# ============================================================
# Public functions
# ============================================================
#
# These functions are kept so main.py does NOT need to change.
#
# ============================================================

_cached_extraction = None
_cached_transcript = None


def _get_cached_extraction(transcript: str) -> dict:
    """
    Run extraction only once for the same transcript.
    """

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


def extract_action_items(transcript: str) -> str:
    result = _get_cached_extraction(transcript)

    return result["action_items"]


def extract_key_decisions(transcript: str) -> str:
    result = _get_cached_extraction(transcript)

    return result["key_decisions"]


def extract_questions(transcript: str) -> str:
    result = _get_cached_extraction(transcript)

    return result["open_questions"]
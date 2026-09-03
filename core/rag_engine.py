import os

from langchain_mistralai import ChatMistralAI

from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
)

from core.vector_store import (
    build_vector_store,
    load_vector_store,
    get_retriever,
)


# ============================================================
# LLM
# ============================================================

def get_llm():

    api_key = os.getenv(
        "MISTRAL_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "MISTRAL_API_KEY is not set in the environment."
        )

    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=api_key,
        temperature=0.3,
    )


# ============================================================
# DOCUMENT FORMATTER
# ============================================================

def format_docs(docs):

    return "\n\n".join(
        doc.page_content
        for doc in docs
    )


# ============================================================
# RAG PROMPT
# ============================================================

RAG_SYSTEM_PROMPT = """
You are an expert meeting assistant.

Answer the user's question based ONLY on the meeting
transcript context provided below.

If the answer is not found in the context, say exactly:

"I could not find this information in the meeting transcript."

Do not invent information.

Always be concise and precise.

If quoting someone, mention that it is a quote.

Context from meeting transcript:

{context}
"""


# ============================================================
# BUILD RAG CHAIN
# ============================================================

def build_rag_chain(
    transcript: str,
):

    if not transcript.strip():

        raise ValueError(
            "Cannot build RAG chain from empty transcript."
        )


    # --------------------------------------------------------
    # Build vector store
    # --------------------------------------------------------

    vector_store = build_vector_store(
        transcript
    )


    # --------------------------------------------------------
    # Retriever
    # --------------------------------------------------------

    retriever = get_retriever(
        vector_store,
        k=4,
    )


    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    llm = get_llm()


    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                RAG_SYSTEM_PROMPT,
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )


    # --------------------------------------------------------
    # RAG chain
    # --------------------------------------------------------

    rag_chain = (

        {
            "context": (
                retriever
                | RunnableLambda(format_docs)
            ),

            "question": (
                RunnablePassthrough()
            ),
        }

        | prompt
        | llm
        | StrOutputParser()

    )


    return rag_chain


# ============================================================
# LOAD EXISTING RAG CHAIN
# ============================================================

def load_rag_chain(
    collection_name: str,
):

    # --------------------------------------------------------
    # Load vector store
    # --------------------------------------------------------

    vector_store = load_vector_store(
        collection_name
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # Pass vector_store to get_retriever()
    # --------------------------------------------------------

    retriever = get_retriever(
        vector_store,
        k=4,
    )


    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    llm = get_llm()


    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                RAG_SYSTEM_PROMPT,
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )


    # --------------------------------------------------------
    # RAG chain
    # --------------------------------------------------------

    rag_chain = (

        {
            "context": (
                retriever
                | RunnableLambda(format_docs)
            ),

            "question": (
                RunnablePassthrough()
            ),
        }

        | prompt
        | llm
        | StrOutputParser()

    )


    return rag_chain


# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(
    rag_chain,
    question: str,
) -> str:

    if rag_chain is None:

        raise RuntimeError(
            "RAG chain has not been initialized."
        )


    if not question.strip():

        return "Please enter a question."


    answer = rag_chain.invoke(
        question
    )


    return answer.strip()
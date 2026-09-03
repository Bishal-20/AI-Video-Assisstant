import os
import re
import uuid

import torch

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ============================================================
# CONFIG
# ============================================================

CHROMA_DIR = "vector_db"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

COLLECTION_PREFIX = "meeting_"


# ============================================================
# EMBEDDINGS
# ============================================================

def get_embeddings():

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": device
        },
    )


# ============================================================
# COLLECTION NAME
# ============================================================

def create_collection_name():

    unique_id = uuid.uuid4().hex[:12]

    return f"{COLLECTION_PREFIX}{unique_id}"


# ============================================================
# BUILD VECTOR STORE
# ============================================================

def build_vector_store(
    transcript: str,
    collection_name: str | None = None,
) -> Chroma:

    print("Building vector store...")

    if not transcript.strip():

        raise ValueError(
            "Cannot build vector store from empty transcript."
        )


    # --------------------------------------------------------
    # Create collection
    # --------------------------------------------------------

    if collection_name is None:

        collection_name = create_collection_name()


    # --------------------------------------------------------
    # Split transcript
    # --------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(
        transcript
    )


    # --------------------------------------------------------
    # Create Documents
    # --------------------------------------------------------

    documents = [

        Document(
            page_content=chunk,
            metadata={
                "chunk_index": i,
            },
        )

        for i, chunk in enumerate(chunks)

    ]


    # --------------------------------------------------------
    # Embeddings
    # --------------------------------------------------------

    embeddings = get_embeddings()


    # --------------------------------------------------------
    # Chroma
    # --------------------------------------------------------

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DIR,
    )


    print(
        f"Vector store created: {collection_name}"
    )

    print(
        f"Indexed {len(documents)} transcript chunks."
    )


    return vector_store


# ============================================================
# LOAD VECTOR STORE
# ============================================================

def load_vector_store(
    collection_name: str,
) -> Chroma:

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    return vector_store


# ============================================================
# RETRIEVER
# ============================================================

def get_retriever(
    vector_store: Chroma,
    k: int = 4,
):

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k
        },
    )
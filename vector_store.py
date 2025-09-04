"""
Module: vector_store.py
Description: Handles PDF processing and ChromaDB vector store management.
Dependencies: chromadb, langchain_chroma, pdfplumber
"""

import os
import glob
import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader
from config import FOLDER_PATH, KNOWLEDGE_BASE_PATH, PROCESSED_FILES_PATH, CHUNK_SIZE, CHUNK_OVERLAP

# Global components
embedding = FastEmbedEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
vector_store = None

def get_processed_files():
    """
    Get the set of already processed files.

    Returns:
        set: Set of processed filenames.
    """
    if os.path.exists(PROCESSED_FILES_PATH):
        with open(PROCESSED_FILES_PATH, 'r') as f:
            return set(f.read().splitlines())
    return set()

def update_processed_files(new_files):
    """
    Update the list of processed files.

    Args:
        new_files (list): List of new filenames to add to the processed files.
    """
    processed = get_processed_files()
    processed.update(new_files)
    with open(PROCESSED_FILES_PATH, 'w') as f:
        f.write('\n'.join(processed))

def initialize_vector_store():
    """
    Initialize or load the vector store.

    Raises:
        Exception: If vector store initialization fails.
    """
    global vector_store
    try:
        if os.path.exists(FOLDER_PATH):
            print("Loading existing vector store...")
            vector_store = Chroma(
                persist_directory=FOLDER_PATH,
                embedding_function=embedding,
                client_settings=chromadb.config.Settings()
            )
        else:
            print("Initializing new vector store...")
            process_all_pdfs()

        # Check for new unprocessed files
        current_files = {os.path.basename(f) for f in glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, "*.pdf"))}
        processed_files = get_processed_files()
        new_files = current_files - processed_files

        if new_files:
            print(f"Processing {len(new_files)} new files...")
            process_pdfs(list(new_files))
            update_processed_files(new_files)

        if vector_store is None:
            raise ValueError("Vector store initialization failed. Check logs for details.")

    except Exception as e:
        print(f"Vector store initialization failed: {e}")
        raise  # Re-raise the exception to stop the application

def process_pdfs(filenames):
    """
    Process PDF files and update the vector store.

    Args:
        filenames (list): List of PDF filenames to process.

    Raises:
        Exception: If PDF processing fails.
    """
    global vector_store
    try:
        all_docs = []
        for i, filename in enumerate(filenames):
            print(f"Processing file {i + 1}/{len(filenames)}: {filename}")
            loader = PDFPlumberLoader(os.path.join(KNOWLEDGE_BASE_PATH, filename))
            docs = loader.load()
            print(f"Loaded {len(docs)} documents from {filename}")
            all_docs.extend(docs)

        if all_docs:
            print("Splitting documents into chunks...")
            chunks = text_splitter.split_documents(all_docs)
            print(f"Created {len(chunks)} chunks")

            print("Generating embeddings and updating vector store...")
            if vector_store:
                vector_store.add_documents(chunks)
            else:
                vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=embedding,
                    persist_directory=FOLDER_PATH,
                    client_settings=chromadb.config.Settings()
                )
            print("Processing complete!")
    except Exception as e:
        print(f"Error processing PDFs: {e}")

def process_all_pdfs():
    """Process all PDFs in the knowledge base."""
    pdf_files = glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, "*.pdf"))
    process_pdfs([os.path.basename(f) for f in pdf_files])
    update_processed_files(os.path.basename(f) for f in pdf_files)

# Initialize the vector store when the module is imported
initialize_vector_store()
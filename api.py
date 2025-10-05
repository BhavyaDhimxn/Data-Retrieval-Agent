"""
Module: api.py
Description: Defines Flask API endpoints for querying and uploading PDFs.
Dependencies: flask, flask_limiter, redis, langchain.chains
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import redis
from vector_store import vector_store, get_processed_files, process_pdfs, update_processed_files
from llm import cached_llm, raw_prompt
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from config import RATE_LIMIT, KNOWLEDGE_BASE_PATH, SEARCH_K, SCORE_THRESHOLD
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader

# Flask app
flask_app = Flask(__name__)

# Decide storage URI for rate limiting: try Redis, fallback to memory for local dev
storage_uri = "redis://localhost:6379"
try:
    redis.Redis(host='localhost', port=6379, db=0).ping()
except redis.ConnectionError:
    storage_uri = "memory://"

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=flask_app,
    storage_uri=storage_uri,
    default_limits=[RATE_LIMIT]
)

@flask_app.route("/ask", methods=["POST"])
@limiter.limit(RATE_LIMIT)
def handle_query():
    """
    Handle queries from the API.

    Returns:
        JSON: Response containing the answer and sources.
    """
    try:
        query = request.json.get("query")
        if not query:
            return jsonify({"error": "Query required"}), 400

        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": SEARCH_K, "score_threshold": SCORE_THRESHOLD}
        )
        chain = create_retrieval_chain(
            retriever,
            create_stuff_documents_chain(cached_llm, raw_prompt)
        )
        result = chain.invoke({"input": query})

        # Add citations
        sources = [{"source": doc.metadata.get("source", "Unknown"), "page": doc.metadata.get("page", "N/A")}
                   for doc in result.get("context", [])]

        return jsonify({
            "answer": result["answer"],
            "sources": sources
        })
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({"error": "Processing failed"}), 500

@flask_app.route("/knowledge_base", methods=["POST"])
@limiter.limit(RATE_LIMIT)
def upload_pdf():
    """
    Handle PDF uploads.

    Returns:
        JSON: Response indicating the status of the upload.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files accepted"}), 400

    save_path = os.path.join(KNOWLEDGE_BASE_PATH, file.filename)
    file.save(save_path)

    if file.filename in get_processed_files():
        return jsonify({"warning": "File already processed"}), 200

    try:
        process_pdfs([file.filename])
        update_processed_files([file.filename])
        return jsonify({
            "status": "Processed successfully",
            "file": file.filename,
            "chunks": len(RecursiveCharacterTextSplitter().split_documents(PDFPlumberLoader(save_path).load()))
        })
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": "File processing failed"}), 500
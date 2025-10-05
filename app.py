"""
Module: app.py
Description: Main entry point for the application.
Dependencies: flask
"""

import logging
from api import flask_app
from vector_store import initialize_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    try:
        # Initialize vector store on app startup
        logging.info("Initializing vector store...")
        initialize_vector_store()
        logging.info("Vector store initialized successfully.")

        # Start Flask API
        logging.info("Starting Flask API on port 5000...")
        flask_app.run(port=5000)
    except Exception as e:
        logging.error(f"Application encountered an error: {e}")
        exit(1)



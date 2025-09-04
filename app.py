"""
Module: app.py
Description: Main entry point for the application.
Dependencies: flask, slack_bolt, redis
"""

import logging
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from api import flask_app
from slack import start_slack_bot
from vector_store import initialize_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask app
app = Flask(__name__)

# Initialize Redis client for rate limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Check if Redis is running
    logging.info("Connected to Redis successfully.")
except redis.ConnectionError:
    logging.error("Failed to connect to Redis. Ensure Redis is running on localhost:6379.")
    exit(1)

# Configure Flask-Limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"  # Redis URI for rate limiting
)
limiter.init_app(app)

if __name__ == "__main__":
    try:
        # Initialize vector store on app startup
        logging.info("Initializing vector store...")
        initialize_vector_store()
        logging.info("Vector store initialized successfully.")

        # Start Slack bot
        logging.info("Starting Slack bot...")
        start_slack_bot()
        logging.info("Slack bot started successfully.")

        # Start Flask API
        logging.info("Starting Flask API on port 5000...")
        flask_app.run(port=5000)
    except Exception as e:
        logging.error(f"Application encountered an error: {e}")
        exit(1)



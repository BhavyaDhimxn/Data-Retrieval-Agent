import os

# Configuration
FOLDER_PATH = "db"
KNOWLEDGE_BASE_PATH = "knowledge_base"
PROCESSED_FILES_PATH = os.path.join(KNOWLEDGE_BASE_PATH, "processed_files.txt")

# Ensure necessary directories exist
os.makedirs(FOLDER_PATH, exist_ok=True)
os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)

# Slack credentials
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

# Vector store and chunking configuration
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 80
SEARCH_K = 15
SCORE_THRESHOLD = 0.2

# Rate limiting
RATE_LIMIT = "10/minute"
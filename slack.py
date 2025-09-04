"""
Module: slack.py
Description: Handles Slack bot interactions.
Dependencies: slack_bolt, langchain.chains
"""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from vector_store import vector_store
from llm import cached_llm, raw_prompt
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN, SEARCH_K, SCORE_THRESHOLD

# Slack app
slack_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

def format_response(answer, sources):
    """
    Format the response with Markdown for Slack.

    Args:
        answer (str): The answer to the query.
        sources (list): List of sources with metadata.

    Returns:
        str: Formatted response.
    """
    # Clean up the answer (remove unwanted tags)
    answer = answer.replace("<s>[INST]", "").replace("[/INST]</s>", "").strip()

    # Format sources with page numbers
    sources_text = "\n".join([f"> *Source*: {s['source']} (Page: {s.get('page', 'N/A')})" for s in sources])

    # Return the formatted response
    return f"""
*Answer*:
{answer}

*Sources (Citations)*:
{sources_text}
"""


@slack_app.message(".*")
def handle_message(body, say):
    """
    Handle Slack messages.

    Args:
        body (dict): The event body from Slack.
        say (function): Function to send a response in Slack.
    """
    try:
        if vector_store is None:
            say("Error: Vector store is not initialized. Please contact the administrator.")
            return

        query = body["event"]["text"]
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

        # Format and send response
        response = format_response(result["answer"], sources)
        say(response)
    except Exception as e:
        print(f"Slack error: {e}")
        say("Error processing your request")

@slack_app.event("app_mention")
def handle_app_mention(body, say):
    """
    Handle Slack app mentions.

    Args:
        body (dict): The event body from Slack.
        say (function): Function to send a response in Slack.
    """
    try:
        if vector_store is None:
            say("Error: Vector store is not initialized. Please contact the administrator.")
            return

        query = body["event"]["text"]
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

        # Format and send response
        response = format_response(result["answer"], sources)
        say(response)
    except Exception as e:
        print(f"App mention error: {e}")
        say("Error processing your mention request")

# Start the Slack bot
def start_slack_bot():
    """Start the Slack bot in Socket Mode."""
    handler = SocketModeHandler(slack_app, SLACK_APP_TOKEN)
    handler.start()

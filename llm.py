"""
Module: llm.py
Description: Handles LLM initialization and prompt templates.
Dependencies: langchain_ollama, langchain.prompts
"""

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

# LLM initialization
cached_llm = OllamaLLM(model="llama3")

# Prompt template
raw_prompt = PromptTemplate.from_template(
    """<s>[INST] You are a technical assistant that answers strictly from provided context.
    If unsure, say "I don't know based on my training data". Context: {context}
    Question: {input} [/INST]</s>"""
)
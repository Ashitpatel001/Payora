from langchain_groq import ChatGroq
import os

def get_llm(temperature: float = 0.2) -> ChatGroq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
        
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=api_key,
        timeout=15,
        max_retries=0,
    )


import ollama
from analysis import get_overview

def ask_agent(question):
    context = str(get_overview())

    response = ollama.chat(
        model="llama3:8b",
        messages=[
            {
                "role":"user",
                "content": f'''
You are an urban intelligence assistant for Kolding Kommune.

Context:
{context}

Question:
{question}

Answer professionally and briefly.
'''
            }
        ]
    )

    return response["message"]["content"]

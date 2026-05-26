
# import ollama
# from analysis import get_overview

# def ask_agent(question):
#     context = str(get_overview())

#     response = ollama.chat(
#         model="llama3:8b",
#         messages=[
#             {
#                 "role":"user",
#                 "content": f'''
# You are an urban intelligence assistant for Kolding Kommune.

# Context:
# {context}

# Question:
# {question}

# Answer professionally and briefly.
# '''
#             }
#         ]
#     )

#     return response["message"]["content"]


# import ollama
# from analysis import get_overview

# def ask_agent(question):
#     context = str(get_overview())

#     response = ollama.chat(
#         model="llama3:8b",
#         messages=[
#             {
#                 "role": "system",
#                 "content": """You are a concise urban data assistant for Kolding Kommune, Denmark.

# Rules you must follow:
# - Answer to the question directly with basic understanding
# - Only use the provided data context — never invent figures
# - Focus strictly on Kolding and Denmark
# - No greetings, no sign-offs, no filler phrases
# - If the question is outside the data scope, say: "That data is not available in the current database."
# - Respond in the same language the user writes in"""
#             },
#             {
#                 "role": "user",
#                 "content": f"""Data context:
# {context}

# Question: {question}"""
#             }
#         ]
#     )

#     return response["message"]["content"]


# import ollama
# from analysis import get_full_ai_context

# def ask_agent(question):

#     context = get_full_ai_context()

#     response = ollama.chat(
#         model="llama3:8b",
#         messages=[
#             {
#                 "role": "system",
#                 "content": """You are a professional urban data analyst for Kolding Kommune, Denmark.

# Rules:
# - Answer to the question directly with required correct understanding
# - Use ONLY the data provided — never invent or estimate figures not in the context
# - Focus exclusively on Kolding, Denmark
# - Start directly with the answer — no greetings, no "Based on the data...", no sign-offs
# - Use specific numbers from the data when answering
# - If the question cannot be answered from the data, reply only: "That detail is not available in the current Kolding database."
# - When asked about charts or visualisations on the page, use the corresponding dataset sections to answer"""
#             },
#             {
#                 "role": "user",
#                 "content": f"DATA:\n{context}\n\nQUESTION: {question}"
#             }
#         ]
#     )

#     return response["message"]["content"]

# import ollama
# from analysis import get_full_ai_context

# def ask_agent(question):

#     context = get_full_ai_context()

#     response = ollama.chat(
#         model="llama3:8b",
#         messages=[
#             {
#                 "role":"system",
#                 "content": """
# You are Kolding Pulse AI, an urban intelligence analyst for Kolding Kommune.

# Your job is NOT only to report data.
# Your job is to explain urban patterns and provide insight.

# Rules:
# - Use ONLY the provided Kolding data
# - Never invent numbers
# - Use exact figures from the dataset
# - Be concise but insightful
# - Explain WHY patterns may matter
# - Highlight trends when visible
# - If comparison is possible, compare
# - When appropriate, mention urban implications
# - No greetings or filler

# Good answer style:

# Bad:
# "The movement was 11618."

# Good:
# "March 27 recorded the highest movement with 11,618 movements, indicating unusually strong urban activity compared with surrounding days."

# If unavailable:
# "That detail is not available in the current Kolding database."
# """
#             },
#             {
#                 "role":"user",
#                 "content": f"""
# KOLDING DATA:
# {context}

# QUESTION:
# {question}
# """
#             }
#         ]
#     )

#     return response["message"]["content"]

import ollama
from analysis import get_full_ai_context

# Conversation memory
conversation_history = []

SYSTEM_PROMPT = """
You are Kolding Pulse AI, an urban intelligence analyst for Kolding Kommune, Denmark.

Your role:
- Explain movement, stay behaviour, events and city activity
- Provide useful urban insight
- Explain WHY patterns matter
- Compare trends when possible
- Focus ONLY on Kolding data

Rules:
- Use ONLY provided data
- Never invent numbers
- Use exact figures
- Be concise but intelligent
- No greetings
- No filler text
- No sign-offs

Good answer style:

Bad:
"Movement was 11618."

Good:
"March 27 recorded the highest movement with 11,618 movements, indicating unusually strong urban activity compared with surrounding days."

If unavailable:
"That detail is not available in the current Kolding database."
"""

def ask_agent(question):

    global conversation_history

    context = get_full_ai_context()

    messages = [
        {
            "role":"system",
            "content":SYSTEM_PROMPT
        },
        {
            "role":"user",
            "content":f"""
KOLDING DATA:
{context}
"""
        }
    ]

    # memory
    messages.extend(conversation_history)

    # new question
    messages.append({
        "role":"user",
        "content":question
    })

    response = ollama.chat(
        model="llama3:8b",
        messages=messages
    )

    answer = response["message"]["content"]

    # save memory
    conversation_history.append({
        "role":"user",
        "content":question
    })

    conversation_history.append({
        "role":"assistant",
        "content":answer
    })

    # limit memory size
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    return answer


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

def parking_ai_insight(stats_text):

    prompt = f"""
You are Kolding Pulse AI.

Provide a short parking intelligence insight
in 2 concise sentences.

Focus on:
- parking demand
- congestion
- mobility implications

Use only these parking statistics:

{stats_text}

No greetings.
No filler.
Professional tone.
"""

    response = ollama.chat(
        model="llama3:8b",
        messages=[
            {
                "role":"system",
                "content":"You are a parking mobility analyst."
            },
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response["message"]["content"]

def city_ai_insight(stats_text):

    prompt = f"""
You are Kolding Pulse AI.

Provide a short city activity insight
in 2 concise sentences.

Focus on:
- urban vitality
- activity intensity
- open places and movement

Use ONLY this data:

{stats_text}

No greetings.
Professional tone.
No filler.
"""

    response = ollama.chat(
        model="llama3:8b",
        messages=[
            {
                "role":"system",
                "content":"You are an urban vitality analyst."
            },
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response["message"]["content"]


def forecast_ai_insight(stats_text):

    prompt = f"""
You are Kolding Pulse AI.

Provide a short forecast intelligence insight
in 2 concise sentences.

Focus on:

- predicted movement
- expected activity
- crowd intensity
- planning implications

Use ONLY these forecast statistics:

{stats_text}

No greetings.
No filler.
Professional tone.
"""

    response = ollama.chat(
        model="llama3:8b",
        messages=[
            {
                "role":"system",
                "content":
                "You are a city forecasting analyst."
            },
            {
                "role":"user",
                "content":
                prompt
            }
        ]
    )

    return response["message"]["content"]
import glob
import os

import ollama
import pandas as pd

from config import OLLAMA_MODEL, AI_ENABLED, DATA_DIR

_AI_DISABLED_MSG = "AI is currently disabled. Set AI_ENABLED = True in config.py to enable."

# ── Load all CSVs and XLSXs from data/ at startup ─────────────────────────────
DATA_CONTEXT = ""

for file in glob.glob(str(DATA_DIR / "*")):
    try:
        ext = os.path.splitext(file)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file, low_memory=False)
        elif ext == ".xlsx":
            df = pd.read_excel(file)
        else:
            continue

        name = os.path.basename(file)
        DATA_CONTEXT += f"""
==================================================
DATASET: {name}
==================================================
Columns: {list(df.columns)}
Total rows: {len(df)}
FULL DATA:
{df.to_string(index=False)}
"""
        print(f"[agent] Loaded: {name}")
    except Exception as e:
        print(f"[agent] Failed loading {file}: {e}")

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are Kolding Pulse AI, an urban intelligence analyst for Kolding Kommune, Denmark.

You have access to ALL datasets inside the data folder.

Rules:
- Use ONLY loaded datasets
- Never invent numbers
- Use exact figures
- Explain patterns and WHY they matter
- Compare trends when useful
- Be concise but intelligent
- Professional tone
- No greetings, no filler text, no sign-offs

Focus on: movement, stay duration, parking, congestion, forecast,
city activity, holidays, events, and any loaded dataset.

Good answer style:
Bad:  "Movement was 11618."
Good: "March 27 recorded the highest movement with 11,618 movements,
       indicating unusually strong urban activity compared with surrounding days."

If data is unavailable:
"That detail is not available in the current Kolding database."
"""

# ── Conversation memory ────────────────────────────────────────────────────────
_conversation_history = []


# ── Main chat agent ────────────────────────────────────────────────────────────
def ask_agent(question: str, context: str = "") -> str:
    """context param kept for backwards compatibility but DATA_CONTEXT is used."""
    if not AI_ENABLED:
        return _AI_DISABLED_MSG

    global _conversation_history

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"KOLDING DATABASE:\n{DATA_CONTEXT}"},
        *_conversation_history,
        {"role": "user",   "content": question},
    ]

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    answer   = response["message"]["content"]

    _conversation_history.append({"role": "user",      "content": question})
    _conversation_history.append({"role": "assistant", "content": answer})

    if len(_conversation_history) > 10:
        _conversation_history = _conversation_history[-10:]

    return answer


# ── Specialised insight calls (use DATA_CONTEXT too) ──────────────────────────
def _quick_insight(system: str, prompt: str) -> str:
    if not AI_ENABLED:
        return _AI_DISABLED_MSG

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": f"KOLDING DATABASE:\n{DATA_CONTEXT}\n\n{prompt}"},
        ],
    )
    return response["message"]["content"]


def parking_ai_insight(stats_text: str) -> str:
    return _quick_insight(
        system="You are a parking mobility analyst.",
        prompt=(
            f"Provide a short parking intelligence insight in 2 concise sentences.\n"
            f"Focus on: parking demand, congestion, mobility implications.\n"
            f"Additional stats:\n{stats_text}\n\n"
            f"No greetings. No filler. Professional tone."
        ),
    )


def city_ai_insight(stats_text: str) -> str:
    return _quick_insight(
        system="You are an urban vitality analyst.",
        prompt=(
            f"Provide a short city activity insight in 2 concise sentences.\n"
            f"Focus on: urban vitality, activity intensity, open places and movement.\n"
            f"Additional stats:\n{stats_text}\n\n"
            f"No greetings. Professional tone. No filler."
        ),
    )


def forecast_ai_insight(stats_text: str) -> str:
    return _quick_insight(
        system="You are a city forecasting analyst.",
        prompt=(
            f"Provide a short forecast intelligence insight in 2 concise sentences.\n"
            f"Focus on: predicted movement, expected activity, crowd intensity, planning implications.\n"
            f"Additional stats:\n{stats_text}\n\n"
            f"No greetings. No filler. Professional tone."
        ),
    )
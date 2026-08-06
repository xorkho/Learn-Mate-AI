import httpx
from app.config import settings
import json

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b:free"


def _call_openrouter(payload: dict) -> dict:
    """
    Shared helper — OpenRouter ko call karta hai aur common errors
    (rate limit, network issue) ko clean ValueError mein convert karta hai.
    """
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise ValueError("The AI service is currently rate-limited. Please wait a minute and try again.")
        raise ValueError(f"AI service error: {e.response.status_code}")
    except httpx.RequestError:
        raise ValueError("Could not reach the AI service. Please check your connection and try again.")

    return response.json()


def ask_llm(query: str, context_chunks: list[str]) -> str:
    """
    Given a user query and relevant context chunks, ask the LLM
    to answer based on the document context.
    """
    context_text = "\n\n".join(context_chunks)

    system_prompt = (
        "You are a helpful study assistant. Answer the user's question "
        "using ONLY the context provided below. "
        "Keep your answer SHORT and to the point — 2 to 4 sentences maximum, "
        "unless the question specifically asks for a list or detailed explanation. "
        "Use markdown formatting (bullet points, bold text) where it improves clarity. "
        "If the answer is not found in the context, say so honestly instead of making things up.\n\n"
        f"Context:\n{context_text}"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        "max_tokens": 300,
        "temperature": 0.3,
    }

    data = _call_openrouter(payload)
    return data["choices"][0]["message"]["content"]


def generate_summary(chunks: list[str]) -> str:
    """
    Generate a structured study summary of the document.
    """
    context_text = "\n\n".join(chunks[:15])  # speed ke liye 30 se 15 kiya

    system_prompt = f"""
You are an expert study assistant.

Your task is to create a well-structured summary of the provided document.

Instructions:
- Write approximately 300–500 words.
- Start with a heading: ## Document Summary
- Begin with a short 2–3 sentence overview.
- Organize the summary into clear sections using Markdown headings.
- Use bullet points wherever appropriate.
- Highlight important terms using **bold**.
- Focus only on the important concepts and ignore repetitive details.
- Maintain the original meaning without adding information.
- Use simple, easy-to-understand language suitable for students.
- End with a section titled **Key Takeaways** containing 5 concise bullet points.

Document:
{context_text}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the document summary."},
        ],
        "temperature": 0.3,
        "max_tokens": 700,
    }

    data = _call_openrouter(payload)
    return data["choices"][0]["message"]["content"]


def generate_quiz(chunks: list[str], num_questions: int = 5, difficulty: str = "medium") -> list[dict]:
    """
    Generate multiple-choice questions based on the document content,
    tagged with topic and difficulty level.
    """
    context_text = "\n\n".join(chunks[:30])

    difficulty_instructions = {
        "easy": "Focus on basic recall and simple definitions from the text.",
        "medium": "Focus on understanding concepts and how they relate to each other.",
        "hard": "Focus on deeper analysis, application, and edge cases from the text.",
    }
    difficulty_note = difficulty_instructions.get(difficulty, difficulty_instructions["medium"])

    system_prompt = (
        "You are a helpful study assistant. Based on the document content below, "
        f"generate exactly {num_questions} multiple-choice questions at {difficulty} difficulty level. "
        f"{difficulty_note} "
        "Respond ONLY with a valid JSON array, no extra text, no markdown formatting. "
        "Each item must have this exact structure:\n"
        '{"question": "the question text", '
        '"options": ["first option text", "second option text", "third option text", "fourth option text"], '
        '"correct_answer": "the exact text of the correct option, copied character-for-character from the options array", '
        '"topic": "a short 2-4 word topic label for this question, e.g. \'Python Loops\' or \'Data Structures\'"}\n\n'
        "IMPORTANT: correct_answer must be an exact copy of one of the strings in the options array — "
        "do NOT use letters like A, B, C, D. Use the full option text.\n\n"
        f"Document content:\n{context_text}"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate {num_questions} {difficulty} quiz questions."},
        ],
        "max_tokens": 1200,
        "temperature": 0.4,
    }

    data = _call_openrouter(payload)
    raw_text = data["choices"][0]["message"]["content"]

    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        quiz_data = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("The AI returned an unexpected format. Please try generating the quiz again.")

    return quiz_data
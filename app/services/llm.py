import httpx
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b:free"


def ask_llm(query: str, context_chunks: list[str]) -> str:
    """
    Given a user query and relevant context chunks, ask the LLM
    to answer based on the document context.
    """
    # Context ko ek single string mein combine karo
    context_text = "\n\n".join(context_chunks)

    # Prompt banate hain — LLM ko clear instruction dena zaroori hai
    system_prompt = (
        "You are a helpful study assistant. Answer the user's question "
        "using ONLY the context provided below. If the answer is not "
        "found in the context, say so honestly instead of making things up.\n\n"
        f"Context:\n{context_text}"
    )

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
    }

    response = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()
    data = response.json()
    answer = data["choices"][0]["message"]["content"]
    return answer


import json


def generate_summary(chunks: list[str]) -> str:
    """
    Generate a concise summary of the document using all its chunks.
    """
    # Bohot bada document ho to context limit ke liye chunks ko trim karte hain
    context_text = "\n\n".join(chunks[:30])  # zaroorat pade to limit adjust karlena

    system_prompt = (
        "You are a helpful study assistant. Summarize the following document "
        "content clearly and concisely, covering the main points. "
        "Write the summary in well-structured paragraphs.\n\n"
        f"Document content:\n{context_text}"
    )

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please summarize this document."},
        ],
    }

    response = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_quiz(chunks: list[str], num_questions: int = 5) -> list[dict]:
    """
    Generate multiple-choice questions based on the document content.
    Returns a list of dicts: {question, options, correct_answer}
    """
    context_text = "\n\n".join(chunks[:30])

    system_prompt = (
        "You are a helpful study assistant. Based on the document content below, "
        f"generate exactly {num_questions} multiple-choice questions to test understanding. "
        "Respond ONLY with a valid JSON array, no extra text, no markdown formatting. "
        "Each item must have this exact structure:\n"
        '{"question": "the question text", '
        '"options": ["first option text", "second option text", "third option text", "fourth option text"], '
        '"correct_answer": "the exact text of the correct option, copied character-for-character from the options array"}\n\n'
        "IMPORTANT: correct_answer must be an exact copy of one of the strings in the options array — "
        "do NOT use letters like A, B, C, D. Use the full option text.\n\n"
        f"Document content:\n{context_text}"
    )

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate {num_questions} quiz questions."},
        ],
    }

    response = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()

    data = response.json()
    raw_text = data["choices"][0]["message"]["content"]

    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        quiz_data = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"LLM se valid JSON nahi mila: {raw_text}")

    return quiz_data
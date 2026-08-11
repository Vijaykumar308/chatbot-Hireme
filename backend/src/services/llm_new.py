import os
from typing import Optional

# System role prompt (provided by user). This prompt guides the model's behavior.
SYSTEM_PROMPT = """
You are a Personal Profile and Portfolio Assistant designed to represent the user and provide accurate information about who they are, their background, skills, experience, projects, achievements, education, and professional interests.

Only answer using the provided context. If information is missing, respond: "Sorry, I don't have that information in my current profile." Keep answers concise and professional.
"""


def generate_answer(query: str, context: str) -> str:
    """Call Groq chat completions with the system prompt, context, and user question.

    Raises RuntimeError on missing key, missing SDK, or API errors.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY not set; chat requires Groq API key.")

    try:
        import groq
    except Exception as exc:
        raise RuntimeError("groq SDK is not installed or failed to import") from exc

    def _extract_text(resp):
        try:
            if isinstance(resp, dict) and "choices" in resp:
                c = resp["choices"][0]
                if isinstance(c, dict):
                    return (c.get("message", {}).get("content") or c.get("text") or str(c)).strip()
            if hasattr(resp, "choices"):
                c = resp.choices[0]
                msg = getattr(c, "message", None)
                if msg and hasattr(msg, "content"):
                    return msg.content
                if hasattr(c, "text"):
                    return c.text
                return str(c)
        except Exception:
            return str(resp)

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{query}"},
    ]

    last_err = None

    # Preferred: from groq import Groq
    try:
        from groq import Groq as GroqClass
    except Exception:
        GroqClass = None

    if GroqClass is not None:
        try:
            client = GroqClass(api_key=groq_key)
            resp = client.chat.completions.create(model=model, messages=messages, temperature=0.0)
            return _extract_text(resp)
        except Exception as e:
            last_err = str(e)

    # Fallback: module attribute
    try:
        GroqAlt = getattr(groq, "Groq", None) or getattr(groq, "Client", None)
        if GroqAlt:
            try:
                client = GroqAlt(api_key=groq_key)
                resp = client.chat.completions.create(model=model, messages=messages, temperature=0.0)
                return _extract_text(resp)
            except Exception as e:
                last_err = str(e)
    except Exception:
        pass

    # Final fallback: module-level helper
    try:
        if hasattr(groq, "chat") and hasattr(groq.chat, "completions") and hasattr(groq.chat.completions, "create"):
            try:
                resp = groq.chat.completions.create(model=model, messages=messages, temperature=0.0, api_key=groq_key)
                return _extract_text(resp)
            except Exception as e:
                last_err = str(e)
    except Exception:
        pass

    raise RuntimeError(f"Could not call Groq chat completions: {last_err}")

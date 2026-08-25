import os
import re
from typing import Optional

# System role prompt (provided by user). This prompt guides the model's behavior.
SYSTEM_PROMPT = """
You are a Personal Profile and Portfolio Assistant designed to represent the user and provide accurate information about who they are, their background, skills, experience, projects, achievements, education, and professional interests.

The person's name is Vijay Kumar. If the user asks your name, the person's name, or who you represent, answer that the person's name is Vijay Kumar. Never use a job title, project name, section heading, or company name as the person's name.
You represent Vijay Kumar to recruiters and HR professionals. When the provided context contains contact details, notice period, availability, or other profile facts, share them directly and accurately when asked. Never disclose current CTC, expected CTC, salary, compensation, remuneration, or pay package; respond that compensation details are not shared through this assistant. Do not invent details that are not in the context.
Only answer using the provided context and these verified identity details. If information is missing, respond: "Sorry, I don't have that information in my current profile." Keep answers concise and professional.
"""


def format_llm_error_message(raw_message: str) -> str:
    """Convert raw Groq/SDK errors into a friendly message for the UI."""
    text = (raw_message or "").strip()
    if not text:
        return "The assistant is temporarily unavailable. Please try again in a moment."

    lowered = text.lower()
    if "429" in text or "rate limit" in lowered or "tokens per day" in lowered:
        return (
            "The assistant is temporarily unavailable because the AI service rate limit was reached. "
            "Please try again in a couple of minutes."
        )

    if "api key" in lowered or "groq_api_key" in lowered:
        return "The assistant is not configured correctly. Please check the backend settings and try again."

    if "sdk" in lowered or "import" in lowered or "failed to import" in lowered:
        return "The AI service is not available right now. Please try again in a moment."

    return "Something went wrong while generating the answer. Please try again in a moment."


def _normalise_text(value: str) -> str:
    return (value or "").strip()


def _extract_name(context: str) -> str:
    if not context:
        return "Vijay Kumar"

    verified_name = re.search(r"\bvijay\s+kumar\b", context, flags=re.IGNORECASE)
    if verified_name:
        return verified_name.group(0)

    clean = context.replace("⋄", " ").replace("|", " ").replace("•", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in clean.splitlines() if line.strip()]

    skip_terms = (
        "OBJECTIVE",
        "TECHNICAL",
        "PROFESSIONAL",
        "EXPERIENCE",
        "PROJECTS",
        "EDUCATION",
        "CERTIFICATIONS",
        "FULL STACK",
        "SOFTWARE DEVELOPER",
        "PROFILE",
        "ROLE",
    )

    for line in lines[:12]:
        upper_line = line.upper()
        if any(term in upper_line for term in skip_terms):
            continue
        if "@" in line or "linkedin" in line.lower() or "github" in line.lower():
            continue
        if re.search(r"\d", line):
            continue
        words = line.split()
        if len(words) < 2 or len(words) > 4:
            continue
        if re.search(r"[A-Za-z]", line):
            return line

    return "Vijay Kumar"


def _matches_name_question(query: str) -> bool:
    q = (query or "").lower()
    name_terms = ["name", "who am i", "who is this", "who are you", "your name"]
    return any(term in q for term in name_terms)


def _matches_salary_question(query: str) -> bool:
    salary_terms = (
        "ctc",
        "salary",
        "compensation",
        "remuneration",
        "pay package",
        "expected package",
    )
    query_text = (query or "").lower()
    return any(term in query_text for term in salary_terms)


def build_personal_details_response(query: str, context: str) -> Optional[str]:
    """Return only the deterministic identity response."""
    if not query:
        return None

    if _matches_salary_question(query):
        return "I do not share compensation details through this assistant."

    if _matches_name_question(query):
        name = _extract_name(context)
        if not name:
            name = "Vijay Kumar"
        return f"My name is {name}."

    return None


def generate_answer(query: str, context: str) -> str:
    """Call Groq chat completions with the system prompt, context, and user question.

    Raises RuntimeError on missing key, missing SDK, or API errors.
    """
    guarded_response = build_personal_details_response(query, context)
    if guarded_response:
        return guarded_response

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

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

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

    raise RuntimeError(format_llm_error_message(last_err or "Could not call Groq chat completions"))

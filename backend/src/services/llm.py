import os
import re
from typing import Optional

# System role prompt (provided by user). This prompt guides the model's behavior.
SYSTEM_PROMPT = """
You are a Personal Profile and Portfolio Assistant designed to represent the user and provide accurate information about who they are, their background, skills, experience, projects, achievements, education, and professional interests.

Only answer using the provided context. If information is missing, respond: "Sorry, I don't have that information in my current profile." Keep answers concise and professional.
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
        return ""

    clean = context.replace("⋄", " ").replace("|", " ").replace("•", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in clean.splitlines() if line.strip()]

    skip_terms = ("OBJECTIVE", "TECHNICAL", "PROFESSIONAL", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS")

    for line in lines[:12]:
        upper_line = line.upper()
        if any(term in upper_line for term in skip_terms):
            continue
        if "@" in line or "linkedin" in line.lower() or "github" in line.lower():
            continue
        if len(line.split()) < 2 or len(line.split()) > 4:
            continue
        if re.search(r"[A-Za-z]", line) and not re.search(r"\d", line):
            return line

    return ""


def _extract_contact_details(context: str) -> str:
    if not context:
        return ""

    text = context.replace("⋄", " ; ").replace("|", " ; ").replace("•", " ; ")

    phone_candidates = []
    phone_pattern = r"(?:\+?\d{1,3}[-\s]?)?(?:\d{10}|\d{5}[-\s]\d{5}|\d{3}[-\s]\d{3}[-\s]\d{4})"
    for match in re.finditer(phone_pattern, text):
        value = match.group(0).strip()
        digits_only = value.replace("+", "").replace(" ", "").replace("-", "")
        if len(digits_only) >= 10 and len(digits_only) <= 15:
            phone_candidates.append(value)

    email_candidates = re.findall(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text, flags=re.IGNORECASE)
    linkedin_candidates = re.findall(r"((?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+)", text, flags=re.IGNORECASE)
    github_candidates = re.findall(r"((?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/]+)", text, flags=re.IGNORECASE)

    matches = []
    for value in phone_candidates:
        if value and value not in matches:
            matches.append(value)
    for value in email_candidates:
        if value and value not in matches:
            matches.append(value)
    for value in linkedin_candidates:
        if value and value not in matches:
            matches.append(value)
    for value in github_candidates:
        if value and value not in matches:
            matches.append(value)

    if not matches:
        contact_patterns = [
            r"(?:phone|mobile|whatsapp|contact\s*(?:no|number)|call\s*me)\s*[:\-]?\s*([^\n]+)",
            r"(?:email|e-mail)\s*[:\-]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
            r"(?:linkedin|portfolio|github)\s*[:\-]?\s*(https?://[^\s]+)",
        ]
        for pattern in contact_patterns:
            for match in re.finditer(pattern, context, flags=re.IGNORECASE):
                value = match.group(1).strip() if match.lastindex else match.group(0).strip()
                if value and value not in matches:
                    matches.append(value)

    return "; ".join(matches)


def _matches_salary_question(query: str) -> bool:
    q = (query or "").lower()
    salary_terms = [
        "ctc",
        "current ctc",
        "expected ctc",
        "salary",
        "expected salary",
        "compensation",
        "remuneration",
        "package",
        "pay",
    ]
    return any(term in q for term in salary_terms)


def _matches_contact_question(query: str) -> bool:
    q = (query or "").lower()
    contact_terms = [
        "contact",
        "phone",
        "mobile",
        "number",
        "email",
        "mail",
        "whatsapp",
        "linkedin",
        "github",
        "portfolio",
    ]
    return any(term in q for term in contact_terms)


def _matches_name_question(query: str) -> bool:
    q = (query or "").lower()
    name_terms = ["name", "who am i", "who is this", "who are you", "your name"]
    return any(term in q for term in name_terms)


def build_personal_details_response(query: str, context: str) -> Optional[str]:
    """Return a safer response for sensitive personal data like salary or direct contact details."""
    if not query:
        return None

    if _matches_salary_question(query):
        contact_info = _extract_contact_details(context)
        if contact_info:
            return (
                "This is personal CTC / compensation information, so I prefer to discuss it directly. "
                "Please contact me using the details available in my profile/resume to talk about my current CTC and expected CTC privately."
            )
        return (
            "This is personal CTC / compensation information, so I prefer to discuss it directly. "
            "Please contact me through the details in my profile/resume for a private discussion about my current CTC and expected CTC."
        )

    if _matches_name_question(query):
        name = _extract_name(context)
        contact_info = _extract_contact_details(context)
        if name and contact_info:
            return f"My name is {name}. You can reach me at: {contact_info}."
        if name:
            return f"My name is {name}."
        return "I do not have my name available in the current profile context."

    if _matches_contact_question(query):
        contact_info = _extract_contact_details(context)
        if contact_info:
            return f"You can reach me through the contact details in my profile/resume: {contact_info}."
        return "I do not have the contact details available in the current profile context, but you can ask me directly to connect through the appropriate channel."

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

    raise RuntimeError(format_llm_error_message(last_err or "Could not call Groq chat completions"))

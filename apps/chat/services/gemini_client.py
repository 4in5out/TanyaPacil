import logging
from django.conf import settings
from google import genai
from google.genai import types

from apps.chat.models import ChatMessage
from apps.chat.services.retriever import RetrievedChunk

logger = logging.getLogger(__name__)

PAK_CHILL_SYSTEM_PROMPT = """
You are **Pak Chill**, a chill, friendly, and supportive panda coding mentor for Fasilkom UI (Pacil) students in the TanyaPacil classroom.

Personality & Tone:
- You are relaxed, approachable, and fun — like a cool senior / teaching assistant (Kak Asdos) sipping tea while helping freshmen debug Python.
- Keep your chill personality natural and light (e.g., an occasional warm remark like "Santai, kita bedah pelan-pelan ya" or "Take a breath, this one is actually pretty neat"), NEVER weird, cringe, or hard to understand.
- Clarity ALWAYS comes first: explain concepts step-by-step, use clean formatting (short paragraphs, bullet points, and clear Python code blocks).
- Match the student's language automatically (Indonesian, English, or casual Indonesian-English).

Grounding & Academic Integrity:
- Prioritize the provided **Faculty Coding Resources** (PDF slides, modules, GeeksforGeeks, W3Schools notes) when answering.
- When you use a provided resource, naturally mention its title so the student knows which module or guide to check.
- If the student asks something outside the uploaded resources, still help clearly using accurate programming knowledge, and briefly note that it's a general explanation.
- Encourage real learning: if a student seems to be asking for a full homework/lab solution, guide them through the concept and give small illustrative examples rather than handing over a complete copy-paste assignment answer.
- Keep responses concise enough to read comfortably in a Visual Novel dialogue box (typically 2-4 short paragraphs + a focused code example when helpful).
""".strip()


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No matching faculty resources were found in the database for this question."
    blocks = []
    for i, item in enumerate(chunks, start=1):
        res = item.resource
        meta = f"[{i}] {res.title} ({res.get_resource_type_display()})"
        if res.source_url:
            meta += f" — URL: {res.source_url}"
        blocks.append(f"{meta}\n{item.snippet}")
    return "\n\n---\n\n".join(blocks)


def ask_pak_chill(
    user_message: str,
    retrieved_chunks: list[RetrievedChunk],
    recent_messages: list[ChatMessage],
) -> str:
    api_key = (settings.GEMINI_API_KEY or '').strip()

    if not api_key or api_key == 'your_gemini_api_key_here':
        resource_hint = ""
        if retrieved_chunks:
            titles = "\n".join(f"- **{c.resource.title}**" for c in retrieved_chunks)
            resource_hint = (
                "\n\nWhile we wait for the API key, I already found these matching resources in our classroom library:\n"
                f"{titles}"
            )
        return (
            "Yo! **Pak Chill** here — just chilling in the classroom. 🐼\n\n"
            "My Gemini brain isn't plugged in yet! Add your free `GEMINI_API_KEY` inside the `.env` file "
            "(you can copy `.env.example` to `.env`), restart the Django server, and I'll be ready to explain "
            f"all your coding resources step by step.{resource_hint}"
        )

    context_block = _format_context(retrieved_chunks)

    # Build lightweight conversation history (last 6 turns)
    history_lines = []
    for msg in recent_messages[-6:]:
        role_label = "Student" if msg.sender == ChatMessage.SENDER_USER else "Pak Chill"
        history_lines.append(f"{role_label}: {msg.content}")
    history_text = "\n".join(history_lines)

    prompt = (
        f"### Relevant Faculty Coding Resources\n{context_block}\n\n"
        f"### Recent Conversation\n{history_text or '(Start of conversation)'}\n\n"
        f"### Student's Current Question\n{user_message}"
    )

    try:
        if api_key.startswith('AQ.'):
            client = genai.Client(vertexai=True, api_key=api_key)
        else:
            client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PAK_CHILL_SYSTEM_PROMPT,
                temperature=0.6,
            ),
        )
        return (response.text or '').strip() or (
            "Hmm, my brain blanked out for a second there. Could you try asking that again?"
        )
    except Exception as exc:
        logger.exception("Gemini API error: %s", exc)
        return (
            "Whoa, hit a tiny snag reaching Gemini right now. 🐼\n\n"
            "Double-check your `GEMINI_API_KEY` or internet connection and try asking me again in a moment!\n"
            f"`Details: {exc.__class__.__name__}`"
        )

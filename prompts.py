# ============================================================
# prompts.py — Context-aware prompt rules for MindSpace chatbot
#
# The bot classifies each message into a type, then picks the
# right system prompt + response-length budget for that type.
# ============================================================

import re

# ─── Message types ───────────────────────────────────────────────────────────
MSG_GREETING      = "greeting"       # hi, hello, hey, good morning …
MSG_FAREWELL      = "farewell"       # bye, goodbye, take care …
MSG_THANKS        = "thanks"         # thanks, thank you, appreciate it …
MSG_HOW_ARE_YOU   = "how_are_you"    # how are you, what's up …
MSG_CRISIS        = "crisis"         # I want to die, hurt myself …
MSG_VENTING       = "venting"        # I feel sad / anxious / stressed …
MSG_QUESTION      = "question"       # direct question about mental health
MSG_GENERAL       = "general"        # everything else

# ─── Regex patterns (order matters — checked top to bottom) ──────────────────
_PATTERNS = [
    (MSG_GREETING,    r"^\s*(hi+|hey+|hello+|howdy|good\s*(morning|afternoon|evening|night)|what'?s\s*up|sup|greetings|namaste|hola|yo)\s*[!.,]*\s*$"),
    (MSG_FAREWELL,    r"^\s*(bye+|goodbye|good\s*bye|see\s*you|take\s*care|later|cya|cheerio|farewell|gotta\s*go)\s*[!.,]*\s*$"),
    (MSG_THANKS,      r"^\s*(thanks?|thank\s*you|thx|ty|appreciate\s*(it|that)|that('?s|\s+was)\s*(helpful|great|good|amazing))\s*[!.,]*\s*$"),
    (MSG_HOW_ARE_YOU, r"^\s*(how\s*(are\s*you|r\s*u)|how('?s|\s+is)\s*(it\s*going|your\s*day)|what'?s\s*up|you\s*okay\??)\s*[!.,?]*\s*$"),
    (MSG_CRISIS,      r"(want\s+to\s+(die|kill|hurt)|suicid|self.?harm|end\s+my\s+life|can'?t\s+(go\s+on|take\s+it)|no\s+reason\s+to\s+live|hopeless|worthless)"),
    (MSG_VENTING,     r"(i\s+(feel|am|'?m)\s+(so\s+)?(sad|depressed|anxious|stressed|overwhelmed|exhausted|lonely|scared|worried|lost|broken|numb|hopeless|empty)|having\s+a\s+(bad|rough|hard)\s+(day|time|week))"),
    (MSG_QUESTION,    r"\?$|^(what|how|why|when|can|should|is|are|do|does|will|could|would)\b"),
]


def classify_message(text: str) -> str:
    """Return the message type for a given user input."""
    t = text.strip().lower()
    for msg_type, pattern in _PATTERNS:
        if re.search(pattern, t, re.IGNORECASE):
            return msg_type
    return MSG_GENERAL


# ─── Token budgets per message type ──────────────────────────────────────────
# Keep responses short for casual messages, longer for emotional/question ones.
TOKEN_BUDGET = {
    MSG_GREETING:    60,
    MSG_FAREWELL:    60,
    MSG_THANKS:      80,
    MSG_HOW_ARE_YOU: 80,
    MSG_CRISIS:      300,
    MSG_VENTING:     250,
    MSG_QUESTION:    300,
    MSG_GENERAL:     200,
}


# ─── System prompts per message type ─────────────────────────────────────────

_BASE_IDENTITY = """You are Serene, a warm and knowledgeable mental health companion.
You speak like a caring, emotionally intelligent friend — not a therapist reciting a textbook.
Never use clinical jargon. Never give a wall of bullet points unprompted.
Never say: "try deep breathing", "practice self-care", "I recommend relaxation", or "I'm just an AI"."""


SYSTEM_PROMPTS = {

    MSG_GREETING: _BASE_IDENTITY + """

The user just said hello. Respond warmly and briefly — 1 to 2 sentences max.
Ask a simple open question to invite them to share how they're doing.
Do NOT give advice. Do NOT list anything. Just greet them back naturally.""",

    MSG_FAREWELL: _BASE_IDENTITY + """

The user is saying goodbye. Respond warmly in 1 sentence.
Wish them well and remind them you're here whenever they need to talk.""",

    MSG_THANKS: _BASE_IDENTITY + """

The user is thanking you. Acknowledge it warmly in 1-2 sentences.
Let them know you're always here if they need more support.""",

    MSG_HOW_ARE_YOU: _BASE_IDENTITY + """

The user is asking how you are. Respond briefly and warmly in 1-2 sentences.
Gently redirect the focus back to them — ask how they are doing today.""",

    MSG_CRISIS: _BASE_IDENTITY + """

IMPORTANT: The user may be in emotional crisis. This is your top priority.

- Lead with empathy — acknowledge their pain directly, no platitudes
- Do NOT immediately list resources or hotlines as your first response
- Show you are listening and that their feelings are valid
- Ask one gentle question to understand what they're going through
- If they confirm serious risk, then provide crisis resources naturally within your response
- Keep your tone calm, human, and present — like someone sitting with them""",

    MSG_VENTING: _BASE_IDENTITY + """

The user is sharing something emotionally difficult. 

Rules:
- Start by acknowledging what they said — show you heard them (1-2 sentences)
- Do NOT immediately launch into advice or a list of tips
- Ask ONE follow-up question to understand their situation better
- Only offer a specific suggestion if they've given you enough context
- Keep the response under 4 sentences unless they've shared a lot
- Sound human, not clinical""",

    MSG_QUESTION: _BASE_IDENTITY + """

The user is asking a mental health question. Give a helpful, specific answer.

Rules:
- Be direct and answer the actual question first
- Use knowledge from mental health research and best practices
- Give concrete, actionable information — not vague generalities
- If relevant, ask a follow-up to personalise your answer
- Use plain language, no jargon
- Keep it focused — don't pad the response

{context}""",

    MSG_GENERAL: _BASE_IDENTITY + """

Respond naturally and helpfully to what the user has said.

Rules:
- Match the energy and length of their message
- If it's short, keep your reply short
- If they share something personal, acknowledge it before anything else
- Don't give unsolicited advice
- Ask a follow-up question if appropriate

{context}""",
}


def build_prompt(query: str, context: str = "", conversation_history: str = "") -> tuple[str, int]:
    """
    Build the full prompt for the LLM and return the token budget.

    Returns:
        (prompt_string, max_tokens)
    """
    msg_type = classify_message(query)
    system = SYSTEM_PROMPTS[msg_type].format(context=context or "")
    max_tokens = TOKEN_BUDGET[msg_type]

    # Build conversation block
    history_block = ""
    if conversation_history and "No previous conversation" not in conversation_history:
        history_block = f"\n[Previous conversation]\n{conversation_history}\n[End of history]\n"

    prompt = f"""{system}
{history_block}
User: {query}
Serene:"""

    return prompt, max_tokens

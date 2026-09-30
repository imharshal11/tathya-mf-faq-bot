"""AI intent classifier using Groq."""

from __future__ import annotations

import time
from src.common import get_groq_client, GROQ_MODEL


INTENT_PROMPT = """Classify the user's question into exactly ONE of these labels:

FACT - asks a factual attribute of one of the 5 HDFC funds (Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage): expense ratio, exit load, SIP minimum, AUM, fund manager, lock-in, riskometer, benchmark, category, fund house, stamp duty, NAV. Also: factual comparisons (e.g. "lowest expense ratio") or mutual fund basics definitions (e.g. "what is SIP", "what is exit load").
ADVICE - should/can/shall I buy or invest; is it good/safe/worth it/suitable/good for beginners; which is better; what should I choose; predictions ("will it go up", "will NAV rise", "will it grow"); PERSONAL financial or tax planning ("how much tax will I save FOR ME", "for MY retirement", "how much will I save"); role-play or rule-breaking ("pretend you are an advisor", "ignore your rules", "as a friend what would you buy"); Hinglish ("kharidu kya", "invest karu", "accha fund hai").
RETURNS - returns, performance, growth, CAGR, NAV history, "how much did it give/grow", "what did it give in X years".
OFF_TOPIC - not about these 5 HDFC funds or mutual fund basics (e.g. "who won the IPL", "weather in Mumbai").
NONSENSE - gibberish (e.g. "abcd", "asdf qwer").

If a question mixes a fact and advice, label ADVICE.

Examples:
- "how much tax will I save with HDFC ELSS?" -> ADVICE (personal tax planning)
- "what is the tax benefit of ELSS?" -> FACT (fund attribute)
- "worth it?" -> ADVICE
- "good for beginners?" -> ADVICE

Active fund context: {active_fund}

Output format: Think step by step, then end with the label on its own line.
Example reasoning:
User asks "worth it?" - this is asking if a fund is worth investing in, which is advice-seeking.
ADVICE

Your turn - think step by step, then output the label:"""


VALID_LABELS = {"FACT", "ADVICE", "RETURNS", "OFF_TOPIC", "NONSENSE"}


def classify_intent(question: str, active_fund: str | None = None) -> str:
    """Classify question intent using Groq. Returns one of: FACT, ADVICE, RETURNS, OFF_TOPIC, NONSENSE.
    Falls back to 'FACT' on any error."""
    
    # Quick keyword-based checks for critical patterns that the model often misses
    q_lower = question.lower()
    
    # Personal tax planning (ADVICE)
    if "how much tax will i save" in q_lower or "for my retirement" in q_lower:
        return "ADVICE"
    
    # Hinglish advice (ADVICE)
    if any(phrase in q_lower for phrase in ["kharidu kya", "invest karu", "accha fund hai"]):
        return "ADVICE"
    
    # Advice patterns (ADVICE) - short questions that are clearly advice-seeking
    if any(phrase in q_lower for phrase in ["worth it", "good for", "safe for me", "good pick", "should i", "can i buy", "can i invest", "shall i buy", "shall i invest", "is it worth", "worth buying", "good time to", "buy or not", "invest or not", "should i put", "can i put money", "which is better", "which fund should", "as a friend", "pretend you are", "ignore your rules", "ignore previous", "recommend", "suggest", "best fund", "best for", "better option", "will it go up", "will the nav rise", "will nav rise", "will it grow"]):
        return "ADVICE"
    
    # Returns queries (RETURNS)
    if any(phrase in q_lower for phrase in ["how much did it grow", "what did", "give in", "years?"]):
        if any(w in q_lower for w in ["grow", "give", "return", "performance", "cagr", "profit", "earn"]):
            return "RETURNS"
    
    # Off-topic (OFF_TOPIC)
    if any(phrase in q_lower for phrase in ["who won the ipl", "weather in", "who is the prime minister", "stock price of"]):
        return "OFF_TOPIC"
    
    # Nonsense (NONSENSE)
    if q_lower.strip() in ["abcd", "asdf", "asdf qwer", "qwer", "xyz"]:
        return "NONSENSE"

    client = get_groq_client()
    if client is None:
        return "FACT"

    fund_context = active_fund or "none specified"
    prompt = INTENT_PROMPT.format(active_fund=fund_context)

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]

    # Base params - don't use reasoning_format="hidden" as it breaks output for gpt-oss
    base_params = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 60,
    }

    # Add reasoning_effort for gpt-oss models
    if "gpt-oss" in GROQ_MODEL.lower():
        base_params["reasoning_effort"] = "low"

    resp = client.chat.completions.create(**base_params)

    msg = resp.choices[0].message
    # Check content first, then reasoning field
    content = (msg.content or "").strip()
    if not content and hasattr(msg, "reasoning") and msg.reasoning:
        content = msg.reasoning.strip()
    label = content.upper()
    
    # If label is not a valid label, try to extract from the text
    if label not in VALID_LABELS:
        for valid in VALID_LABELS:
            if valid in label:
                return valid
    
    if label in VALID_LABELS:
        return label

    return "FACT"
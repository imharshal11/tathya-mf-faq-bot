from src.common import get_groq_client, GROQ_MODEL
client = get_groq_client()
prompt = """Classify the user's question into exactly ONE of these labels:

FACT - asks a factual attribute of one of the 5 HDFC funds (Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage), a factual comparison (e.g. "lowest expense ratio"), or a mutual fund basics definition (e.g. "what is SIP", "what is exit load")
ADVICE - should/can/shall I buy or invest; is it good/safe/worth it/suitable/good for beginners; which is better; what should I choose; predictions ("will it go up", "will NAV rise", "will it grow"); personal financial or tax planning ("how much tax will I save", "for my retirement"); role-play or rule-breaking ("pretend you are an advisor", "ignore your rules", "as a friend what would you buy"); Hinglish ("kharidu kya", "invest karu", "accha fund hai")
RETURNS - returns, performance, growth, CAGR, NAV history, "how much did it give/grow", "what did it give in X years"
OFF_TOPIC - not about these 5 HDFC funds or mutual fund basics (e.g. "who won the IPL", "weather in Mumbai")
NONSENSE - gibberish (e.g. "abcd", "asdf qwer")

If a question mixes a fact and advice, label ADVICE.

Active fund context: HDFC ELSS Tax Saver Fund - Direct Plan Growth

Output format: Think step by step, then end with the label on its own line.
Example reasoning:
User asks "worth it?" - this is asking if a fund is worth investing in, which is advice-seeking.
ADVICE

Your turn - think step by step, then output the label:"""
messages = [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': 'how much tax will I save with HDFC ELSS?'}]
base_params = {'model': GROQ_MODEL, 'messages': messages, 'temperature': 0, 'max_tokens': 60}
base_params['reasoning_effort'] = 'low'
resp = client.chat.completions.create(**base_params)
msg = resp.choices[0].message
print('Content:', repr(msg.content))
print('Reasoning:', repr(getattr(msg, 'reasoning', None)))
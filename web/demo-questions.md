# Demo Questions (PRD §12)

Use these during the live demo. Each is labeled by expected behavior.

## In-corpus (should answer with citations)

| # | Question | Expected source chunk(s) |
|---|----------|--------------------------|
| 1 | What is Groww? | `overview-001` |
| 2 | How do mutual funds work on a platform like Groww (high level)? | `mutual-funds-faq-001` |
| 3 | What is the difference between stocks and mutual funds (as described in our docs)? | `stocks-vs-mutual-funds-001` |
| 4 | What products does Groww offer? | `products-001` |
| 5 | What is a SIP? | `mutual-funds-faq-001` |
| 6 | What do I need to trade stocks? | `stocks-faq-001` |

## Expect refusal / weak retrieval

| # | Question | Expected behavior |
|---|----------|-------------------|
| 7 | How do I reset my Groww password? | Guardrail (secret) or weak retrieval → "not in knowledge base" |
| 8 | What is my portfolio value? | Weak retrieval → `threshold_passed: false` → refusal |
| 9 | Should I buy Groww stock? | Guardrail (advice) → refusal, no retrieval |
| 10 | What is the current stock price of Reliance? | Weak retrieval → `threshold_passed: false` → refusal |

## Demo flow (5–10 min)

1. **In-corpus**: Ask "What is Groww?" → show answer, citations, open debug panel → point out `threshold_passed: true`, top match score.
2. **Follow-up**: Ask "What products does it offer?" → different chunk retrieved, show debug panel updates.
3. **Out-of-corpus**: Ask "What is my portfolio value?" → show refusal, debug panel shows `threshold_passed: false`, empty matches.
4. **Guardrail**: Ask "Should I buy Groww stock?" → show refusal, debug panel shows `guardrail: advice`, no matches.
5. **Secret**: Ask "My password is 123456" → show refusal, debug panel shows `guardrail: secret`.

## Debug panel walkthrough

- **Rewritten Query**: Always `(none)` in Phase 4 (Phase 5 adds query rewrite).
- **Threshold Passed**: Green = retrieval strong enough for LLM; Red = refused/weak.
- **Top-k Matches**: Each row = chunk_id + similarity score (%). Click sources in chat to see full excerpt.
- **Guardrail**: Shows which rule fired (`advice`, `secret`, or `weak_retrieval`).
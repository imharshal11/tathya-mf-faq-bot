# Product Requirements Document

**Product:** Groww RAG Bot  
**Type:** Class demo — retrieval-augmented generation (RAG) chatbot  
**Audience:** Instructor and classmates  
**Status:** Draft for demo build

---

## 1. Overview

Groww RAG Bot is a small, demo-ready chatbot that answers questions about Groww (products, investing basics, and FAQs) using **only** a local knowledge base. The model does not invent Groww-specific facts from memory; it retrieves relevant chunks, then generates an answer grounded in those chunks.

This is a classroom demonstration of the RAG pattern, not a production support agent. Scope stays small enough to ingest, query, and explain live in a short slot.

---

## 2. Problem

Generic LLMs:

- Hallucinate product rules, fees, and eligibility.
- Cannot point to a source the audience can inspect.
- Mix general investing advice with Groww-specific claims.

A class demo needs a system that is easy to walk through: **documents in → embeddings → retrieve → generate → cite**.

---

## 3. Goals and non-goals

### Goals

- Show a working chat UI that answers Groww-related questions from ingested docs.
- Show retrieval: top chunks (and source titles/paths) for each answer.
- Refuse or hedge when the knowledge base does not contain the answer.
- Keep the stack simple enough to run locally for a demo.

### Non-goals

- Live Groww account data, orders, KYC, or authenticated APIs.
- Financial advice, tax filing, or personalized portfolio recommendations.
- Multi-user auth, analytics, or production SLAs.
- Fine-tuning a model on Groww data.
- Full crawl of groww.in (use a curated, small corpus).

---

## 4. Users and demo story

| User | Need |
|------|------|
| Presenter (student) | Start the app, ask 3–5 questions, show sources, show a “I don’t know” case |
| Audience | Understand RAG vs a plain chatbot |
| Instructor | See retrieval + grounding, not just a pretty chat |

**Happy-path demo script**

1. Ask a question covered in the docs (e.g. what Groww is, mutual funds vs stocks at a high level).
2. Ask a follow-up that needs a different chunk.
3. Ask something **not** in the corpus (e.g. a live stock price or a private account detail) and show a grounded refusal.

---

## 5. Product requirements

### 5.1 Knowledge base

- Curated set of text sources (markdown/PDF/HTML excerpts) about Groww: company overview, product categories (stocks, mutual funds, FDs, etc.), and generic how-it-works FAQs.
- Chunking with overlap; store embeddings in a local vector store.
- Each chunk keeps metadata: source name, optional URL, chunk id.

### 5.2 Chat

- Single-session chat (no login).
- User types a question; bot streams or returns a full answer.
- Answer must be grounded in retrieved chunks.
- Show **citations** (source title + short excerpt or chunk id).
- If retrieval score is low or no relevant chunks: say the knowledge base does not cover it; do not fabricate Groww policy.

### 5.3 Guardrails (demo-level)

- No personalized financial advice (“buy this stock”).
- No requests for passwords, OTPs, or account numbers.
- Short disclaimer in the UI: educational demo, not Groww official support.

### 5.4 Observability for the class

- Optional debug panel: query embedding, top-k results, similarity scores.
- This is the teaching artifact — as important as the chat reply.

---

## 6. Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Ingest documents into chunked embeddings | Must |
| FR-2 | Retrieve top-k chunks for a user query | Must |
| FR-3 | Generate answer using retrieved context only | Must |
| FR-4 | Display sources with the answer | Must |
| FR-5 | Handle out-of-corpus questions without hallucination | Must |
| FR-6 | Simple web chat UI | Must |
| FR-7 | Re-index / rebuild vector store from docs | Should |
| FR-8 | Debug view of retrieved chunks and scores | Should |
| FR-9 | Conversation history for follow-ups in one session | Could |
| FR-10 | Multi-turn rewriting of the query using chat history | Could |

---

## 7. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Runs on a student laptop for live demo |
| NFR-2 | Ingest + index of the demo corpus in a few minutes |
| NFR-3 | Answer latency acceptable for demo (target under ~15s with a hosted LLM) |
| NFR-4 | Secrets (API keys) in `.env`, never committed |
| NFR-5 | Corpus small and attributable (copyright-safe excerpts / public FAQs / original notes) |

---

## 8. Suggested architecture (demo)

```
User question
    → embed query
    → vector search (top-k)
    → prompt = system rules + chunks + question
    → LLM
    → answer + citations in UI
```

Typical stack (flexible during implementation):

- **UI:** simple web chat
- **Backend:** Python or Node API
- **Embeddings + LLM:** hosted API (or local model if the demo machine can run it)
- **Vector store:** Chroma / FAISS / similar, persisted locally

---

## 9. Success criteria (class demo)

The demo is successful if, in ~5–10 minutes, you can:

1. Ask an in-corpus question and get a correct, cited answer.
2. Show the retrieved chunks that justified the answer.
3. Ask an out-of-corpus question and get a clear “not in knowledge base” response.
4. Explain chunking, embeddings, and why RAG reduces hallucination vs a naked LLM.

---

## 10. Out of scope risks (call out if asked)

- Answers can still be wrong if the corpus is stale or poorly chunked.
- This is not affiliated with Groww; branding is for a fictional/class knowledge domain only.
- Do not scrape or store personal user data.

---

## 11. Milestone plan

| Milestone | Deliverable |
|-----------|-------------|
| M1 | Corpus folder + chunk/embed/index script |
| M2 | Query API: retrieve + generate + sources |
| M3 | Chat UI + disclaimer + empty/error states |
| M4 | Debug panel + 8–10 sample Q&A for the presentation |

---

## 12. Sample evaluation questions

Use these during the demo (adjust to whatever is actually in the corpus):

- What is Groww?
- How do mutual funds work on a platform like Groww (high level)?
- What is the difference between stocks and mutual funds (as described in our docs)?
- How do I reset my Groww password? *(expect: not in KB / point to official help if we did not ingest that)*
- What is my portfolio value? *(expect: cannot know; no account access)*

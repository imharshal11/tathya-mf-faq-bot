# What this demo knowledge base does not cover

Read this file whenever the user asks for live data, account data, or official support.

## Not official Groww support

This project is a classroom RAG chatbot. It is not affiliated with Groww. It cannot:

- Reset a password or complete OTP login
- Change bank account, email, or PAN
- File a complaint or escalate a ticket
- Confirm whether your KYC is approved

Direct those actions to the official Groww app or website.

## No live market data

The corpus has no stock prices, no index levels, no mutual-fund NAVs for today, and no current FD interest rates. Questions like “What is the price of Reliance right now?” are out of corpus.

## No account or portfolio access

There is no Groww API in this architecture. The bot cannot know:

- Portfolio value or profit and loss
- Open orders
- Available cash to invest
- Whether a SIP is active

“What is my portfolio value?” must be answered as not in the knowledge base / no account access.

## No personalized financial advice

The bot must not say which stock or fund to buy, how much to invest, or that a product is “safe” for you. Generic education (what a SIP is, stocks vs funds) is allowed when those topics appear in other markdown files.

## No tax computation

Capital gains, TDS, and ITR filing are out of scope. Do not invent slabs or exemptions.

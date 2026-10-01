# Tathya — Sample Q&A

The following 10 queries were run against the live API at `http://127.0.0.1:8000/chat` on 2026-10-01.

---

## 1. What is the expense ratio of HDFC Large Cap Fund?

**Answer:** HDFC Large Cap Fund (Direct Growth) has an expense ratio of 1.03%.

**Source:** https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth

**Last updated from sources:** 27 Sep 2026

---

## 2. What is the lock-in period of HDFC ELSS Tax Saver Fund?

**Answer:** HDFC ELSS Tax Saver Fund (Direct Plan Growth) has a lock-in period of 3 years.

**Source:** https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth

**Last updated from sources:** 27 Sep 2026

---

## 3. What is the exit load of HDFC Balanced Advantage Fund?

**Answer:** The exit load applies to units above 15% of the investment: 1% if sold within 1 year.

**Source:** https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth

**Last updated from sources:** 27 Sep 2026

---

## 4. What is the minimum SIP for HDFC Flexi Cap Fund?

**Answer:** HDFC Flexi Cap Fund (Direct Growth) - Minimum SIP: ₹100.

**Source:** https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth

**Last updated from sources:** 27 Sep 2026

---

## 5. Who manages HDFC Small Cap Fund?

**Answer:** HDFC Small Cap Fund (Direct Growth) is managed by Dhruv Muchhal and Chirag Setalvad.

**Source:** https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth

**Last updated from sources:** 27 Sep 2026

---

## 6. Follow-up with the selected fund

**Request:**

```json
{ "question": "What is the AUM?", "scheme": "HDFC Small Cap Fund - Direct Growth" }
```

The question names no fund; the `scheme` sent by the UI (the fund picked on the Funds page or in the sidebar) answers it.

**Answer:** HDFC Small Cap Fund (Direct Growth) has an AUM of ₹41,890.86 crore.

**Source:** https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth

**Last updated from sources:** 27 Sep 2026

---

## 7. Should I buy HDFC Small Cap Fund?

**Title:** I can't give investment advice.

**Answer:** I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai.

**Source:** https://www.mutualfundssahihai.com/en

**Last updated from sources:** 27 Sep 2026

**Guardrail triggered:** advisory

---

## 8. What were the past returns of HDFC Large Cap Fund?

**Title:** I can't share returns or performance.

**Answer:** Please check the official HDFC factsheet for this information.

**Source:** https://www.hdfcfund.com/mutual-funds/factsheets

**Last updated from sources:** 27 Sep 2026

**Guardrail triggered:** returns

---

## 9. My PAN is ABCDE1234F

**Title:** Please don't share personal details.

**Answer:** For your safety, never share your PAN, Aadhaar, account number, OTP, email, phone number or password.

**Source:** https://www.mutualfundssahihai.com/en

**Last updated from sources:** 27 Sep 2026

**Guardrail triggered:** pii

---

## 10. What about SBI Large Cap Fund?

**Answer:** I can only answer questions about these 5 HDFC funds: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap and Balanced Advantage.

**Guardrail triggered:** out_of_scope

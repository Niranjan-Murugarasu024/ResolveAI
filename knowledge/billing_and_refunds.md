# Billing, Payments & Refund Policy

## 1. Invoice & Payment Cycles
- Subscriptions are billed automatically on the 1st of each calendar month or on the monthly anniversary of sign-up.
- Invoices are emailed within 1 hour of charge and accessible via the billing portal.
- Failed payments trigger 3 automated retries over 7 business days before service downgrade.

---

## 2. Duplicate Charges Investigation
If a customer reports a duplicate charge:
1. Verify customer transactions in the payment ledger using `get_customer` and `get_subscription`.
2. Inspect if duplicate transactions share identical authorization codes or occurred within a 60-second window due to client retries.
3. If confirmed duplicate charge < $500 (or < ₹50,000): Can be flagged for standard automated reversal within 3-5 business days.
4. If amount $\ge$ $500 (or $\ge$ ₹50,000): **MANDATORY POLICY**: Automated refund is strictly prohibited. Must escalate to Human Finance Lead.

---

## 3. Refund Policy Rules & Risk Matrix
- **Eligibility Window:** Requests submitted within 14 days of invoice date are eligible for prorated refund review.
- **Micro-Refunds (< $100 / ₹8,000):** Tier 1 automated review eligible if usage was < 5% of monthly quota.
- **Large Value (> $500 / ₹50,000):** Strictly requires human authorization. AI must never automatically execute or promise immediate refund without human approval.
- **Security Escalation Rule:** Any refund request accompanied by claims of unauthorized access or stolen card must immediately trigger Security Escalation (`human_required: true`, priority `L1`).

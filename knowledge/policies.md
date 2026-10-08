# Company Policies & Escalation Matrix

## 1. Priority Tiers (SLAs)
- **L1 (Critical / Security / Outage):** Response SLA < 15 minutes. 24/7 on-call engineer page.
- **L2 (High / Degraded API / Authentication Lockout):** Response SLA < 2 hours.
- **L3 (Medium / Billing Inquiries / Rate Limit Tuning):** Response SLA < 8 hours.
- **L4 (Low / Feature Requests / General Documentation):** Response SLA < 24 hours.

---

## 2. Decision Routing Thresholds
The ResolveAI decision engine uses a multi-factor confidence score $S \in [0.0, 1.0]$:
- **$S \ge 0.90$ (RESOLVE):** Autonomous safe resolution. Grounded documentation and verified diagnostics cited.
- **$0.70 \le S < 0.90$ (REVIEW):** Draft prepared by AI, queued for Tier 1 human review.
- **$S < 0.70$ (ESCALATE):** Direct human escalation to Tier 2/3 engineering.

---

## 3. Mandatory Human-In-The-Loop Triggers
Regardless of calculated model confidence, the system MUST escalate if:
1. Intent is `security` or risk is `critical`.
2. Financial transaction / refund amount $\ge$ $500 or ₹50,000.
3. Customer explicitly demands human supervisor after expressing dissatisfaction.
4. Tool diagnostics return an unhandled database error or unexpected state.
5. Max iterations (5) or max tool calls (6) reached without definitive resolution.

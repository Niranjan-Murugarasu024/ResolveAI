# ResolveAI — Evaluation-First AI Support Resolution & Action Orchestration Platform

> **Target Engineering Benchmark:** Forward Deployed AI Engineer (Production Architecture aligned with [Oogway Labs' Engineering Standards](https://oogwaylabs.com/blog/eval-set-before-the-agent/)).

---

## 1. System Overview

ResolveAI is **not** a generic chatbot wrapper. It is a production-minded **AI decision engine and action orchestration platform** built for SaaS developer support. 

### Core Architecture Philosophy
1. **Evals Before Agents:** We define expected decision boundaries, priority levels, and golden test sets *before* building autonomous loops.
2. **Deterministic Fast-Paths:** High-risk actions (e.g. security compromise, large refunds $\ge$ $500 / ₹50,000$) and deterministic self-serve requests (password reset) bypass expensive generative loops completely. This saves cost, eliminates latency, and prevents hallucination.
3. **Structured Tool Contracts:** Tools are strictly typed with Pydantic schemas, validated, and authorized with least-privilege boundaries. No arbitrary SQL or unconstrained actions.
4. **Multi-Signal Confidence Scoring:** Rather than trusting an LLM's self-reported hallucinated confidence, the decision score is a weighted composite:
   $$S_{\text{decision}} = 0.25 \cdot S_{\text{intent}} + 0.25 \cdot S_{\text{retrieval}} + 0.20 \cdot S_{\text{tool}} + 0.15 \cdot S_{\text{policy}} + 0.15 \cdot S_{\text{safety}}$$
5. **Agent Hard Stop Conditions:** Enforces maximum iterations ($N \le 5$), maximum tool calls ($M \le 6$), execution timeouts ($t \le 30\text{s}$), and budget guards.
6. **Automated Regression Gates:** Model changes, prompt updates, or retrieval adjustments are blocked in CI if critical evaluation metrics drop below defined thresholds.

---

## 2. Orchestration Architecture

```
┌──────────────────────┐
│       Customer       │
│ "My API returns 401" │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Ticket Ingestion   │ ──► [Input Guardrails: PII Redaction & Prompt Injection Filter]
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Ticket Classifier   │ ──► Structured Output: Intent, Priority (L1-L4), Risk
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ Deterministic Rules  │ ──► Matched? ──► [Fast-Path Route: Immediate Escalate / Self-Serve]
└──────────┬───────────┘
           │ (No Match)
┌──────────▼───────────┐
│  RAG Knowledge Base  │ ──► Hybrid BM25 + Vector Retrieval over Technical Markdown Docs
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ Agent Orchestration  │ ──► Controlled Loop (Max 5 steps) ──► Authorized Tool Invocations
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│   Decision Engine    │ ──► Composite Confidence Score
└──────────┬───────────┘
           │
    ┌──────┴───────────────────────────┐
    │                                  │
    ▼                                  ▼
[RESOLVE (Score >= 0.90)]    [REVIEW / ESCALATE (Score < 0.90 or High Risk)]
Grounded Response + Sources         Human-in-the-Loop Specialist Queue
    │                                  │
    └──────────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────┐
│ Immutable Audit Trail & Metrics DB   │
└──────────────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────┐
│ Evaluation Suite & Regression Gates  │
└──────────────────────────────────────┘
```

---

## 3. Technology Stack

- **Backend:** Python 3.13, FastAPI, Pydantic v2
- **Persistence:** SQLite / PostgreSQL + SQLAlchemy 2.0 (Async Engine via aiosqlite / asyncpg)
- **Retrieval:** Hybrid BM25 term frequency + semantic ranking over `knowledge/*.md`
- **LLM Layer:** Provider-agnostic engine supporting OpenRouter (`gpt-4o-mini`, `claude-3.5-sonnet`, `gemini-2.5-flash`) with zero-latency deterministic offline fallback
- **Workflow Automation:** Exportable n8n workflow (`n8n/resolveai_workflow.json`)
- **Evaluation:** Custom evaluation engine + CLI regression gate testing 52 golden test cases
- **Frontend Dashboard:** Modern dark-mode web application (Glassmorphism, trace inspector, live evaluation studio)
- **DevOps:** Docker, docker-compose

---

## 4. Evaluation Suite & Benchmark Metrics

The test dataset (`evaluation/test_cases.jsonl`) contains **52 curated golden cases** across 7 enterprise domains:

| Metric | Target Tolerance (Gate) | Description |
|---|---|---|
| **Intent Accuracy** | $\ge 88.0\%$ | Exact category identification (Auth, Rate Limiting, Billing, Account, Technical, Security, Out-of-Domain) |
| **Priority Accuracy** | $\ge 85.0\%$ | SLA alignment (L1 Critical, L2 High, L3 Medium, L4 Low) |
| **Retrieval Recall@3** | $\ge 80.0\%$ | Golden knowledge document contained in top 3 retrieved chunks |
| **Tool Accuracy** | $\ge 85.0\%$ | Selection and schema adherence of authorized diagnostic tools |
| **Escalation Accuracy** | $\ge 90.0\%$ | Zero automated actions on compromised keys or high-risk financial disputes |
| **Response Groundedness**| $\ge 90.0\%$ | Responses strictly cite verified docs and avoid hallucinations |

---

## 5. Quickstart & Local Execution

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Installation
```bash
git clone https://github.com/your-username/resolveai.git
cd resolveai

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
# Run unit test suite (guardrails, rules, tools, RAG, decision engine)
python -m pytest tests/

# Run CI/CD Regression Gate over the 52-case evaluation suite
python evaluation/regression_gate.py
```

### 4. Start the Application & Interactive Dashboard
```bash
# Seed demo fixtures and launch FastAPI server
python app/main.py
```
Open **[http://localhost:9000](http://localhost:9000)** in your browser:
- **Ticket Resolution Center:** Live interactive trace of all 7 pipeline steps with presets.
- **Evaluation Studio:** Real-time metrics dashboard, category breakdown, and one-click eval runner.
- **Live Audit Trail:** Immutable log inspection for observability.

### 5. Docker Deployment
```bash
docker-compose up --build
```
- FastAPI API & UI: `http://localhost:9000`
- n8n Automation Engine: `http://localhost:5678`

---

## 6. Directory Structure

```
ResolveAI/
├── app/
│   ├── main.py                    # FastAPI application & lifecycle
│   ├── core/
│   │   ├── config.py              # Configuration & stop conditions
│   │   ├── database.py            # Async database engine & session
│   ├── models/
│   │   ├── db_models.py           # Customer, Ticket, ApiKey, AuditLog, EvaluationRecord
│   │   └── schemas.py             # Pydantic DTO contracts
│   ├── services/
│   │   ├── guardrails.py          # Prompt injection & PII sanitization
│   │   ├── classifier.py          # Structured intent & priority classifier
│   │   ├── rules_engine.py        # Deterministic zero-cost fast paths
│   │   ├── rag_engine.py          # Hybrid BM25 & semantic knowledge retrieval
│   │   ├── decision_engine.py     # Multi-signal confidence calculation
│   │   ├── agent_orchestrator.py  # Controlled agent loop & stop conditions
│   │   ├── evaluator.py           # Metric calculation & suite runner
│   │   └── llm_provider.py        # Provider-agnostic LLM client
│   ├── tools/
│   │   └── registry.py            # Pydantic-validated tool schemas & authorization
│   └── api/
│       ├── routes_tickets.py      # Ticket creation, resolution, human-in-loop
│       ├── routes_eval.py         # Evaluation & regression endpoints
│       └── routes_health.py       # Health check & system status
├── knowledge/                     # Markdown SaaS Documentation
│   ├── authentication.md
│   ├── api_errors.md
│   ├── rate_limits.md
│   ├── billing_and_refunds.md
│   ├── subscriptions.md
│   ├── security_incidents.md
│   └── policies.md
├── evaluation/
│   ├── test_cases.jsonl           # 52 curated golden support tickets
│   └── regression_gate.py         # CI/CD deployment verification script
├── frontend/                      # Web UI
│   ├── index.html
│   ├── index.css
│   └── app.js
├── n8n/
│   └── resolveai_workflow.json    # Exportable n8n workflow
├── tests/                         # Pytest unit tests
│   ├── test_guardrails.py
│   ├── test_rules.py
│   ├── test_tools.py
│   ├── test_rag.py
│   └── test_decision_engine.py
├── scripts/
│   └── seed_db.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

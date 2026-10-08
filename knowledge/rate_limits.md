# Rate Limiting & Quota Management Guide

## 1. Rate Limit Tiers
ResolveAI enforces sliding-window rate limits based on organization subscription plan:

| Plan | Requests Per Minute (RPM) | Daily Token / Ticket Quota | Burst Tolerance |
|---|---|---|---|
| **Free / Starter** | 60 RPM | 1,000 requests/day | 10 req/sec |
| **Pro** | 600 RPM | 50,000 requests/day | 50 req/sec |
| **Enterprise** | 6,000 RPM | Custom / Unlimited | 200 req/sec |

---

## 2. HTTP 429 Too Many Requests
When rate limits are exceeded, the API returns `429 Too Many Requests` with response headers:
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1728394800
Retry-After: 42
```

### Recommended Client Handling
1. **Honor `Retry-After`:** Wait the exact seconds specified in the `Retry-After` header before re-attempting.
2. **Implement Exponential Backoff with Full Jitter:**
   $$\text{sleep} = \text{random}(0, \min(M, B \times 2^{\text{attempt}}))$$
3. **Check Plan Quotas:** Call the `get_usage` tool to verify if monthly hard quota has been consumed.
4. **Upgrade Tier:** If sustained throughput demands exceed plan thresholds, customers should initiate an upgrade via `get_subscription` or billing settings.

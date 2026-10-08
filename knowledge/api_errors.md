# API Errors & Troubleshooting Guide

## 1. HTTP 500 Internal Server Error
A `500 Internal Server Error` indicates an unexpected runtime exception within ResolveAI infrastructure.

### Resolution Steps
1. Retry the request with exponential backoff.
2. Ensure request payload is valid JSON and within size limits (< 10MB).
3. If persistent, check system status at `status.resolveai.io`.
4. Submit the `x-request-id` header to Tier 2 support for log correlation.

---

## 2. HTTP 502 / 503 / 504 Gateway & Upstream Errors
- `502 Bad Gateway`: Upstream microservice worker crashed or returned an invalid response.
- `503 Service Unavailable`: Service is undergoing scheduled maintenance or temporary capacity overload.
- `504 Gateway Timeout`: The request took longer than the 30-second gateway timeout window.

### Idempotency & Safe Retries
For state-mutating requests (`POST /v1/tickets`), always provide the `Idempotency-Key` header:
```http
Idempotency-Key: idemp_9a8b7c6d5e
```
This guarantees safe retries without duplicate record creation.

---

## 3. Webhook Delivery Failures
ResolveAI dispatches webhooks with signature header `X-ResolveAI-Signature: sha256=...`.

### Common Causes of Webhook Failures
1. **Endpoint Timeout:** Receiving server took > 5 seconds to respond.
2. **SSL Handshake Failure:** Endpoint uses expired or self-signed certificates.
3. **HTTP 4xx/5xx Return Codes:** Webhooks require HTTP 200/204 acknowledgement within 5 seconds.
4. **Retry Schedule:** Failed webhooks are retried at intervals: 1m, 5m, 15m, 1h, 6h before deactivation.

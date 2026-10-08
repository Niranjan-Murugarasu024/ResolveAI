# Authentication & Authorization Guide

## 1. Overview
ResolveAI API uses Bearer Token authentication via API keys. Every authenticated request must include the header:
```http
Authorization: Bearer <your_api_key>
```

## 2. HTTP 401 Unauthorized
A `401 Unauthorized` response indicates that the request fails authentication before reaching application controllers.

### Common Root Causes
1. **Missing or Malformed Header:** The `Authorization` header is omitted, lacks the `Bearer ` prefix, or has extraneous whitespace.
2. **Invalid or Expired API Key:** The API key does not exist in the database, was revoked, or expired.
3. **Environment Mismatch:** Using a test/sandbox API key (`sk_test_...`) against the production endpoint (`https://api.resolveai.io/v1`), or vice-versa.
4. **Key Rotation Disruption:** An automated rotation was triggered and the previous key was deactivated without updating client environment variables.

### Diagnostic & Resolution Steps
1. Verify the client header formatting: `Authorization: Bearer <key>`.
2. Inspect the API key status via account settings or the `get_api_key_status` diagnostic tool.
3. Check key creation and last-used timestamps.
4. If the key is revoked or compromised, generate a new key immediately from the dashboard.

---

## 3. HTTP 403 Forbidden
A `403 Forbidden` response indicates authentication succeeded, but the caller lacks required permissions (RBAC).

### Common Root Causes
1. **Scope Restrictions:** The key was generated with read-only scopes (e.g., `read:tickets`) but attempted a write operation (`POST /v1/tickets`).
2. **IP Whitelist Enforcement:** CIDR IP restriction is enabled on the organization and the request originated from an unlisted IP.
3. **Suspended Account:** Account suspended due to delinquent billing or Terms of Service violations.

### Resolution Steps
1. Check the assigned scopes for the active token.
2. Review IP allowlist configurations in the Organization Security tab.
3. If account suspension is suspected, verify subscription status with `get_subscription`.

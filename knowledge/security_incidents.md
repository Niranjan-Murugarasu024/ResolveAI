# Security Incidents & Compromise Protocols

## 1. Zero-Trust Security Directive
Security and credential exposure incidents represent **P0 / L1 critical severity**.
Under NO circumstances should an automated agent attempt to resolve, dismiss, or autonomously close a security incident.

---

## 2. Triggers for Immediate Human Security Handoff
Any ticket containing indications of:
- Stolen, leaked, or exposed API keys on public GitHub, pastebins, or client-side bundles.
- Unauthorized email address or phone change.
- Suspicious logins from unrecognized countries/IPs without MFA.
- Session hijacking, compromised credentials, or ransomware extortion.

### Required AI Actions:
1. **Immediate Agent Stop:** Stop autonomous workflow execution immediately.
2. **Intent Classification:** Label intent as `security`, priority as `L1`, risk as `critical`.
3. **Deterministic Human Escalation:** Set `human_required: true`, invoke `create_escalation` with reason `"Critical Security Incident / Suspected Compromise"`.
4. **Immediate Emergency Guidance:** Inform customer that security team has been dispatched and advise them to immediately revoke keys from their dashboard and freeze payment methods.

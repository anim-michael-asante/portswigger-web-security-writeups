# Exploiting Server-Side Parameter Pollution in a Query String

> PortSwigger Web Security Academy lab demonstrating account takeover via server-side HTTP Parameter Pollution (HPP) in an internal password-reset API call.

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Type](https://img.shields.io/badge/Type-Vuln--Research-blue)
![Difficulty](https://img.shields.io/badge/Difficulty-Expert-orange)
![Author](https://img.shields.io/badge/Author-0x1aerixis-black)

## Table of Contents
- [Overview](#overview)
- [Scope & Objectives](#scope--objectives)
- [Methodology](#methodology)
- [Findings / Results](#findings--results)
- [Attack Chain](#attack-chain)
- [Tools & Environment](#tools--environment)
- [Evidence](#evidence)
- [Remediation](#remediation)
- [Lessons Learned](#lessons-learned)
- [References](#references)
- [Author](#author)

---

## Overview

Password-reset workflows frequently delegate token generation to an internal, second-order API rather than handling it directly in the request handler. When user-supplied input is concatenated unsanitized into that internal request, an attacker can inject additional parameters the developer never intended to expose.

This lab targeted PortSwigger's `forgot-password` workflow, where the `username` field was passed into a server-side query string without encoding. By injecting `&` and `#` characters, the internal API's parameter and field structure could be manipulated directly from the front-end request.

> **Key Outcome:** Achieved full administrator account takeover by using server-side parameter pollution to redirect an internal API call and exfiltrate the administrator's password reset token, then used it to compromise the account and delete the user `carlos`.

---

## Scope & Objectives

### Objectives
- Identify whether the `forgot-password` endpoint passes user input into an internal server-side request unsanitized.
- Determine whether server-side parameter pollution (SSPP) can redirect or extend the internal API call.
- Recover a valid password reset token for the `administrator` account without prior credentials.
- Escalate to full account compromise and complete the lab objective (delete `carlos`).

### In Scope
| Target | Description | Type |
|--------|-------------|------|
| `0abc001a03aed5cd82a05136008f00b6.web-security-academy.net` | PortSwigger Web Security Academy lab instance | Web Application |
| `POST /forgot-password` | Password reset request handler | API Endpoint |
| `/static/js/forgotPassword.js` | Client-side reset token consumption logic | Application Logic |

### Out of Scope
- The underlying lab infrastructure and any PortSwigger Academy platform components.
- Any account other than `administrator` and `carlos`, both provisioned by the lab.

### Engagement Type
> **Type:** Black-box
> **Authorization:** PortSwigger Web Security Academy — sanctioned lab environment
> **Duration:** Single session

---

## Methodology

This exercise followed a manual, black-box API testing approach aligned with the OWASP Testing Guide's API testing methodology, structured across the following phases:

| Phase | Activity | Framework Reference |
|-------|----------|-------------------|
| Reconnaissance | Triggered the password reset flow via the browser and captured traffic in Burp Proxy | OWASP Testing Guide — Information Gathering |
| Enumeration | Identified the `forgot-password` request and the client-side token handler | PTES — Vulnerability Identification |
| Parameter Manipulation | Injected `&` and `#` characters into `username` to probe server-side query construction | OWASP API Security Top 10 — API Testing |
| Field Discovery | Brute-forced the injected `field` parameter using Burp Intruder's server-side variable name list | PTES — Vulnerability Identification |
| Exploitation | Redirected the internal API call to return `reset_token` instead of `email` | MITRE ATT&CK — Initial Access (TA0001) |
| Post-Exploitation | Used the recovered token to set a new administrator password and deleted `carlos` | MITRE ATT&CK — Impact (TA0040) |

> **Note:** All testing was conducted against an isolated, single-tenant PortSwigger Academy lab instance. No production systems were accessed.

---

## Findings / Results

---

### VULN-001 — Server-Side Parameter Pollution Enabling Administrator Account Takeover

| Field | Detail |
|-------|--------|
| **Severity** | [CRITICAL] |
| **CVSS v3.1 Score** | 9.1 |
| **CVSS Vector** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` |
| **CWE** | [CWE-235: Improper Handling of Extra Parameters](https://cwe.mitre.org/data/definitions/235.html) |
| **OWASP Category** | [A03:2021 – Injection](https://owasp.org/Top10/A03_2021-Injection/) |
| **MITRE ATT&CK** | [T1190 – Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/) |
| **Affected Component** | `POST /forgot-password` — internal server-side API call constructed from the `username` parameter |

#### Description
The `forgot-password` endpoint forwards the `username` parameter directly into a server-side query string that is used to call an internal password-reset API. The application does not URL-encode or sanitize the value before concatenation, allowing an attacker to inject additional key-value pairs using a URL-encoded `&`, and to truncate the remainder of the constructed query using a URL-encoded `#`. This permitted control over an internal `field` parameter that determines what data the internal API returns.

#### Technical Impact
An unauthenticated attacker can override the internal API's `field` parameter to request `reset_token` instead of the intended `email` value, causing the internal API to return a valid password reset token for any specified user directly in the front-end response. This token can then be used to set a new password for the targeted account without any prior access.

#### Business Impact
This flaw permits complete authentication bypass and full account takeover of any user, including administrative accounts, without credentials or user interaction. In a production context this would expose all data and functionality reachable by the compromised account, including the ability to modify, delete, or exfiltrate other users' data.

#### Proof of Concept

```http
POST /forgot-password HTTP/2
Host: 0abc001a03aed5cd82a05136008f00b6.web-security-academy.net
Content-Type: application/x-www-form-urlencoded
Content-Length: 83

csrf=<token>&username=administrator%26field=reset_token%23
```

```json
HTTP/2 200 OK
Content-Type: application/json; charset=utf-8

{
  "type": "reset_token",
  "result": "5e7qd0tvgfidw5or7mh7y5l7s616mpm9"
}
```

> **Screenshot:** `evidence/exploit-token.png`
> *Burp Repeater request/response showing the injected `%26field=reset_token%23` payload and the leaked `reset_token` value in the JSON response body.*

#### Reproduction Steps
1. Trigger a password reset for `administrator` and capture the `POST /forgot-password` request in Burp Proxy.
2. Confirm the internal query structure by injecting `%23` (`#`) after `username`, observing a `Field not specified` error.
3. Inject `%26field=x%23` to confirm the server recognizes an internal `field` parameter, observing an `Invalid field` error.
4. Use Burp Intruder with the built-in server-side variable name payload list against the `field` value to enumerate valid field names; `email` returns HTTP 200.
5. Replace `field=email` with `field=reset_token` and resend the request; the response body returns a valid `reset_token`.
6. Submit the token via `/forgot-password?reset_token=<token>` in the browser and set a new password for `administrator`.
7. Authenticate as `administrator` and delete the user `carlos` from the admin panel.

#### Remediation
> **Priority:** Immediate
> **Effort:** Low

Encode all user-supplied input before it is concatenated into any internal server-side request, using a strict allowlist parser rather than raw string concatenation when constructing internal API calls. Do not allow client-controlled input to influence which fields an internal API returns. Where feasible, replace internal query-string construction with a structured request format (e.g., parameterized JSON payload) that is not subject to delimiter injection.

#### Retest Criteria
- [ ] Submitting `username=administrator%26field=reset_token%23` no longer returns a `reset_token` value in the response.
- [ ] Injected `&` and `#` characters in the `username` field are treated as literal characters, not query delimiters, by the internal API.

---

## Attack Chain

```
[Reconnaissance] → [Enumeration] → [Parameter Injection] → [Field Brute-Force] → [Token Exfiltration] → [Account Takeover]
      ↓                  ↓                   ↓                     ↓                     ↓                    ↓
 [Burp Proxy]     [forgot-password    [# and & delimiter     [Burp Intruder /     [field=reset_token   [New password set,
                    endpoint found]     injection]             variable list]      injected]            carlos deleted]
```

| Stage | Technique | Tool | MITRE ATT&CK TTP |
|-------|-----------|------|-------------------|
| Initial Access | Exploited server-side parameter pollution in `forgot-password` | Burp Repeater | [T1190](https://attack.mitre.org/techniques/T1190/) |
| Discovery | Enumerated internal `field` parameter values | Burp Intruder | [T1595](https://attack.mitre.org/techniques/T1595/) |
| Credential Access | Exfiltrated administrator `reset_token` via injected field | Burp Repeater | [T1552](https://attack.mitre.org/techniques/T1552/) |
| Impact | Reset administrator password and deleted `carlos` | Browser | [T1531](https://attack.mitre.org/techniques/T1531/) |

---

## Tools & Environment

### Environment
| Component | Specification |
|-----------|---------------|
| **OS / Platform** | PortSwigger Web Security Academy — hosted lab instance |
| **Target** | `0abc001a03aed5cd82a05136008f00b6.web-security-academy.net` |
| **Network** | PortSwigger Academy sandboxed lab network |

### Tools Used
| Tool | Version | Purpose |
|------|---------|---------|
| Burp Suite Community Edition | 2026.3.3 | Traffic interception, Repeater-based payload testing |
| Burp Intruder | Bundled with Burp Suite | Brute-forcing the internal `field` parameter name |
| Chromium (Burp's browser) | 146 | Triggering the reset flow and consuming the recovered token |

---

## Evidence

All supporting evidence is organized in the `/evidence/` directory.

| Reference | File | Description |
|-----------|------|--------------|
| VULN-001 PoC | `evidence/exploit-token.png` | Burp Repeater request showing the `%26field=reset_token%23` injection and the leaked reset token in the JSON response |
| Lab Confirmation | `evidence/lab-solved.png` | PortSwigger Academy lab status confirming successful solve after deleting `carlos` |

> **Note:** Screenshots are reproduced as captured from Burp Suite Community Edition during the assessment.

---

## Remediation

### Prioritized Action Plan

| Priority | Finding | Effort | Recommended Action | Deadline |
|----------|---------|--------|-------------------|----------|
| [IMMEDIATE] | VULN-001 — Server-Side Parameter Pollution | Low | Encode all user input before internal API concatenation; restrict which fields an internal API can return based on client input | Within 24–48 hrs |

### Strategic Recommendations
1. **Input Encoding at Trust Boundaries** — Any value crossing from a client-facing request into an internal API call must be encoded or validated against a strict allowlist, regardless of whether the internal API is considered "trusted."
2. **Principle of Least Response** — Internal APIs should return only the minimum data required for the calling context, rather than exposing a generic `field`-selectable response structure to a caller that is itself relaying untrusted client input.
3. **Structured Internal Requests** — Replace ad hoc query-string concatenation between internal services with structured, schema-validated payloads (e.g., JSON with fixed keys) to eliminate delimiter-based injection entirely.

---

## Lessons Learned

### Technical Takeaways
- Server-side parameter pollution can occur even when there is no visible reflected output, purely through differential error messages (`Invalid username`, `Parameter is not supported`, `Field not specified`, `Invalid field`).
- Burp Intruder's built-in server-side variable name list is an efficient way to enumerate hidden internal parameter names once an injection point is confirmed.
- Truncating a server-side query string with `#` is a distinct primitive from extending it with `&` — both were needed together to fully control the internal request.

### What I Would Do Differently
- Script the field-name brute-force and token-extraction flow with Turbo Intruder to make the technique reusable against future SSPP-style targets rather than working the request manually in Repeater.

### Skills Demonstrated
> `HTTP Parameter Pollution` `API Security Testing` `Burp Suite (Repeater/Intruder)` `Authentication Bypass Analysis` `Server-Side Request Manipulation`

---

## References

- [PortSwigger — Server-side parameter pollution](https://portswigger.net/web-security/api-testing/server-side-parameter-pollution)
- [OWASP Top 10 2021 — A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [CWE-235: Improper Handling of Extra Parameters](https://cwe.mitre.org/data/definitions/235.html)
- [MITRE ATT&CK — T1190: Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [NVD CVSS v3.1 Calculator](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator)

---

## Author

**Michael Asante Anim** | `0x1aerixis`
BSc Cyber Security — University of Mines and Technology (UMaT), Tarkwa, Ghana

[![GitHub](https://img.shields.io/badge/GitHub-anim--michael--asante-black?logo=github)](https://github.com/anim-michael-asante)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/michael-asante-anim)
[![TryHackMe](https://img.shields.io/badge/TryHackMe-0x1aerixis-red?logo=tryhackme)](https://tryhackme.com/p/0x1aerixis)
[![X](https://img.shields.io/badge/X-0x1aerixis-black?logo=x)](https://x.com/0x1aerixis)
[![Discord](https://img.shields.io/badge/Discord-0x1aerixis-5865F2?logo=discord)](https://discord.com/users/0x1aerixis)

> *"Built in the lab. Documented for the field."*

---
> **Disclaimer:** All work documented in this repository was conducted in authorized, isolated lab environments or sanctioned CTF platforms. No unauthorized systems were accessed. This project is intended for educational and portfolio purposes only.

# 14-sqli-blind-time-based-pg-sleep

![Platform](https://img.shields.io/badge/Platform-PortSwigger_Web_Security_Academy-orange)
![Category](https://img.shields.io/badge/Category-SQL_Injection-red)
![Technique](https://img.shields.io/badge/Technique-Blind_Time--Based-critical)
![OWASP](https://img.shields.io/badge/OWASP-A03:2021_Injection-red)
![CVSS](https://img.shields.io/badge/CVSS_v3.1-9.8_CRITICAL-critical)
![Status](https://img.shields.io/badge/Status-Solved-brightgreen)

---

## Table of Contents

1. [Overview](#overview)
2. [Scope & Objectives](#scope--objectives)
3. [Methodology](#methodology)
4. [Findings](#findings)
5. [Risk Summary](#risk-summary)
6. [Attack Chain](#attack-chain)
7. [Tools & Environment](#tools--environment)
8. [Evidence](#evidence)
9. [Remediation Strategy](#remediation-strategy)
10. [Lessons Learned](#lessons-learned)
11. [References](#references)
12. [Author](#author)

---

## Overview

This writeup documents the exploitation of a blind SQL injection vulnerability in a PortSwigger
Web Security Academy lab environment. The target application processes a `TrackingId` cookie in
a backend SQL query without returning query results or distinguishing error responses. By
injecting a conditional `pg_sleep()` payload via the cookie, it is possible to infer the presence
of specific database records through observable response delays. The lab objective — inducing a
10-second delay using a crafted cookie payload — was achieved, confirming the existence of the
`administrator` account in the `users` table.

This lab maps to **OWASP API Security Top 10 (2023) API8** (Security Misconfiguration) and
**OWASP Top 10 (2021) A03** (Injection), and demonstrates inference-based data exfiltration
without any direct output channel.

---

## Scope & Objectives

| Field | Detail |
|---|---|
| Platform | PortSwigger Web Security Academy |
| Lab Title | Blind SQL Injection with Time Delays and Information Retrieval |
| Lab Number | 14 (PortSwigger SQLi Series) |
| Target Component | `TrackingId` HTTP cookie |
| Database Backend | PostgreSQL |
| In Scope | Cookie parameter injection, time-based inference |
| Out of Scope | Authentication bypass, data exfiltration beyond account confirmation |
| Objective | Trigger a 10-second conditional delay using SQL injection to confirm `administrator` exists in `users` table |

---

## Methodology

The assessment followed the **PTES (Penetration Testing Execution Standard)** and aligned with
**NIST SP 800-115** technical testing guidelines.

### Phase 1 — Reconnaissance
Identified the `TrackingId` cookie as the injection surface by observing that it is submitted
with every page request and processed server-side with no reflected output.

### Phase 2 — Injection Point Confirmation
Tested the cookie for SQL injection susceptibility by introducing a single quote (`'`) and
observing no visible change in response body or status code — confirming blind injection
behaviour.

### Phase 3 — Time-Based Inference
Constructed a conditional payload using PostgreSQL's `pg_sleep()` function wrapped in a
`CASE WHEN` expression:

```sql
'||(SELECT CASE WHEN (username='administrator') THEN pg_sleep(10) ELSE pg_sleep(0) END FROM users)--
```

The `||` operator concatenates the injected subquery into the original SQL context. The `CASE
WHEN` clause causes a 10-second sleep only if a row matching `username='administrator'` is found
in the `users` table. A `pg_sleep(0)` branch was included to confirm that delays were conditional
rather than server-side latency artefacts.

### Phase 4 — Objective Confirmation
A 10-second response delay was observed, confirming the row exists. Lab status transitioned to
solved.

---

## Findings

### F-001 — Blind Time-Based SQL Injection via TrackingId Cookie [CRITICAL]

| Field | Detail |
|---|---|
| Finding ID | F-001 |
| Severity | [CRITICAL] |
| CVSS v3.1 Score | 9.8 |
| CVSS v3.1 Vector | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-89 — Improper Neutralisation of Special Elements used in an SQL Command |
| OWASP Top 10 (2021) | A03:2021 — Injection |
| MITRE ATT&CK TTP | T1190 — Exploit Public-Facing Application |
| Affected Component | `TrackingId` HTTP Cookie |

**Description**

The application executes a SQL query incorporating the raw value of the `TrackingId` cookie
without parameterisation or input sanitisation. Although query results are not returned to the
client and error states are suppressed, the query executes synchronously. This allows an attacker
to embed time-delay functions (e.g., `pg_sleep()`) inside conditional expressions to infer
database content one condition at a time.

**Technical Impact**

- Enumeration of database table contents (usernames, existence of privileged accounts)
- Potential for full credential exfiltration via iterative character-by-character inference
- Arbitrary SQL execution within the database engine's privilege context

**Business Impact**

- Compromise of privileged account credentials with no authentication required
- Breach of all data accessible to the database service account
- Regulatory exposure under GDPR and PCI-DSS for affected user records

**Proof of Concept**

Injected cookie value:

```
TrackingId=tyWZpiIJv4g7Blfi'||(SELECT CASE WHEN (username='administrator') THEN pg_sleep(10) ELSE pg_sleep(0) END FROM users)--
```

Reconstructed server-side SQL (inferred):

```sql
SELECT tracking_id FROM tracking_table
WHERE tracking_id = 'tyWZpiIJv4g7Blfi'
||(SELECT CASE WHEN (username='administrator') THEN pg_sleep(10) ELSE pg_sleep(0) END FROM users)--'
```

**Reproduction Steps**

1. Intercept any request to the application using Burp Suite.
2. Locate the `TrackingId` cookie in the request.
3. Append the following to the existing cookie value:
   ```
   '||(SELECT CASE WHEN (username='administrator') THEN pg_sleep(10) ELSE pg_sleep(0) END FROM users)--
   ```
4. Forward the request and observe response time.
5. A response time >= 10 seconds confirms `administrator` exists in `users`.

---

## Risk Summary

| ID | Title | Severity | CVSS | Priority |
|---|---|---|---|---|
| F-001 | Blind Time-Based SQLi via TrackingId | [CRITICAL] | 9.8 | [IMMEDIATE] |

---

## Attack Chain

```
[Attacker]
    |
    v
[HTTP Request with malicious TrackingId cookie]
    |
    v
[Application passes cookie value directly into SQL query — no parameterisation]
    |
    v
[PostgreSQL executes CASE WHEN conditional with pg_sleep()]
    |
    v
[Response delayed 10 seconds — confirms administrator account exists in users table]
    |
    v
[Objective achieved — lab solved]
```

MITRE ATT&CK mapping:

| Tactic | Technique | ID |
|---|---|---|
| Initial Access | Exploit Public-Facing Application | T1190 |
| Discovery | Account Discovery | T1087 |
| Collection | Data from Information Repositories | T1213 |

---

## Tools & Environment

| Tool | Version | Purpose |
|---|---|---|
| Burp Suite Community Edition | Latest | HTTP interception and request modification |
| Browser (Chromium) | Latest | Lab environment access |
| PostgreSQL (target) | Not disclosed | Target database engine |
| PortSwigger Web Security Academy | N/A | Lab hosting platform |

---

## Evidence

**Lab Solved — Time Delay Confirmed**

![Lab solved confirmation screenshot](evidence/lab-solved.png)

*Figure 1: Browser view confirming lab solved status after 10-second response delay triggered by
conditional pg_sleep() payload injected via TrackingId cookie.*

---

## Remediation Strategy

### R-001 — Parameterise All SQL Queries [IMMEDIATE]

Replace string concatenation with parameterised queries or prepared statements across all
database access code paths. The `TrackingId` cookie value must never be interpolated directly
into SQL.

**Vulnerable pattern (pseudocode):**
```sql
"SELECT ... WHERE tracking_id = '" + cookie_value + "'"
```

**Remediated pattern (pseudocode):**
```sql
"SELECT ... WHERE tracking_id = ?"  -- with cookie_value as a bound parameter
```

### R-002 — Input Validation on Cookie Values [SHORT-TERM]

Enforce allowlist-based validation on the `TrackingId` cookie. Tracking IDs are typically
alphanumeric strings of fixed length — reject any value containing SQL metacharacters (`'`, `|`,
`-`, `(`, `)`, `;`).

### R-003 — Apply Least Privilege to Database Service Account [SHORT-TERM]

Restrict the database service account used by the application to the minimum required
permissions. The account should not have `SELECT` access to the `users` table from the analytics
query context.

### R-004 — Suppress Timing Side Channels [PLANNED]

Implement response time normalisation or query execution timeouts at the application layer to
reduce the effectiveness of time-based inference attacks, even if injection were to occur.

### Retest Criteria

- Inject `' OR pg_sleep(10)--` into the `TrackingId` cookie.
- Confirm response time is consistently under 1 second regardless of payload.
- Verify no SQL error information is present in any response body or header.

---

## Lessons Learned

- Blind injection vulnerabilities are exploitable without any output channel. The absence of
  error messages or reflected data does not indicate safety.
- Synchronous query execution is a prerequisite for time-based inference. Asynchronous database
  architectures would mitigate this specific vector.
- Conditional payloads (`CASE WHEN`) allow precise, testable inference — distinguishing actual
  delay from network jitter requires multiple requests to reduce false positives.
- PostgreSQL's `pg_sleep()` is semantically equivalent to `WAITFOR DELAY` in MSSQL and
  `SLEEP()` in MySQL — the technique is database-agnostic at the conceptual level but the
  specific function must match the backend.
- Tracking cookies are a frequently overlooked injection surface. Any parameter processed
  server-side — including non-visible identifiers — must be treated as untrusted input.

---

## References

| Reference | Detail |
|---|---|
| OWASP Top 10 (2021) — A03 | https://owasp.org/Top10/A03_2021-Injection/ |
| CWE-89 | https://cwe.mitre.org/data/definitions/89.html |
| MITRE ATT&CK T1190 | https://attack.mitre.org/techniques/T1190/ |
| NIST SP 800-115 | https://csrc.nist.gov/publications/detail/sp/800/115/final |
| PortSwigger SQLi Cheat Sheet | https://portswigger.net/web-security/sql-injection/cheat-sheet |
| CVSS v3.1 Calculator | https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator |
| PostgreSQL pg_sleep() | https://www.postgresql.org/docs/current/functions-datetime.html |

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
> **Disclaimer:** All work documented in this repository was conducted in authorized, isolated
> lab environments or sanctioned CTF platforms. No unauthorized systems were accessed.
> This project is intended for educational and portfolio purposes only.

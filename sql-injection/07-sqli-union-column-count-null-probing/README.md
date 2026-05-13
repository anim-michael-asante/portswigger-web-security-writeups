# SQL Injection UNION Attack — Column Enumeration via NULL Probing

![Platform](https://img.shields.io/badge/Platform-PortSwigger%20Web%20Security%20Academy-orange)
![Difficulty](https://img.shields.io/badge/Difficulty-Apprentice-brightgreen)
![Type](https://img.shields.io/badge/Type-SQL%20Injection%20%7C%20UNION%20Attack-blue)
![OWASP](https://img.shields.io/badge/OWASP-A03%3A2021%20Injection-red)
![CVSS](https://img.shields.io/badge/CVSS%20v3.1-9.8%20CRITICAL-critical)
![Status](https://img.shields.io/badge/Lab%20Status-SOLVED-success)
![Author](https://img.shields.io/badge/Author-0x1aerixis-black)

---

## Table of Contents

1. [Overview](#overview)
2. [Scope & Objectives](#scope--objectives)
3. [Methodology](#methodology)
4. [Findings](#findings)
5. [Risk Summary Table](#risk-summary-table)
6. [Attack Chain](#attack-chain)
7. [Tools & Environment](#tools--environment)
8. [Evidence](#evidence)
9. [Remediation Strategy](#remediation-strategy)
10. [Lessons Learned](#lessons-learned)
11. [References](#references)
12. [Author](#author)

---

## Overview

This write-up documents the exploitation of a SQL injection vulnerability present in the product category filter parameter of a PortSwigger Web Security Academy lab. The objective was to determine the number of columns returned by the back-end SQL query through a UNION-based injection approach using incremental NULL value probing. This technique constitutes the mandatory first phase of any UNION attack: column count enumeration. The lab was completed by crafting progressively extended UNION SELECT payloads until the application responded without errors, confirming a three-column result set. This write-up aligns with OWASP A03:2021 (Injection) and maps directly to the MITRE ATT&CK technique T1190 (Exploit Public-Facing Application).

---

## Scope & Objectives

| Field                | Details                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Platform             | PortSwigger Web Security Academy                                                               |
| Lab Title            | SQL Injection UNION Attack, Determining the Number of Columns Returned by the Query            |
| Target URL           | `https://0ae600bf04351592826db01200640069.web-security-academy.net`                            |
| Vulnerable Endpoint  | `/filter?category=`                                                                            |
| Vulnerable Parameter | `category`                                                                                     |
| Engagement Type      | Authorized lab environment — isolated, sandboxed                                               |
| Out of Scope         | Any system outside the designated PortSwigger lab instance                                     |
| Authorization        | Implicit — PortSwigger Web Security Academy labs are publicly accessible training environments |

**Primary Objective:** Determine the number of columns returned by the back-end SQL query by injecting a UNION SELECT payload containing NULL values until a valid response is returned.

**Secondary Objective:** Establish foundational column enumeration technique required for subsequent UNION-based data extraction attacks.

---

## Methodology

The engagement followed the **PTES (Penetration Testing Execution Standard)** methodology for web application vulnerability assessment, with specific reference to **OWASP Testing Guide v4.2** section OTG-INPVAL-005 (Testing for SQL Injection).

### Phase 1 — Reconnaissance

Identify the vulnerable parameter by observing that the application reflects database query results directly in the HTTP response body. This confirms the injection point is suitable for UNION-based data retrieval.

### Phase 2 — Injection Point Confirmation

Test the `category` parameter for SQL injection by appending a single quote (`'`) to the parameter value. An application-level error or abnormal response confirms unsanitized input is being interpolated into a raw SQL query.

```http
GET /filter?category=Pets' HTTP/1.1
Host: 0ae600bf04351592826db01200640069.web-security-academy.net
```

### Phase 3 — Column Count Enumeration (UNION NULL Probing)

UNION-based injection requires that the injected SELECT statement return the exact same number of columns as the original query. NULL values are used because NULL is compatible with any data type, eliminating type-mismatch errors during column count probing.

Payloads were injected incrementally:

**Attempt 1 — 1 column (error):**

```
/filter?category=Pets'+UNION+SELECT+NULL--
```

**Attempt 2 — 2 columns (error):**

```
/filter?category=Pets'+UNION+SELECT+NULL,NULL--
```

**Attempt 3 — 3 columns (success):**

```
/filter?category=Pets'+UNION+SELECT+NULL,NULL,NULL--
```

On the third attempt, the application returned a valid response with an additional row containing NULL values, confirming the back-end query returns exactly **3 columns**.

### Phase 4 — Result Verification

The absence of a SQL error and the presence of an injected row in the response body served as objective confirmation of successful column enumeration.

---

## Findings

### Finding F-001 — Unsanitized SQL Injection in Product Category Filter

| Field                   | Details                                                                     |
| ----------------------- | --------------------------------------------------------------------------- |
| Finding ID              | F-001                                                                       |
| Severity                | [CRITICAL]                                                                  |
| CVSS v3.1 Score         | 9.8                                                                         |
| CVSS v3.1 Vector        | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`                              |
| CWE                     | CWE-89 — Improper Neutralization of Special Elements used in an SQL Command |
| OWASP Category          | A03:2021 — Injection                                                        |
| MITRE ATT&CK TTP        | T1190 — Exploit Public-Facing Application                                   |
| Affected Component      | `/filter` endpoint — `category` GET parameter                               |
| Authentication Required | None                                                                        |

**Description:**

The `category` parameter in the `/filter` endpoint is directly interpolated into a SQL query without sanitization or parameterized query handling. An unauthenticated attacker can inject arbitrary SQL syntax, including UNION SELECT statements, to manipulate query logic, enumerate the column structure of the result set, and subsequently extract data from other database tables.

**Technical Impact:**

- Full column structure of the query result set enumerable without authentication
- UNION SELECT payloads can be constructed to retrieve sensitive data from arbitrary tables (credentials, session tokens, PII) once column count and compatible types are determined
- Depending on database user privileges, the attack surface may extend to file read/write operations and OS command execution

**Business Impact:**

- Unauthorized access to application data including user accounts and sensitive records
- Potential full database compromise and lateral movement to connected systems
- Regulatory exposure under GDPR, NDPC Act 2012 (Ghana), and PCI DSS depending on data classification

**Proof of Concept:**

The following request was submitted using Burp Suite Proxy. The response included an additional content row containing NULL values with HTTP 200 status, confirming successful UNION injection:

```
GET /filter?category=Pets'+UNION+SELECT+NULL,NULL,NULL-- HTTP/1.1
Host: 0ae600bf04351592826db01200640069.web-security-academy.net
```

**Reproduction Steps:**

1. Navigate to the target lab URL.
2. Intercept the `/filter?category=Pets` request using Burp Suite Proxy.
3. Modify the `category` parameter to: `Pets'+UNION+SELECT+NULL--`
4. Observe a SQL error or abnormal response (1 column — mismatch).
5. Extend the payload to: `Pets'+UNION+SELECT+NULL,NULL--`
6. Observe continued error (2 columns — mismatch).
7. Extend the payload to: `Pets'+UNION+SELECT+NULL,NULL,NULL--`
8. Observe HTTP 200 response with injected NULL row in the body — column count confirmed as **3**.

**Remediation:**

Parameterize all SQL queries using prepared statements. Do not construct queries through string concatenation. See Remediation Strategy section for implementation detail.

**Retest Criteria:**

After remediation, inject `Pets'+UNION+SELECT+NULL,NULL,NULL--` via the `category` parameter. The application must return an error or ignore the injected payload without reflecting additional rows. A SQL error surfaced to the client also indicates incomplete remediation (error handling must be addressed separately).

---

## Risk Summary Table

| ID    | Title                                    | Severity   | CVSS v3.1 | CWE    | Priority    |
| ----- | ---------------------------------------- | ---------- | --------- | ------ | ----------- |
| F-001 | SQL Injection in Product Category Filter | [CRITICAL] | 9.8       | CWE-89 | [IMMEDIATE] |

---

## Attack Chain

```
[1] RECONNAISSANCE
    Observe application reflects query results directly in HTTP response
    Confirms UNION-based injection is viable
         |
         v
[2] INJECTION POINT CONFIRMATION
    Append single quote (') to category parameter
    Application returns SQL error or abnormal response
    Confirms unsanitized input interpolated into raw SQL
         |
         v
[3] COLUMN COUNT ENUMERATION — NULL PROBING
    Inject: '+UNION+SELECT+NULL--          (1 col) -> ERROR
    Inject: '+UNION+SELECT+NULL,NULL--     (2 col) -> ERROR
    Inject: '+UNION+SELECT+NULL,NULL,NULL--(3 col) -> SUCCESS
         |
         v
[4] CONFIRMATION
    HTTP 200 response returned
    Additional NULL row present in response body
    Column count confirmed: 3
         |
         v
[5] OBJECTIVE ACHIEVED
    Lab solved — column enumeration complete
    Foundation established for full UNION data extraction in subsequent labs
```

**MITRE ATT&CK Mapping:**

| Phase          | Technique                               | ID                            |
| -------------- | --------------------------------------- | ----------------------------- |
| Initial Access | Exploit Public-Facing Application       | T1190                         |
| Discovery      | Query column structure via NULL probing | T1190 (sub-technique context) |

---

## Tools & Environment

| Tool                             | Version | Purpose                                           |
| -------------------------------- | ------- | ------------------------------------------------- |
| Burp Suite Community Edition     | Latest  | HTTP proxy, request interception and modification |
| Chromium / Firefox               | N/A     | Lab browser interface                             |
| PortSwigger Web Security Academy | N/A     | Authorized target lab environment                 |

**Attack Machine:** Attacker-controlled browser with Burp Suite configured as an HTTP proxy on `127.0.0.1:8080`.

**Target:** PortSwigger Web Security Academy sandboxed lab instance — isolated, ephemeral, and authorized.

---

## Evidence

sql-injection/07-sqli-union-column-count-null-probing/evidence/lab-solved.png

| ID    | Artifact                  | Description                                                                                                      |
| ----- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| E-001 | `evidence/lab-solved.png` | Full browser screenshot confirming lab solved status and application response to three-column UNION NULL payload |

> All evidence was captured within the PortSwigger Web Security Academy authorized lab environment. No external or production systems were accessed.

```
evidence/
└── lab-solved.png     # Lab completion confirmation — HTTP 200, NULL row reflected, solved banner visible
```

## sql-injection/07-sqli-union-column-count-null-probing/evidence/lab-solved.png

## Remediation Strategy

### R-001 — Parameterized Queries (Prepared Statements)

**Priority:** [IMMEDIATE] — Implement within 24–48 hours.

Replace all dynamic SQL string concatenation with parameterized queries or an ORM that enforces parameterization by default. User-supplied input must never be interpolated directly into SQL statement strings.

**Vulnerable Pattern (do not use):**

```python
query = "SELECT * FROM products WHERE category = '" + category + "'"
cursor.execute(query)
```

**Remediated Pattern:**

```python
query = "SELECT * FROM products WHERE category = ?"
cursor.execute(query, (category,))
```

**Java (JDBC) Example:**

```java
PreparedStatement stmt = conn.prepareStatement(
    "SELECT * FROM products WHERE category = ?"
);
stmt.setString(1, category);
ResultSet rs = stmt.executeQuery();
```

### R-002 — Input Validation and Allowlisting

**Priority:** [SHORT-TERM]

Apply server-side input validation to constrain the `category` parameter to a predefined allowlist of valid category identifiers. Reject requests with values not present in the allowlist before they reach the query layer.

### R-003 — Suppress Verbose SQL Errors

**Priority:** [SHORT-TERM]

Configure the application to return generic error messages to clients. Verbose SQL errors must not be surfaced in HTTP responses, as they disclose table names, query structure, and database engine details that accelerate exploitation.

### R-004 — Least Privilege Database Accounts

**Priority:** [PLANNED]

The database account used by the application should have only SELECT privileges on the required tables. Write, DDL, and file system privileges must be revoked to limit the blast radius of any successful injection.

---

## Lessons Learned

**Column count enumeration is the mandatory prerequisite for UNION injection.** A UNION SELECT statement will be rejected by the database engine if the injected query does not return the exact same number of columns as the original query. NULL probing is the most reliable enumeration technique because NULL is type-compatible with any column datatype, isolating column count discovery from type-mismatch errors.

**Comment terminators are database-engine-specific.** The `--` comment terminator used in this lab is standard for PostgreSQL and Microsoft SQL Server. MySQL requires `-- ` (with a trailing space) or `#`. Payload construction must account for the underlying database engine.

**Response-based injection relies on reflected output.** This attack class is only viable when query results are included in the HTTP response. Blind injection scenarios require alternative techniques (boolean-based or time-based inference) when no output is reflected.

**Error handling is itself an information disclosure control.** The lab's error responses on column count mismatch directly confirmed injection success and narrowed the attack surface. Production applications that suppress all SQL errors remove a significant reconnaissance signal from the attacker's workflow.

---

## References

| Source                  | Reference                                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| PortSwigger Web Academy | [SQL Injection UNION Attacks](https://portswigger.net/web-security/sql-injection/union-attacks)                            |
| OWASP                   | [A03:2021 — Injection](https://owasp.org/Top10/A03_2021-Injection/)                                                        |
| OWASP Testing Guide     | [OTG-INPVAL-005 — Testing for SQL Injection](https://owasp.org/www-project-web-security-testing-guide/)                    |
| MITRE ATT&CK            | [T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)                                    |
| NIST NVD                | [CWE-89 — SQL Injection](https://cwe.mitre.org/data/definitions/89.html)                                                   |
| NIST                    | [CVSS v3.1 Calculator](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator)                                               |
| NIST                    | [SP 800-115 — Technical Guide to Information Security Testing](https://csrc.nist.gov/publications/detail/sp/800-115/final) |

---

## Author

**Michael Asante Anim** | `0x1aerixis`
BSc Cyber Security — University of Mines and Technology (UMaT), Tarkwa, Ghana

[![GitHub](https://img.shields.io/badge/GitHub-anim--michael--asante-black?logo=github)](https://github.com/anim-michael-asante)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/michael-asante-anim)
[![TryHackMe](https://img.shields.io/badge/TryHackMe-0x1aerixis-red?logo=tryhackme)](https://tryhackme.com/p/0x1aerixis)
[![X](https://img.shields.io/badge/X-0x1aerixis-black?logo=x)](https://x.com/0x1aerixis)
[![Discord](https://img.shields.io/badge/Discord-0x1aerixis-5865F2?logo=discord)](https://discord.com/users/0x1aerixis)

> _"Built in the lab. Documented for the field."_

---

> **Disclaimer:** All work documented in this repository was conducted in authorized, isolated
> lab environments or sanctioned CTF platforms. No unauthorized systems were accessed.
> This project is intended for educational and portfolio purposes only.

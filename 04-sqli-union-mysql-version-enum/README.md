# SQL Injection — Querying Database Type and Version (MySQL/Microsoft)

![Platform](https://img.shields.io/badge/Platform-PortSwigger_Web_Security_Academy-orange)
![Difficulty](https://img.shields.io/badge/Difficulty-Apprentice-green)
![Status](https://img.shields.io/badge/Status-Solved-brightgreen)
![Category](https://img.shields.io/badge/Category-SQL_Injection-red)
![OWASP](https://img.shields.io/badge/OWASP-A03:2021_Injection-critical)
![MITRE](https://img.shields.io/badge/MITRE-T1190-blue)
![Lab](https://img.shields.io/badge/Lab-4-lightgrey)

---

## Table of Contents

1. [Overview](#overview)
2. [Scope and Objectives](#scope-and-objectives)
3. [Methodology](#methodology)
4. [Findings](#findings)
5. [Attack Chain](#attack-chain)
6. [Tools and Environment](#tools-and-environment)
7. [Evidence](#evidence)
8. [Remediation Strategy](#remediation-strategy)
9. [Lessons Learned](#lessons-learned)
10. [References](#references)
11. [Author](#author)

---

## Overview

This writeup documents the exploitation of a SQL injection vulnerability in a PortSwigger Web Security Academy Apprentice-level lab. The target application exposes unsanitized user input through a product category filter parameter. A UNION-based injection payload was constructed to enumerate the backend database engine and extract the version string. The lab simulates a MySQL/Microsoft SQL Server environment. The objective — displaying the database version string — was achieved in a single crafted request.

---

## Scope and Objectives

| Field                | Detail                                                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Platform             | PortSwigger Web Security Academy                                                                                          |
| Lab Title            | SQL Injection — Querying Database Type and Version on MySQL and Microsoft                                                 |
| Lab URL              | `https://portswigger.net/web-security/sql-injection/examining-the-database/lab-querying-database-version-mysql-microsoft` |
| Target Endpoint      | `/filter?category=`                                                                                                       |
| Vulnerable Parameter | `category` (GET)                                                                                                          |
| In Scope             | Web application category filter, database version enumeration                                                             |
| Out of Scope         | Authentication bypass, data exfiltration beyond version string, all other endpoints                                       |
| Objective            | Extract and display the backend database version string via SQL injection                                                 |

---

## Methodology

The engagement followed the OWASP Testing Guide (OTG-INPVAL-005) for SQL Injection testing and the PTES exploitation phase.

### Phase 1 — Reconnaissance

Identified the injectable parameter by observing that the `category` query string was reflected in page content and controlled application behaviour. No input sanitization was apparent from response differentials.

### Phase 2 — Injection Point Confirmation

Appended a single quote (`'`) to the category value to confirm SQL syntax error behaviour, confirming unparameterized query construction on the backend.

### Phase 3 — Column Count Enumeration

Used `ORDER BY` clause incrementation to determine the number of columns returned by the base query. The query returned no error at `ORDER BY 2` and errored at `ORDER BY 3`, confirming a two-column result set.

### Phase 4 — UNION SELECT Construction

Constructed a `UNION SELECT` payload with two columns. MySQL/Microsoft SQL Server exposes the database version through the `@@version` global variable. `NULL` was used as a placeholder for the second column.

### Phase 5 — Version Extraction

Injected the finalized payload via the `category` parameter. The database version string was returned inline within the product listing page.

---

## Findings

### Finding F-01 — SQL Injection via Unsanitized Category Filter Parameter

| Field              | Detail                                                                      |
| ------------------ | --------------------------------------------------------------------------- |
| Finding ID         | F-01                                                                        |
| Severity           | [HIGH]                                                                      |
| CVSS v3.1 Score    | 8.6                                                                         |
| CVSS v3.1 Vector   | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N`                              |
| CWE                | CWE-89 — Improper Neutralization of Special Elements Used in an SQL Command |
| OWASP Category     | A03:2021 — Injection                                                        |
| MITRE ATT&CK TTP   | T1190 — Exploit Public-Facing Application                                   |
| Affected Component | `/filter?category=` (GET parameter)                                         |

**Description**

The application constructs a SQL query by directly concatenating user-supplied input from the `category` GET parameter without parameterization or escaping. An unauthenticated attacker can inject arbitrary SQL syntax, terminating the original query and appending a `UNION SELECT` statement to read from the database engine itself.

**Technical Impact**

- Database version and engine fingerprinting (confirmed exploited)
- Potential enumeration of table names, column names, and stored data depending on database user privileges
- Groundwork for secondary attacks including authentication bypass and data extraction

**Business Impact**

- Disclosure of backend technology stack enables targeted exploitation
- If elevated database privileges exist, full data exfiltration is achievable in subsequent steps
- Regulatory exposure under applicable data protection frameworks (e.g., GDPR, Ghana Data Protection Act 2012)

**Proof of Concept**

Injected URL:

```
https://0a3a00390406265380799e4600550023.web-security-academy.net/filter?category=Accessories'+UNION+SELECT+@@version,+NULL--+
```

Decoded payload:

```sql
' UNION SELECT @@version, NULL--
```

**Reproduction Steps**

1. Navigate to the application's product filter endpoint.
2. Append a single quote to the category value and observe SQL error behaviour.
3. Enumerate column count using `ORDER BY 1--`, `ORDER BY 2--`, etc.
4. Confirm two columns are returned.
5. Submit the payload: `' UNION SELECT @@version, NULL-- `
6. Observe the database version string rendered in the product listing.

**Result Returned**

```
8.0.42-0ubuntu0.20.04.1
```

This confirms the backend is running **MySQL 8.0.42** on an Ubuntu 20.04 host.

---

## Attack Chain

```
[1] Parameter Discovery
    Observed category filter reflects user input in SQL context
         |
         v
[2] Injection Confirmation
    Appended ' — SQL syntax disruption confirmed
         |
         v
[3] Column Enumeration
    ORDER BY 2 succeeds, ORDER BY 3 fails — two columns confirmed
         |
         v
[4] UNION SELECT Construction
    ' UNION SELECT @@version, NULL--
         |
         v
[5] Version Extraction
    MySQL 8.0.42-0ubuntu0.20.04.1 returned inline in page response
         |
         v
[6] Objective Achieved
    Database type and version confirmed — lab solved
```

---

## Tools and Environment

| Tool / Resource                    | Purpose                             |
| ---------------------------------- | ----------------------------------- |
| Browser (Chromium)                 | Manual payload delivery via URL bar |
| PortSwigger Web Security Academy   | Isolated lab environment            |
| MySQL `@@version` system variable  | Database version extraction         |
| OWASP Testing Guide OTG-INPVAL-005 | Methodology reference               |

No automated scanners or external tools were required. The attack was completed manually using only the browser address bar.

---

## Evidence

### Screenshot — Lab Solved and Version String Extracted

![Lab solved screenshot showing UNION SELECT payload reflected in the page title and the MySQL version string `8.0.42-0ubuntu0.20.04.1` rendered at the bottom of the product listing.](./evidence/lab-solved.png)

> **Figure 1:** The injected `UNION SELECT` payload is reflected in the page heading. The database version string `8.0.42-0ubuntu0.20.04.1` appears at the bottom of the product list, confirming successful extraction of backend database version information through SQL injection.

---

## Remediation Strategy

### R-01 — Parameterized Queries [IMMEDIATE]

Replace all dynamic SQL string concatenation with prepared statements and parameterized queries.

**Before (vulnerable):**

```sql
SELECT * FROM products WHERE category = '" + category + "'
```

**After (secure):**

```java
PreparedStatement stmt = conn.prepareStatement(
    "SELECT * FROM products WHERE category = ?"
);
stmt.setString(1, category);
```

All database interaction layers must adopt this pattern without exception.

**Retest Criteria:** Inject `' UNION SELECT NULL-- ` into the category parameter. The application must return no altered results, no error messages, and no injected data.

---

### R-02 — Input Validation and Allowlist Enforcement [SHORT-TERM]

Apply server-side allowlist validation on the `category` parameter. Accept only expected, pre-defined category values. Reject and log any input that does not match the allowlist.

**Retest Criteria:** Submit an unexpected value such as `Electronics'--`. The application must reject the request with a 400 response or redirect, and log the event.

---

### R-03 — Suppress Verbose Error Messages [SHORT-TERM]

Configure the application to return generic error pages in production. SQL error messages must never be exposed to end users.

**Retest Criteria:** Trigger an invalid query. The response must contain no database error detail, table names, or stack trace.

---

### R-04 — Apply Principle of Least Privilege to Database Accounts [PLANNED]

The application database user must be restricted to only the permissions required for normal operation (SELECT on relevant tables). No access to system tables, schema metadata, or administrative functions should be granted.

**Retest Criteria:** Verify database user grants using `SHOW GRANTS FOR 'app_user'@'%'`. Confirm no elevated privileges are present.

---

## Lessons Learned

**Direct UNION injection without Burp Suite is viable for simple column counts.** Manual enumeration via the browser URL bar is sufficient for Apprentice-level labs and is a practical skill for environments where tooling is restricted.

**`@@version` is MySQL and Microsoft SQL Server specific.** On PostgreSQL the equivalent is `version()`. On Oracle it is `v$version`. Correct dialect identification informs subsequent payload construction.

**Column count confirmation is prerequisite to UNION injection.** Mismatched column counts cause the query to fail silently or error. `ORDER BY` enumeration is a reliable, low-noise method for determining column count before constructing the UNION payload.

**Database version disclosure is not a low-severity finding.** Version strings expose patch level and OS details, enabling targeted exploitation using known CVEs against that engine and distribution.

---

## References

| Reference                          | Link                                                                                                                    |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| PortSwigger Lab                    | https://portswigger.net/web-security/sql-injection/examining-the-database/lab-querying-database-version-mysql-microsoft |
| OWASP A03:2021 — Injection         | https://owasp.org/Top10/A03_2021-Injection/                                                                             |
| CWE-89                             | https://cwe.mitre.org/data/definitions/89.html                                                                          |
| MITRE ATT&CK T1190                 | https://attack.mitre.org/techniques/T1190/                                                                              |
| OWASP Testing Guide OTG-INPVAL-005 | https://owasp.org/www-project-web-security-testing-guide/                                                               |
| CVSS v3.1 Calculator               | https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator                                                                    |
| MySQL 8.0 Release Notes            | https://dev.mysql.com/doc/relnotes/mysql/8.0/en/                                                                        |

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

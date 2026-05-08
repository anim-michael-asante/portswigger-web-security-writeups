# SQL Injection — Querying Database Type and Version on Oracle

[![Platform](https://img.shields.io/badge/Platform-PortSwigger_Web_Security_Academy-orange)](https://portswigger.net/web-security)
[![Category](https://img.shields.io/badge/Category-SQL_Injection-red)](https://owasp.org/www-community/attacks/SQL_Injection)
[![Difficulty](https://img.shields.io/badge/Difficulty-Apprentice-green)]()
[![Status](https://img.shields.io/badge/Status-Solved-brightgreen)]()
[![OWASP](https://img.shields.io/badge/OWASP-A03:2021_Injection-critical)](https://owasp.org/Top10/A03_2021-Injection/)
[![MITRE](https://img.shields.io/badge/MITRE-T1190-red)](https://attack.mitre.org/techniques/T1190/)
[![License](https://img.shields.io/badge/License-Educational_Use_Only-lightgrey)]()

---

## Table of Contents

1. [Overview](#overview)
2. [Scope and Objectives](#scope-and-objectives)
3. [Methodology](#methodology)
4. [Findings](#findings)
5. [Risk Summary](#risk-summary)
6. [Attack Chain](#attack-chain)
7. [Tools and Environment](#tools-and-environment)
8. [Evidence](#evidence)
9. [Remediation Strategy](#remediation-strategy)
10. [Lessons Learned](#lessons-learned)
11. [References](#references)
12. [Author](#author)

---

## Overview

This writeup documents the exploitation of a SQL injection vulnerability in the product category filter of a simulated e-commerce web application hosted on the PortSwigger Web Security Academy platform. The exercise required leveraging a UNION-based SQL injection attack to extract Oracle database version metadata — specifically the `BANNER` field from the `v$version` view. The lab was solved by constructing a well-formed UNION SELECT payload that matched the column count and data type requirements of the original query. This writeup is intended to demonstrate understanding of database fingerprinting techniques, Oracle-specific SQL syntax, and systematic injection testing methodology.

---

## Scope and Objectives

| Item | Detail |
|---|---|
| Platform | PortSwigger Web Security Academy |
| Lab Title | SQL injection attack, querying the database type and version on Oracle |
| Lab Tier | Apprentice |
| Target URL | `https://<lab-id>.web-security-academy.net/filter?category=Accessories` |
| In Scope | The `category` GET parameter in the product filter endpoint |
| Out of Scope | All other application endpoints, authentication mechanisms, and user data |
| Authorization | Fully authorized — isolated sandboxed lab environment |

**Primary Objective:** Exploit the SQL injection vulnerability in the `category` parameter to extract and display the Oracle database version string using a UNION-based attack.

---

## Methodology

The assessment followed the OWASP Testing Guide (OTG-INPVAL-005) and PTES web application testing standards, with the following phases applied:

**Phase 1 — Reconnaissance and Injection Point Identification**

The `category` GET parameter was identified as the injection point by observing that modifying its value directly influenced the SQL query results returned to the user. A single quote (`'`) was appended to confirm the parameter was not sanitized, and an HTTP 500 error response confirmed the application was processing unsanitized input in a backend SQL query.

**Phase 2 — Column Count Determination**

`ORDER BY` clause incrementation was used to enumerate the number of columns returned by the original query:

```sql
Accessories' ORDER BY 1--
Accessories' ORDER BY 2--
Accessories' ORDER BY 3--   -- HTTP 500 error returned, confirming 2 columns
```

This established that the original SELECT statement returns exactly **2 columns**.

**Phase 3 — Data Type Determination**

To confirm both columns accepted string output, a `UNION SELECT` with `NULL` placeholders and a test string was issued:

```sql
Accessories' UNION SELECT 'a', NULL FROM dual--
```

The response rendered content normally, confirming column 1 accepts character data. Oracle requires `FROM dual` in any SELECT statement not targeting a real table.

**Phase 4 — Database Version Extraction**

Oracle database version metadata is stored in the `v$version` dynamic performance view. The `BANNER` column contains the full version string. The final payload was constructed as:

```sql
Accessories' UNION SELECT BANNER, NULL FROM v$version--
```

This injected a second row into the result set containing the Oracle database version string, which was rendered in the application's product listing.

**Full URL (URL-encoded):**

```
/filter?category=Accessories'+UNION+SELECT+BANNER,+NULL+FROM+v$version--
```

---

## Findings

### Finding F-01 — SQL Injection via Unsanitized Category Filter Parameter

| Attribute | Detail |
|---|---|
| Finding ID | F-01 |
| Severity | [CRITICAL] |
| CVSS v3.1 Score | 9.8 |
| CVSS v3.1 Vector | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-89 — Improper Neutralization of Special Elements used in an SQL Command |
| OWASP Category | A03:2021 — Injection |
| MITRE ATT&CK TTP | T1190 — Exploit Public-Facing Application |
| Affected Component | GET `/filter?category=` parameter |

**Description**

The web application passes the value of the `category` GET parameter directly into a backend SQL query without sanitization or parameterization. An unauthenticated remote attacker can inject arbitrary SQL syntax to manipulate the query structure, extract data from the database, and potentially modify or delete records depending on database user privileges.

**Technical Impact**

- Unauthorized extraction of sensitive database metadata, schema information, and application data
- Ability to enumerate all database tables, columns, and stored records via subsequent UNION-based or error-based injection
- Potential for authentication bypass, data manipulation, or remote command execution depending on database configuration and privilege level

**Business Impact**

- Full exposure of backend Oracle database structure and contents to unauthenticated attackers
- Regulatory non-compliance risk under applicable data protection frameworks (e.g., GDPR, PCI-DSS)
- Reputational and legal consequences if user data is exfiltrated

**Proof of Concept**

The following payload was injected into the `category` parameter:

```sql
Accessories' UNION SELECT BANNER, NULL FROM v$version--
```

The application returned the Oracle database version banner string as a product listing entry, confirming arbitrary SQL execution.

**Reproduction Steps**

1. Navigate to the lab's product listing page.
2. Intercept or manually modify the GET request to the `/filter` endpoint.
3. Replace the `category` parameter value with the payload below:
   ```
   Accessories' UNION SELECT BANNER, NULL FROM v$version--
   ```
4. Observe the Oracle database version string rendered in the application response.

**Remediation**

See [Remediation Strategy](#remediation-strategy) — F-01.

**Retest Criteria**

After remediation, inject the same payload. The application must return either an HTTP 400/403 response or an empty/generic product list with no database version information disclosed. Error messages must not reveal SQL syntax or database details.

---

## Risk Summary

| ID | Title | Severity | CVSS v3.1 | Priority |
|---|---|---|---|---|
| F-01 | SQL Injection — Category Filter | [CRITICAL] | 9.8 | [IMMEDIATE] |

---

## Attack Chain

```
[Unauthenticated Attacker]
        |
        v
[1. Identify Injectable Parameter]
   GET /filter?category=Accessories
   -> Append single quote -> HTTP 500 confirms unsanitized input
        |
        v
[2. Enumerate Column Count]
   ORDER BY 1-- / ORDER BY 2-- / ORDER BY 3-- (error)
   -> Confirmed: 2 columns returned
        |
        v
[3. Confirm String-Compatible Column]
   UNION SELECT 'a', NULL FROM dual--
   -> Column 1 accepts character data
        |
        v
[4. Extract Oracle Version Metadata]
   UNION SELECT BANNER, NULL FROM v$version--
   -> Oracle version string rendered in application response
        |
        v
[OBJECTIVE MET — Database version disclosed to unauthenticated attacker]
```

**MITRE ATT&CK Mapping**

| Phase | Technique | ID |
|---|---|---|
| Initial Access | Exploit Public-Facing Application | T1190 |
| Discovery | System Information Discovery | T1082 |

---

## Tools and Environment

| Tool / Resource | Version / Detail | Purpose |
|---|---|---|
| Browser (Chromium) | Latest stable | Manual request crafting and response observation |
| PortSwigger Web Security Academy | Apprentice Lab | Authorized target environment |
| Oracle Database (target) | Version disclosed via `v$version` | Backend DBMS |
| Burp Suite Community (optional) | 2024.x | HTTP interception and parameter manipulation |

---

## Evidence

### Screenshot — Lab Solved

![PortSwigger lab solved confirmation screen showing Oracle database version injected into product listing](./assets/lab-solved.png)

*Figure 1: Lab solved confirmation. The Oracle database `BANNER` string is rendered as a product listing item, confirming successful UNION-based SQL injection.*

### Payload Used

```sql
Accessories' UNION SELECT BANNER, NULL FROM v$version--
```

### URL (URL-encoded)

```
/filter?category=Accessories'+UNION+SELECT+BANNER,+NULL+FROM+v%24version--
```

### Observed Output

The application returned the Oracle database version banner (e.g., `Oracle Database 11g Express Edition Release 11.2.0.2.0 - 64bit Production`) rendered inline within the product listing, confirming arbitrary SQL execution and information disclosure.

---

## Remediation Strategy

### F-01 — SQL Injection via Unsanitized Category Filter [IMMEDIATE]

**Primary Fix — Parameterized Queries (Prepared Statements)**

Replace all dynamic string concatenation in SQL query construction with parameterized queries or prepared statements. The `category` value must be passed as a bound parameter, not interpolated into the query string.

Example (Java — JDBC):

```java
String query = "SELECT name, description FROM products WHERE category = ?";
PreparedStatement stmt = connection.prepareStatement(query);
stmt.setString(1, categoryInput);
ResultSet rs = stmt.executeQuery();
```

**Secondary Controls**

| Control | Detail |
|---|---|
| Input Validation | Whitelist acceptable `category` values at the application layer; reject any value not in the predefined set |
| Least Privilege | The database user account used by the application must have SELECT-only access to required tables — no access to `v$version`, `ALL_TABLES`, or system views |
| Error Handling | Suppress all verbose database error messages from HTTP responses; log internally only |
| WAF Rule | Deploy a WAF rule to detect and block SQL injection patterns (`UNION`, `SELECT`, `--`, `v$version`) in GET parameters |

**Retest Criteria**

Inject `Accessories' UNION SELECT BANNER, NULL FROM v$version--` into the `category` parameter post-remediation. Expected result: HTTP 400/403 or empty product list with no database information disclosed.

---

## Lessons Learned

**1. Oracle SQL syntax differs from other DBMS platforms**
Unlike MySQL or PostgreSQL, Oracle requires `FROM dual` in SELECT statements that do not reference a real table. Awareness of DBMS-specific syntax is required before crafting UNION-based payloads.

**2. Column count and data type enumeration must precede UNION injection**
A UNION SELECT fails if the injected query does not match the original query's column count and compatible data types. Systematic enumeration using `ORDER BY` and `NULL` placeholders is necessary before extracting real data.

**3. System views are high-value targets in Oracle environments**
`v$version`, `ALL_TABLES`, and `ALL_COLUMNS` are Oracle-specific views that expose database structure and metadata. Least-privilege database configuration should revoke application user access to these views.

**4. Parameterized queries eliminate this entire class of vulnerability**
SQL injection is a solved problem at the framework level. Parameterized queries or ORMs with proper binding make UNION-based, error-based, and blind SQL injection attacks ineffective regardless of payload sophistication.

---

## References

| Reference | URL |
|---|---|
| PortSwigger — SQL Injection | https://portswigger.net/web-security/sql-injection |
| PortSwigger — UNION Attacks | https://portswigger.net/web-security/sql-injection/union-attacks |
| OWASP A03:2021 — Injection | https://owasp.org/Top10/A03_2021-Injection/ |
| CWE-89 — SQL Injection | https://cwe.mitre.org/data/definitions/89.html |
| MITRE ATT&CK T1190 | https://attack.mitre.org/techniques/T1190/ |
| Oracle v$version Reference | https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/V-VERSION.html |
| NIST SP 800-115 | https://csrc.nist.gov/publications/detail/sp/800/115/final |
| CVSS v3.1 Calculator | https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator |

---

## Author

**Michael Asante Anim** | `0x1aerixis`
BSc Cyber Security — University of Mines and Technology (UMaT), Tarkwa, Ghana
Member, The Digital Frontline

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

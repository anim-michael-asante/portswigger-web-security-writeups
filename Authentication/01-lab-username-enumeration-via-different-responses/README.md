# Username Enumeration via Different Responses

## Overview
This project documents the exploitation of a username enumeration and password brute-force vulnerability in a PortSwigger Web Security Academy lab. The application returns distinguishable responses for valid versus invalid usernames during login, enabling an attacker to enumerate a valid account and subsequently brute-force its password.

**Status:** Solved
**Category:** Authentication
**Target:** PortSwigger Web Security Academy — Authentication labs

## Vulnerability Classification

| Field | Value |
|---|---|
| CWE | CWE-204: Observable Response Discrepancy |
| CWE (secondary) | CWE-307: Improper Restriction of Excessive Authentication Attempts |
| OWASP | A07:2021 – Identification and Authentication Failures |
| CVSS v3.1 | 5.3 (Medium) — AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N |
| MITRE ATT&CK | T1589.001 (Gather Victim Identity Information: Credentials), T1110.001 (Brute Force: Password Guessing) |

## Methodology

### 1. Reconnaissance
Submitted an invalid username and password to the login form while intercepting traffic with Burp Suite. Located the `POST /login` request in Proxy > HTTP History.

### 2. Username Enumeration
Sent the `POST /login` request to Burp Intruder and marked the `username` parameter as the payload position, using Sniper attack mode with the candidate username wordlist. Sorted results by response `Length`.

One entry returned a distinct response length (6647 vs. 6645 for all others), corresponding to the message "Incorrect password" rather than "Invalid username" — confirming a valid username.

**Enumerated username:** `info`

### 3. Password Brute-Force
Fixed the identified username in the request body and marked the `password` parameter as the new payload position. Loaded the candidate password wordlist and ran a second Sniper attack, this time sorting by `Status code`.

All requests returned `200 OK` except one, which returned `302 Found` — indicating a successful authentication redirect.

**Identified password:** `sunshine`

### 4. Validation
Logged in using `info:sunshine` and confirmed access to the account page, solving the lab.

## Evidence

| Artifact | Description |
|---|---|
| `bruteforce-username.png` | Intruder attack results showing anomalous response length for username `info` |
| `bruteforce-password.png` | Intruder attack results showing `302` status code for password `sunshine` |
| `lab-solved.png` | Confirmation of successful account access |

### Username Enumeration — Anomalous Response Length
![Username enumeration Intruder results](./evidence/bruteforce-username.png)

### Password Brute-Force — 302 Redirect
![Password brute-force Intruder results](./evidence/bruteforce-password.png)

### Lab Solved
![Lab solved confirmation](./evidence/lab-solved.png)

## Root Cause
The application's authentication endpoint returned different error messages depending on whether the submitted username existed in the system ("Invalid username" vs. "Incorrect password"). This discrepancy allowed an attacker to distinguish valid from invalid accounts without needing the correct password, reducing the credential-guessing search space to a single, confirmed username.

## Remediation
- Return a single, generic error message (e.g., "Invalid username or password") for all failed login attempts, regardless of which field was incorrect.
- Ensure response time, length, and status code are consistent across valid and invalid username submissions.
- Implement account lockout or rate-limiting (e.g., exponential backoff, CAPTCHA) after a threshold of failed login attempts to mitigate brute-force attacks.
- Consider multi-factor authentication as a defense-in-depth control.

## References
- NIST SP 800-63B — Digital Identity Guidelines, Authentication and Lifecycle Management
- OWASP Authentication Cheat Sheet
- CWE-204: Observable Response Discrepancy
- MITRE ATT&CK T1110.001: Brute Force — Password Guessing

## Tools Used
- Burp Suite (Proxy, Intruder)

---
Built by Grace

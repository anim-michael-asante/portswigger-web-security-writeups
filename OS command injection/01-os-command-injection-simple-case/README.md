# OS Command Injection — Simple Case

> PortSwigger Web Security Academy lab demonstrating unauthenticated OS command injection in a stock-checking feature, achieving arbitrary command execution on the backend host.

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Type](https://img.shields.io/badge/Type-CTF--Writeup-blue)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-orange)
![Author](https://img.shields.io/badge/Author-0x1aerixis-black)

## Table of Contents
- [Overview](#overview)
- [Scope & Objectives](#scope--objectives)
- [Methodology](#methodology)
- [Findings / Results](#findings--results)
- [Tools & Environment](#tools--environment)
- [Evidence](#evidence)
- [Lessons Learned](#lessons-learned)
- [References](#references)
- [Author](#author)

## Overview

Applications that build shell commands from user-supplied input without sanitization expose the underlying host to arbitrary command execution, regardless of authentication state. This class of flaw can lead to full server compromise, data exfiltration, or lateral movement into internal infrastructure.

This project documents a PortSwigger Web Security Academy lab (OS command injection, simple case) in which a product stock-checking endpoint passed unsanitized request parameters directly into a shell command. Burp Suite was used to intercept and modify the request, appending a shell metacharacter and the `whoami` command to the vulnerable parameter.

The injected command executed successfully, and the response returned the identity of the user running the backend process, confirming the lab objective and demonstrating full command execution primitive.

> **Key Outcome:** Achieved arbitrary OS command execution via unsanitized parameter concatenation into a server-side shell command, confirmed by successful `whoami` execution.

## Scope & Objectives

### Objectives
- Identify the parameter responsible for constructing the server-side shell command
- Inject a shell command separator followed by `whoami` to prove command execution
- Confirm execution via the raw command output returned in the HTTP response

### In Scope
| Target | Description | Type |
|--------|-------------|------|
| `0a6700dd0401874980d7a310001800b8.web-security-academy.net` | PortSwigger Web Security Academy lab instance | Web App |
| `/product/stock` | Stock-checking endpoint accepting `productId` and `storeId` | Endpoint |

### Out of Scope
- All other lab endpoints not related to the stock-checker feature
- Any infrastructure outside the provisioned PortSwigger lab instance

### Engagement Type
> **Type:** Black-box
> **Authorization:** PortSwigger Web Security Academy — sanctioned training lab
> **Duration:** Single session

## Methodology

This exercise followed a condensed recon-to-exploitation approach aligned with the OWASP Testing Guide and MITRE ATT&CK.

| Phase | Activity | Framework Reference |
|-------|----------|-------------------|
| Reconnaissance | Identified the stock-check request and its parameters via Burp Proxy | OWASP Testing Guide |
| Enumeration | Sent the request to Burp Repeater to isolate parameter behavior | PTES — Vulnerability Identification |
| Exploitation | Appended `\|whoami` to the `storeId` parameter to chain an additional OS command | MITRE ATT&CK — Execution (TA0002), T1059 |
| Validation | Confirmed the response body contained the current OS user, verifying command execution | OWASP Testing Guide |

> **Note:** All testing was conducted against an isolated, authorized PortSwigger Web Security Academy lab instance. No production systems were accessed.

## Findings / Results

---

### VULN-001 — OS Command Injection via `storeId` Parameter

| Field | Detail |
|-------|--------|
| **Severity** | [CRITICAL] |
| **CVSS v3.1 Score** | 9.8 |
| **CVSS Vector** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| **CWE** | [CWE-78: Improper Neutralization of Special Elements used in an OS Command](https://cwe.mitre.org/data/definitions/78.html) |
| **OWASP Category** | [A03:2021 – Injection](https://owasp.org/Top10/A03_2021-Injection/) |
| **MITRE ATT&CK** | [T1059 – Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/) |
| **Affected Component** | `POST /product/stock` — `storeId` request parameter |

#### Description
The stock-checking endpoint accepts `productId` and `storeId` as URL-encoded form parameters and passes them, unsanitized, into a server-side shell command used to look up stock levels. Because the application does not filter shell metacharacters, an attacker can append the pipe character (`|`) followed by an arbitrary OS command, causing the shell to execute it after the intended lookup command.

#### Technical Impact
An attacker can execute arbitrary operating system commands with the privileges of the web application process. This can lead to disclosure of the current user context, reading of local files, further reconnaissance of the host, and potential pivoting to other systems reachable from the compromised server.

#### Business Impact
Unrestricted command execution on a production backend could result in full compromise of the affected server, exposure of customer or business data, and service disruption. Depending on data handled by the application, this may trigger regulatory breach-notification obligations and reputational damage.

#### Proof of Concept

```http
POST /product/stock HTTP/2
Host: 0a6700dd0401874980d7a310001800b8.web-security-academy.net
Content-Type: application/x-www-form-urlencoded
Content-Length: 28

productId=1&storeId=1|whoami
```

> **Screenshot:** `evidence/vuln-001-poc-request.png`
> *Burp Suite Repeater request showing the `storeId` parameter modified to `1|whoami`, with the HTTP 200 response returning the current OS user in the response body.*

#### Reproduction Steps
1. Browse a product page and trigger a stock check to capture the `POST /product/stock` request in Burp Proxy.
2. Send the request to Burp Repeater.
3. Modify the `storeId` parameter value from `1` to `1|whoami`.
4. Send the request and observe that the response body contains the output of `whoami` instead of, or in addition to, the expected stock value.

#### Remediation
> **Priority:** Immediate
> **Effort:** Medium

Eliminate direct concatenation of user input into shell commands. Replace shell invocation with a safe API that does not interpret shell metacharacters (for example, calling the required functionality through a language-level library rather than `/bin/sh`). Where shelling out is unavoidable, use an allowlist of expected characters for `productId` and `storeId` (e.g., numeric-only validation) and invoke the command using an argument array rather than a concatenated string, so metacharacters cannot be interpreted by a shell.

#### Retest Criteria
- [ ] Submitting `storeId=1|whoami` (and equivalent separators `;`, `&&`, `` ` ``, `$( )`) no longer returns command output
- [ ] Non-numeric or metacharacter input to `productId`/`storeId` is rejected with a controlled error response

## Tools & Environment

| Tool | Purpose |
|------|---------|
| Burp Suite Community Edition v2026.7.3 | Intercepting proxy and Repeater used to modify and replay the vulnerable request |
| PortSwigger Web Security Academy | Hosted, sanctioned lab environment |
| Chrome | Browser used to interact with the lab application |

## Evidence

| File | Description |
|------|--------------|
| `evidence/vuln-001-poc-request.png` | Burp Repeater request/response showing the `storeId=1\|whoami` payload and the returned username |
| `evidence/vuln-001-lab-solved.png` | Lab status confirmation showing "Congratulations, you solved the lab!" |

## Lessons Learned

- Any point where user input reaches a shell invocation, directly or indirectly, must be treated as a potential command injection sink.
- Pipe and other shell metacharacters (`|`, `;`, `&&`, `` ` ``, `$( )`) are sufficient to chain additional commands when input is concatenated into a shell string without sanitization.
- Response-based confirmation (observing command output reflected back to the client) is a reliable way to validate command injection without relying on blind/time-based techniques.

## References

- [PortSwigger Web Security Academy — OS command injection](https://portswigger.net/web-security/os-command-injection)
- [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- [OWASP Top 10 2021 — A03: Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [MITRE ATT&CK — T1059: Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/)

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

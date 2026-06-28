# File Path Traversal — Null Byte Bypass in File Extension Validation

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Platform](https://img.shields.io/badge/Platform-PortSwigger-red)
![Difficulty](https://img.shields.io/badge/Difficulty-Apprentice-orange)
![Type](https://img.shields.io/badge/Type-Pentest--Simulation-blue)
![Author](https://img.shields.io/badge/Author-0x1aerixis-black)

---

## Table of Contents

- [Overview](#overview)
- [Scope & Objectives](#scope--objectives)
- [Methodology](#methodology)
- [Findings & Results](#findings--results)
- [Risk Summary](#risk-summary)
- [Attack Chain](#attack-chain)
- [Tools & Environment](#tools--environment)
- [Evidence](#evidence)
- [Remediation Strategy](#remediation-strategy)
- [Lessons Learned](#lessons-learned)
- [References](#references)
- [Author](#author)

---

## Overview

This write-up documents the exploitation of a path traversal vulnerability protected by file extension validation in a PortSwigger Web Security Academy lab. The application restricts file retrieval to filenames ending with `.png`, yet fails to account for null byte (`%00`) injection — a legacy string-termination technique that causes the backend file operation to discard the extension suffix before processing the path.

The objective was to bypass the extension check, traverse outside the web root, and retrieve `/etc/passwd` from the server filesystem. Exploitation was achieved in a single request using Burp Suite Repeater.

This technique is most relevant in legacy PHP environments (pre-5.3.4) and any application that constructs file paths via string concatenation without null byte filtering or path canonicalization prior to file operations.

---

## Scope & Objectives

### Objectives

- Demonstrate null byte injection as a bypass against file extension validation
- Retrieve `/etc/passwd` using a combined path traversal and null byte payload
- Map the vulnerability to OWASP Top 10, CWE, and MITRE ATT&CK
- Document remediation controls that would prevent this class of vulnerability

### In Scope

| Target | Description | Type |
|--------|-------------|------|
| PortSwigger Lab 06 | Path traversal — null byte bypass | Web Application |
| `/image` endpoint | Product image retrieval via `filename` parameter | Web API Endpoint |
| `/etc/passwd` | Target system file for proof of exploitation | Filesystem Resource |

### Out of Scope

- Source code review or static analysis
- Authentication and authorization testing
- Network-level or infrastructure attacks
- Denial of service or availability testing
- Privilege escalation beyond unauthenticated file read

### Engagement Type

| Attribute | Value |
|-----------|-------|
| Type | Authorized security training (white-box simulation) |
| Platform | PortSwigger Web Security Academy |
| Authorization | Self-hosted lab environment |
| Duration | Single session |

---

## Methodology

Exploitation followed the **OWASP Testing Guide v4.2** methodology for input validation testing (OTG-INPVAL-013) and the **PTES Exploitation Phase** framework.

### Phase 1 — Reconnaissance & Parameter Identification

- Identified the `filename` parameter in the `/image` endpoint as the injection point
- Confirmed the application enforces a `.png` extension requirement on all file requests
- Verified that directory traversal sequences (`../`) were passed to the backend without stripping

### Phase 2 — Vulnerability Analysis

- Identified that extension validation was performed via trailing string match only
- Determined that null byte (`%00`) terminates string processing in C-based file operations and legacy PHP
- Constructed hypothesis: appending `%00.png` would satisfy the extension check while the file operation would terminate at the null byte

### Phase 3 — Payload Construction

| Component | Value | Purpose |
|-----------|-------|---------|
| Traversal sequence | `../../../` | Exit web root to filesystem root |
| Target path | `etc/passwd` | Sensitive system file |
| Null byte | `%00` | Terminate string at file operation layer |
| Extension bypass | `.png` | Satisfy server-side extension validation |
| Full payload | `../../../etc/passwd%00.png` | Combined bypass vector |

### Phase 4 — Exploitation & Validation

- Injected payload via Burp Suite Repeater into the `filename` parameter
- Received HTTP 200 response containing `/etc/passwd` file contents
- Confirmed exploitation via presence of system user records in the response body

---

## Findings & Results

### Finding PT-01: Path Traversal via Null Byte Injection in Extension Validation

**Severity:** [HIGH]
**CVSS v3.1 Score:** 7.5
**CVSS Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`

#### Classification

| Framework | Value |
|-----------|-------|
| CWE | CWE-22 — Improper Limitation of a Pathname to a Restricted Directory |
| CWE (Secondary) | CWE-158 — Improper Neutralization of Null Byte or NUL Character |
| OWASP Top 10 2021 | A01 — Broken Access Control |
| OWASP Category | Path Traversal / Directory Traversal |

#### MITRE ATT&CK Mapping

| Tactic | Technique ID | Technique Name |
|--------|-------------|----------------|
| Discovery | T1083 | File and Directory Discovery |
| Collection | T1005 | Data from Local System |
| Exfiltration | T1041 | Exfiltration Over C2 Channel |

#### Affected Component

`GET /image?filename=<user-controlled input>` — no sanitization, no path canonicalization, no null byte filtering applied prior to file operation.

#### Technical Description

The application constructs a file path by appending the user-supplied `filename` parameter to a base directory (`/var/www/images/`). Before executing the file read, the application validates that the filename ends with `.png`. This check is performed on the raw input string without prior path canonicalization or null byte filtering.

When the filename contains a null byte (`%00`), the extension check passes because `.png` appears at the end of the submitted string. However, at the file operation layer — particularly in C-based runtimes and PHP versions prior to 5.3.4 — the null byte terminates the string. The resulting path passed to the filesystem resolves to `/etc/passwd`, discarding the `.png` suffix entirely.

**Vulnerable pattern (conceptual PHP):**

```php
$filename = $_GET['filename'];

// Validation: passes because string ends with '.png'
if (substr($filename, -4) === '.png') {
    $path = '/var/www/images/' . $filename;
    readfile($path); // File operation terminates at null byte
}
```

**Request execution sequence:**

1. Input received: `../../../etc/passwd%00.png`
2. Extension check: passes — input ends with `.png`
3. Path constructed: `/var/www/images/../../../etc/passwd\0.png`
4. File operation: string terminates at `\0` — resolves to `/etc/passwd`
5. Response: contents of `/etc/passwd` returned with HTTP 200

#### Proof of Concept

**HTTP Request:**

```http
GET /image?filename=../../../etc/passwd%00.png HTTP/1.1
Host: <lab-instance>.web-security-academy.net
User-Agent: Mozilla/5.0 (X11; Linux x86_64)
Accept: image/webp,image/avif,image/*,*/*;q=0.8
Connection: keep-alive
```

**HTTP Response (excerpt):**

```
HTTP/1.1 200 OK
Content-Type: image/jpeg

root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/sys:/usr/sbin/nologin
```

#### Reproduction Steps

1. Open Burp Suite and configure browser proxy
2. Navigate to any product page and intercept the image request
3. Send the image request to Repeater
4. Modify the `filename` parameter to: `../../../etc/passwd%00.png`
5. Forward the request
6. Observe HTTP 200 response containing `/etc/passwd` contents

#### Impact Analysis

| Impact Category | Rating | Justification |
|-----------------|--------|---------------|
| Confidentiality | HIGH | Unauthenticated read of arbitrary filesystem files |
| Integrity | NONE | No write or modification capability via this vector |
| Availability | NONE | No disruption to application function |

**Business Impact:**

- Direct disclosure of system user accounts, UIDs, GIDs, and shell assignments
- Enables attacker reconnaissance for credential attacks against valid system users
- Potential compliance violation under data protection frameworks (GDPR, Ghana Data Protection Act)
- If application config files are within traversal range, impact escalates to credential exposure

---

## Risk Summary

| ID | Finding | Severity | CVSS | Affected Component | Priority |
|----|---------|----------|------|--------------------|----------|
| PT-01 | Path traversal via null byte bypass | [HIGH] | 7.5 | `/image?filename` | [IMMEDIATE] |

---

## Attack Chain

```
[Attacker]
    |
    | HTTP GET /image?filename=../../../etc/passwd%00.png
    v
[Application — Extension Validation Layer]
    |
    | substr($filename, -4) === '.png'  --> PASS
    v
[Application — Path Construction]
    |
    | /var/www/images/ + ../../../etc/passwd%00.png
    v
[File Operation Layer — Null Byte Termination]
    |
    | String terminates at \0
    | Resolved path: /etc/passwd
    v
[Filesystem]
    |
    | readfile('/etc/passwd')  --> Success
    v
[HTTP Response]
    |
    | 200 OK | Content-Type: image/jpeg
    | Body: /etc/passwd contents
    v
[Attacker — Sensitive file exfiltrated]
```

---

## Tools & Environment

### Tools Used

| Tool | Version | Purpose |
|------|---------|---------|
| Burp Suite Community Edition | v2026.3.2 | HTTP proxy, request interception, Repeater |
| Brave Browser | Latest | HTTP client and lab interaction |
| Kali Linux | Rolling | Attack host OS |
| Burp Decoder | Built-in | URL encoding verification for `%00` |

### Lab Environment

| Component | Specification |
|-----------|---------------|
| Target | PortSwigger Web Security Academy — Lab 06 |
| Attack Host OS | Kali Linux (VMware) |
| Network | NAT / lab-provided |
| Access Level | Unauthenticated |
| Proxy | Burp Suite (127.0.0.1:8080) |

---

## Evidence

### Lab Completion Confirmation

![Lab solved confirmation — 'File path traversal, validation of file extension with null byte bypass' marked as LAB Solved](evidence/01-lab-solved-confirmation.png)

*Lab marked as solved by PortSwigger upon successful retrieval of `/etc/passwd`.*

### Burp Suite Exploitation

![Burp Suite Repeater showing HTTP GET request with payload ../../../etc/passwd%00.png and HTTP 200 response containing /etc/passwd file contents](evidence/02-burp-suite-exploitation.png)

*Burp Suite Repeater: null byte bypass payload (top panel) and server response containing `/etc/passwd` contents (bottom panel). The `Content-Type: image/jpeg` header confirms the application returned the file without recognizing it as non-image data.*

### Key Artifacts

| Artifact | Value | Significance |
|----------|-------|--------------|
| Payload | `../../../etc/passwd%00.png` | Null byte-injected path traversal vector |
| HTTP Status | 200 OK | Confirms successful exploitation |
| Response Content | `/etc/passwd` file contents | Proof of arbitrary file read |
| Content-Type | `image/jpeg` | Confirms absence of response validation |

---

## Remediation Strategy

### PT-01 — Controls for Null Byte Bypass in Extension Validation

**Priority:** [IMMEDIATE]

#### Primary Controls

**1. Reject null bytes at input validation layer**

```python
import os

filename = request.GET.get('filename', '')

# Reject null bytes before any processing
if '\x00' in filename or '%00' in filename:
    return HttpResponseBadRequest('Invalid filename.')
```

**2. Canonicalize path before validation**

```python
BASE_DIR = '/var/www/images'

filename = request.GET.get('filename', '')
requested_path = os.path.realpath(os.path.join(BASE_DIR, filename))

# Verify resolved path is within the allowed base directory
if not requested_path.startswith(BASE_DIR + os.sep):
    return HttpResponseForbidden('Access denied.')
```

**3. Whitelist permitted filenames**

```python
import re

ALLOWED_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+\.png$')

if not ALLOWED_PATTERN.match(filename):
    return HttpResponseBadRequest('Invalid filename format.')
```

#### Defense-in-Depth Controls

| Control | Description | Priority |
|---------|-------------|----------|
| Input validation | Strip or reject `../`, `..\\`, and null byte variants at entry point | [IMMEDIATE] |
| Path canonicalization | Resolve all traversal sequences before file operations | [IMMEDIATE] |
| Whitelist filenames | Accept only alphanumeric filenames with known-good extensions | [SHORT-TERM] |
| Least privilege | Run application process with minimal filesystem permissions | [SHORT-TERM] |
| Chroot / sandbox | Restrict file operations to a confined directory | [PLANNED] |

#### Retest Criteria

The vulnerability is remediated when all of the following return HTTP 400 or HTTP 403 without file contents in the response body:

```
GET /image?filename=../../../etc/passwd%00.png
GET /image?filename=..%2F..%2F..%2Fetc%2Fpasswd%00.png
GET /image?filename=%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd%00.png
```

---

## Lessons Learned

### Technical Insights

**Null byte handling across contexts:**
Null bytes (`\0` / `%00`) terminate strings in C-family languages and many file I/O operations. HTTP URL encoding (`%00`) and backend string processing may interpret null bytes differently depending on framework version and language runtime. PHP versions prior to 5.3.4 explicitly expose this behavior; modern versions are more resistant but custom implementations may reintroduce it.

**File extension validation limitations:**
Simple string matching (`endswith()`, `substr()`) is insufficient as a security control when applied to raw, unsanitized input. Extension validation must be combined with path canonicalization, null byte rejection, and character whitelisting to be effective.

**Defense-in-depth principle:**
This lab demonstrates single-layer validation failure. A correctly implemented file retrieval function would apply multiple controls in sequence — null byte rejection, path normalization, boundary check, and whitelist validation — such that bypassing one layer does not result in exploitation.

### Skills Reinforced

- HTTP parameter manipulation via Burp Suite Repeater
- URL encoding mechanics and null byte injection
- Path traversal attack vector construction
- CVSS v3.1 scoring and vector calculation
- OWASP Testing Guide methodology application
- MITRE ATT&CK framework mapping

### Real-World Applicability

Null byte injection was prevalent in pre-2010 web applications. While modern frameworks provide stronger default protections, the technique remains relevant for:

- Penetration testing legacy applications running older PHP, Python 2, or custom C extensions
- Understanding vulnerability chains during code review engagements
- Identifying defense bypass opportunities where input validation is implemented manually rather than through framework primitives

---

## References

### Vulnerability Standards & Frameworks

- **OWASP Top 10 2021 — A01: Broken Access Control**
  https://owasp.org/Top10/A01_2021-Broken_Access_Control/

- **OWASP Testing Guide v4.2 — Path Traversal Testing (OTG-INPVAL-013)**
  https://owasp.org/www-project-web-security-testing-guide/v4.2/4-Web_Application_Security_Testing/05-Authorization_Testing/01-Testing_for_Path_Traversal

- **CWE-22: Improper Limitation of a Pathname to a Restricted Directory**
  https://cwe.mitre.org/data/definitions/22.html

- **CWE-158: Improper Neutralization of Null Byte or NUL Character**
  https://cwe.mitre.org/data/definitions/158.html

- **NIST SP 800-115: Technical Security Testing and Assessment**
  https://csrc.nist.gov/publications/detail/sp/800-115/final

### Technical References

- **PHP 5.3.4 Changelog — Null Byte Handling Improvements**
  https://www.php.net/releases/5_3_4.php

- **MITRE ATT&CK — T1083: File and Directory Discovery**
  https://attack.mitre.org/techniques/T1083/

- **MITRE ATT&CK — T1005: Data from Local System**
  https://attack.mitre.org/techniques/T1005/

- **CVSS v3.1 Calculator (NVD)**
  https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator

### Learning Resources

- **PortSwigger Web Security Academy — Path Traversal**
  https://portswigger.net/web-security/file-path-traversal

- **PTES — Penetration Testing Execution Standard**
  http://www.pentest-standard.org/

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

> **Disclaimer:** All work documented in this repository was conducted in authorized, isolated lab environments or sanctioned CTF platforms. No unauthorized systems were accessed. This project is intended for educational and portfolio purposes only.

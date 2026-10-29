import datetime
import json
import os
import sys
import urllib.request
import urllib.parse
import time

BEARER = os.environ.get("X_BEARER", "")
DAHL_URL = os.environ.get("DAHL_API_URL", "")
DAHL_KEY = os.environ.get("DAHL_API_KEY", "")
DAHL_MODEL = os.environ.get("DAHL_MODEL", "")
TEST = os.environ.get("TEST", "true").lower() == "true"

BASE = "https://api.twitter.com"

print("=== X REPLY AGENT ===")
print(f"Test: {TEST}")

def get(endpoint, params=None):
    url = BASE + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + BEARER})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print("Error: " + str(e))
        return None

def post(endpoint, data):
    url = BASE + endpoint
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
        headers={"Authorization": "Bearer " + BEARER, "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print("Error: " + str(e))
        return None

me = get("/2/users/me")
if not me or "data" not in me:
    print("Auth failed - check X_BEARER_TOKEN secret")
    sys.exit(1)

my_id = me["data"]["id"]
print("Logged in as @" + me["data"]["username"])

mentions = get("/2/users/" + my_id + "/mentions", {
    "max_results": 10,
    "tweet.fields": "author_id",
    "expansions": "author_id",
    "user.fields": "username"
})

if not mentions or "data" not in mentions:
    print("No mentions")
    sys.exit(0)

tweets = mentions.get("data", [])
users = {u["id"]: u for u in mentions.get("includes", {}).get("users", [])}
print("Found " + str(len(tweets)) + " mentions")

def make_reply(text, author):
    prompt = "Reply to this tweet as Natron Theory CEO. Tweet from @" + author + ": " + text + " Keep under 200 chars. Be friendly. Return only the reply."
    try:
        req = urllib.request.Request(DAHL_URL,
            data=json.dumps({"model": DAHL_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 200}).encode(),
            headers={"Authorization": "Bearer " + DAHL_KEY, "Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("DAHL error: " + str(e))
        return None

for t in tweets:
    author = users.get(t["author_id"], {}).get("username", "?")
    print("@" + author + ": " + t["text"][:50] + "...")
    r = make_reply(t["text"], author)
    if r:
        print("Reply: " + r)
        if not TEST:
            post("/2/tweets", {"text": r, "reply": {"in_reply_to_tweet_id": t["id"]}})
        else:
            print("TEST MODE")
    time.sleep(1)

print("Done")

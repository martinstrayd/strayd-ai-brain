import os
import requests
import json
from datetime import datetime, timedelta, timezone

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USER_ACCESS_TOKEN = os.getenv("X_USER_ACCESS_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

AI_ENDPOINT = "https://inference.dahl.global/v1/chat/completions"
MODEL = "MiniMaxAI/MiniMax-M2.7"
KEYWORDS = '"Natron theory" OR geopolymer OR "artificial stone"'

LOG_DIR = "logs"

def search_recent():
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": KEYWORDS,
        "tweet.fields": "author_id,conversation_id",
        "max_results": 10,
        "start_time": (datetime.now(timezone.utc) - timedelta(hours=9)).isoformat()
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    r = requests.get(url, headers=headers, params=params)
    return r.json().get("data", [])

def call_ai(text):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": f"Reply concisely and naturally to this tweet: {text}"}]
    }
    r = requests.post(
        AI_ENDPOINT,
        headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    return r.json()["choices"][0]["message"]["content"].strip()

def reply(tweet_id, text):
    url = "https://api.x.com/2/tweets"
    payload = {"reply": {"in_reply_to_tweet_id": tweet_id}, "text": text[:280]}
    headers = {"Authorization": f"Bearer {USER_ACCESS_TOKEN}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload)
    return r.status_code

def write_log(entries):
    os.makedirs(LOG_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(LOG_DIR, f"natron-{today}.md")

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"## Run at {datetime.now(timezone.utc).isoformat()}\n\n")
        if not entries:
            f.write("No new mentions found.\n\n")
        else:
            for e in entries:
                f.write(f"**Tweet:** {e['text']}\n\n")
                f.write(f"**Reply:** {e['reply']}\n\n")
                f.write("---\n\n")
    print(f"Log written to {filepath}")

def main():
    print("=== Natron Monitor started ===")
    tweets = search_recent()
    log_entries = []

    if not tweets:
        print("No new mentions found")
    else:
        print(f"Found {len(tweets)} matching tweet(s)")
        for t in tweets:
            text = t["text"]
            tweet_id = t["id"]
            print(f"Processing: {text[:80]}...")

            try:
                reply_text = call_ai(text)
                if reply_text:
                    status = reply(tweet_id, reply_text)
                    log_entries.append({"text": text, "reply": reply_text})
                    print(f"  -> Replied (status: {status})")
            except Exception as e:
                print(f"  -> Error: {e}")

    write_log(log_entries)
    print("=== Finished ===")

if __name__ == "__main__":
    main()

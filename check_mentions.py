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

def main():
    print("=== Natron Monitor started ===")
    tweets = search_recent()

    if not tweets:
        print("No new mentions found")
        print("=== Finished ===")
        return

    print(f"Found {len(tweets)} matching tweet(s)")

    for i, t in enumerate(tweets, 1):
        text = t["text"]
        tweet_id = t["id"]
        print(f"\n[{i}/{len(tweets)}] Tweet: {text[:100]}...")

        try:
            reply_text = call_ai(text)
            if reply_text:
                status = reply(tweet_id, reply_text)
                print(f"  -> Replied (status: {status})")
            else:
                print("  -> AI returned empty reply, skipping")
        except Exception as e:
            print(f"  -> Error: {e}")

    print("\n=== Finished ===")

if __name__ == "__main__":
    main()

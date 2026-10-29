import os
import requests
import json
from datetime import datetime, timedelta, timezone

# Secrets from GitHub
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USER_ACCESS_TOKEN = os.getenv("X_USER_ACCESS_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

AI_ENDPOINT = "https://inference.dahl.global/v1/chat/completions"
MODEL = "MiniMaxAI/MiniMax-M2.7"

KEYWORDS = '"Natron theory" OR geopolymer OR "artificial stone"'

def search_recent():
    """Search for recent tweets matching the keywords."""
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
    requests.post(url, headers=headers, json=payload)

def main():
    tweets = search_recent()
    for t in tweets:
        print("Found:", t["text"][:80])
        reply_text = call_ai(t["text"])
        if reply_text:
            reply(t["id"], reply_text)
            print("Replied")

if __name__ == "__main__":
    main()

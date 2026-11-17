import os
from pathlib import Path
from datetime import date
import requests
import json

# Configuration
API_KEY = os.environ.get("DAHL_API_KEY") # We keep the secret name so you don't have to change GitHub secrets
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

ROOT = Path.cwd()
SOCIAL = ROOT / "social-posts"
WEEKLY = SOCIAL / "weekly"
DAILY = SOCIAL / "daily"

WEEKLY.mkdir(parents=True, exist_ok=True)
DAILY.mkdir(parents=True, exist_ok=True)

def load_knowledge():
    files = [
        "brand-profile.md",
        "martinstrayd.md",
        "suzukimusic.md",
        "songarchive.md",
        "social-manager-prompt.md"
    ]
    
    content = []
    for f in files:
        path = ROOT / f
        if path.exists():
            content.append(path.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"Missing required knowledge file: {f}")
            
    return "\n\n".join(content)

def generate_calendar(knowledge):
    prompt = f"""You are STRAYD Social Media Content Director.
Use ONLY the supplied knowledge. Never invent facts.
Generate a complete Monday-Sunday content calendar.

Each day MUST contain:
## Monday (or Tuesday, etc.)
### X
### Facebook
### YouTube Community
### TikTok
### Instagram
### Image Prompt
### Short Video Idea

SUPPLIED KNOWLEDGE:
{knowledge}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Use only supplied STRAYD knowledge."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 8000
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"Sending request to Groq using model {MODEL}...")
    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        raise RuntimeError(f"Groq API failed with fucking status {response.status_code}: {response.text}")
        
    data = response.json()
    return data["choices"][0]["message"]["content"]

def main():
    if not API_KEY:
        raise EnvironmentError("API key environment variable is missing!")
        
    knowledge = load_knowledge()
    content = generate_calendar(knowledge)
    
    week_str = date.today().isoformat()
    weekly_file = WEEKLY / f"{week_str}-calendar.md"
    weekly_file.write_text(content, encoding="utf-8")
    print(f"Created weekly calendar: {weekly_file.name}")

if __name__ == "__main__":
    main()

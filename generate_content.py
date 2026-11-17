import os
import time
from pathlib import Path
from datetime import date
from google import genai
from google.genai.errors import ServerError

API_KEY = os.environ.get("DAHL_API_KEY")
MODEL = "gemini-3.8-flash"

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
## Monday
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

    client = genai.Client(api_key=API_KEY)
    
    # Retry loop to handle 503 high-demand spikes automatically
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Sending request to Gemini using model {MODEL} (Attempt {attempt}/{max_attempts})...")
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )
            return response.text
        except ServerError as e:
            if attempt == max_attempts:
                raise
            print(f"Server busy (503), waiting 15 seconds before retry...")
            time.sleep(15)

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

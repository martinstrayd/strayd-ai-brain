import os
import time
import random
from pathlib import Path
from datetime import date, timedelta
from google import genai
from google.genai.errors import ServerError

API_KEY = os.environ.get("DAHL_API_KEY")
# Try primary model, with a fallback list if overloaded
MODELS = ["gemini-3.8-flash", "gemini-2.5-flash"]

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

Each day MUST contain headings exactly like this:
## Monday
### X
### Facebook
### YouTube Community
### TikTok
### Instagram
### Image Prompt
### Short Video Idea

(Repeat for Tuesday through Sunday)

SUPPLIED KNOWLEDGE:
{knowledge}
"""

    client = genai.Client(api_key=API_KEY)
    
    # Try through models with heavy retry backoff
    for model_name in MODELS:
        max_attempts = 6
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"Sending request using model {model_name} (Attempt {attempt}/{max_attempts})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                print(f"Successfully generated content using {model_name}!")
                return response.text
            except ServerError as e:
                if attempt == max_attempts:
                    print(f"Model {model_name} exhausted all attempts. Trying next model if available...")
                    break
                
                # Exponential backoff with jitter: 10s, 20s, 40s, 60s, 60s + random jitter
                sleep_time = min(60, (2 ** attempt) * 5) + random.uniform(1, 5)
                print(f"Server busy (503), retrying in {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                
    raise RuntimeError("All models and retry attempts failed due to persistent server capacity issues.")

def split_daily_files(weekly_file_path, week_start_date):
    content = weekly_file_path.read_text(encoding="utf-8")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    lines = content.splitlines()
    
    for i, day in enumerate(days):
        lower = day.lower()
        pdate = week_start_date + timedelta(days=i)
        
        start_idx = -1
        end_idx = len(lines)
        
        for idx, line in enumerate(lines):
            if line.startswith(f"## {day}"):
                start_idx = idx
                break
                
        if start_idx == -1:
            continue
            
        if i < 6:
            next_day = days[i+1]
            for idx in range(start_idx + 1, len(lines)):
                if lines[idx].startswith(f"## {next_day}"):
                    end_idx = idx
                    break
        
        day_content = "\n".join(lines[start_idx:end_idx])
        daily_file = DAILY / f"{pdate}-{lower}.md"
        daily_file.write_text(day_content, encoding="utf-8")
        print(f"Created daily file: {daily_file.name}")

def main():
    if not API_KEY:
        raise EnvironmentError("API key environment variable is missing!")
        
    knowledge = load_knowledge()
    content = generate_calendar(knowledge)
    
    today = date.today()
    weekly_file = WEEKLY / f"{today}-calendar.md"
    weekly_file.write_text(content, encoding="utf-8")
    print(f"Created weekly calendar: {weekly_file.name}")
    
    split_daily_files(weekly_file, today)

if __name__ == "__main__":
    main()

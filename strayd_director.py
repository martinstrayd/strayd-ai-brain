import os
import time
import random
from pathlib import Path
from datetime import date, timedelta
from openai import OpenAI

# Read the Groq API key from the secret you just set
API_KEY = os.environ.get("AI_API_KEY") or os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

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

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=API_KEY
    )
    
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Generating calendar with Groq ({MODEL}) (Attempt {attempt}/{max_attempts})...")
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            print("Successfully generated content!")
            return response.choices[0].message.content
        except Exception as e:
            if attempt == max_attempts:
                raise
            sleep_time = (2 ** attempt) * 3 + random.uniform(1, 3)
            print(f"Error encountered, retrying in {sleep_time:.1f}s: {e}")
            time.sleep(sleep_time)

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
        print(f"Saved daily file: {daily_file.name}")

def main():
    if not API_KEY:
        raise EnvironmentError("No API key found in AI_API_KEY environment variable!")
        
    knowledge = load_knowledge()
    content = generate_calendar(knowledge)
    
    today = date.today()
    weekly_file = WEEKLY / f"{today}-calendar.md"
    weekly_file.write_text(content, encoding="utf-8")
    print(f"Saved weekly calendar: {weekly_file.name}")
    
    split_daily_files(weekly_file, today)

if __name__ == "__main__":
    main()

import json, os, re, subprocess, time
from pathlib import Path
from datetime import date, timedelta

DAHL_API_KEY = os.environ.get("DAHL_API_KEY", "")
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
FIELDS = ["x_post","facebook_post","instagram_post","tiktok_post","youtube_community_post","image_prompt","short_video_idea"]

def parse(text):
    text = re.sub(r"^```json\s*", "", text.strip(), flags=re.I)
    text = re.sub(r"```\s*$", "", text)
    try: return json.loads(text)
    except:
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s: return json.loads(text[s:e+1])
        raise

def valid(data):
    if "days" not in data or len(data["days"]) != 7: raise ValueError("bad days")
    for i, d in enumerate(data["days"]):
        if d.get("day") != DAYS[i]: raise ValueError(f"wrong day {i}")
        for f in FIELDS:
            if not isinstance(d.get(f), str) or not d[f].strip(): raise ValueError(f"missing {f}")
    return data

profile = Path("brand-profile.md").read_text()
messages = [{"role":"system","content":"You are the STRAYD Content Director. Focus on Martin Strayd and STRAYD band. Never invent facts. Return valid JSON."},{"role":"user","content":f"BRAND PROFILE:\n\n{profile}\n\nSTRAYD = Martin Strayd + Suzuki. 55 songs, new single weekly. World Tour 2027.\n\nCreate 7-day calendar. JSON with days array, 7 objects. Fields: day, x_post, facebook_post, instagram_post, tiktok_post, youtube_community_post, image_prompt, short_video_idea.\nDays: Monday to Sunday.\nX: 280 chars. FB: paragraphs. IG: 150-300 chars + hashtags. TikTok: hook + script.\nThemes: Weekly Song Journey, Creativity After 50, Independent Music, NATRON THEORY, How To Rock, Creative Persistence, STRAYD Updates.\nReturn JSON only."}]

req = {"model":"MiniMaxAI/MiniMax-M2.7","messages":messages,"temperature":0.7}
r = subprocess.run(["curl","-s","--fail-with-body","--max-time","180","https://inference.dahl.global/v1/chat/completions","-H","Authorization: Bearer "+DAHL_API_KEY,"-H","Content-Type: application/json","-d",json.dumps(req)], capture_output=True, text=True)
raw = json.loads(r.stdout)["choices"][0]["message"]["content"]

try:
    data = valid(parse(raw))
except:
    req["temperature"] = 0
    req["messages"] = [{"role":"system","content":"Return valid JSON. 7 days, fields: day,x_post,facebook_post,instagram_post,tiktok_post,youtube_community_post,image_prompt,short_video_idea."},{"role":"user","content":"Fix JSON:\n"+raw}]
    r = subprocess.run(["curl","-s","--fail-with-body","--max-time","180","https://inference.dahl.global/v1/chat/completions","-H","Authorization: Bearer "+DAHL_API_KEY,"-H","Content-Type: application/json","-d",json.dumps(req)], capture_output=True, text=True)
    data = valid(parse(json.loads(r.stdout)["choices"][0]["message"]["content"]))

today = date.today()
monday = today - timedelta(days=today.weekday())
root = Path("social-posts")
for d in ("weekly","daily","approved","published"): (root/d).mkdir(parents=True, exist_ok=True)

for i, day in enumerate(data["days"]):
    pd = monday + timedelta(days=i)
    slug = day["day"].lower()
    lines = [f"# {day['day']} — {pd.strftime('%d %B %Y')}","","**STRAYD CONTENT DIRECTOR**","",f"**Date:** {pd.isoformat()}","**Status:** DRAFT","","---",""]
    for f in FIELDS:
        lines += [f"## {f.replace('_',' ').title()}","",day[f].strip(),"","---",""]
    (root/"daily"/f"{pd.isoformat()}-{slug}.md").write_text("\n".join(lines))

weekly = ["# STRAYD Weekly Calendar","",f"**Week of:** {monday.strftime('%d %B %Y')}","**Status:** DRAFT","","---",""]
for i, day in enumerate(data["days"]):
    pd = monday + timedelta(days=i)
    weekly += [f"## {day['day']} — {pd.strftime('%d %B %Y')}","","---",""]
    for f in FIELDS:
        weekly += [f"### {f.replace('_',' ').title()}","",day[f].strip(),"","---",""]
(root/"weekly"/f"{monday.isoformat()}-calendar.md").write_text("\n".join(weekly))
(root/"README.md").write_text("# STRAYD Content Library\n\nMartin Strayd + STRAYD. 55 songs, new single weekly. World Tour 2027.\n")
print("Done")

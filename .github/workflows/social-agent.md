
name: Strayd Content Director

on:
  workflow_dispatch:
  schedule:
    # Mondays at 00:00 UTC = 07:00 Thailand time
    - cron: "0 0 * * 1"

permissions:
  contents: write

concurrency:
  group: strayd-content-director-${{ github.ref }}
  cancel-in-progress: false

jobs:
  content-director:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Check configuration
        shell: bash
        env:
          DAHL_API_KEY: ${{ secrets.DAHL_API_KEY }}
        run: |
          set -euo pipefail

          if [ ! -s brand-profile.md ]; then
            echo "ERROR: brand-profile.md is missing or empty."
            exit 1
          fi

          if [ -z "${DAHL_API_KEY:-}" ]; then
            echo "ERROR: DAHL_API_KEY secret is missing."
            exit 1
          fi

      - name: Generate calendar with Dahl and MiniMax
        shell: bash
        env:
          DAHL_API_KEY: ${{ secrets.DAHL_API_KEY }}
        run: |
          set -euo pipefail

          jq -n --rawfile profile brand-profile.md '
            {
              model: "MiniMaxAI/MiniMax-M2.7",
              messages: [
                {
                  role: "system",
                  content: "You are the STRAYD Content Director. Use only facts supported by the supplied brand profile. Never invent songs, releases, dates, history, achievements, products, URLs or claims. Return valid JSON only, without Markdown fences."
                },
                {
                  role: "user",
                  content: (
                    "BRAND PROFILE:\n\n" + $profile +
                    "\n\nCreate a complete Monday-to-Sunday social content calendar." +
                    "\nReturn one JSON object containing a days array of exactly seven objects." +
                    "\nEach object must contain these string fields: day, x_post, facebook_post, youtube_community_post, image_prompt, short_video_idea." +
                    "\nDay names must be Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, in that order." +
                    "\nWrite actual draft text for X, Facebook and YouTube Community. Also provide an image prompt and a practical short-video idea for each day." +
                    "\nRotate thoughtfully between Weekly Song Journey, Fantasy7, Creativity After 50, Independent Music, NATRON THEORY, How To Rock, Cool Hot Sauce and Creative Persistence where supported by the profile." +
                    "\nUse strayd.com when appropriate. Do not invent URLs or unsupported facts." +
                    "\nUse engaging hooks and relevant calls to action. Avoid generic filler." +
                    "\nReturn JSON with this structure: {\"days\":[{\"day\":\"Monday\",\"x_post\":\"...\",\"facebook_post\":\"...\",\"youtube_community_post\":\"...\",\"image_prompt\":\"...\",\"short_video_idea\":\"...\"}]}"
                  )
                }
              ],
              temperature: 0.7
            }
          ' > request.json

          echo "Calling Dahl inference API..."

          curl --fail-with-body --silent --show-error \
            --retry 2 --retry-delay 2 \
            --connect-timeout 20 --max-time 180 \
            https://inference.dahl.global/v1/chat/completions \
            -H "Authorization: Bearer ${DAHL_API_KEY}" \
            -H "Content-Type: application/json" \
            --data-binary @request.json \
            -o response.json

          jq -er '.choices[0].message.content | strings' \
            response.json > generated-raw.txt

      - name: Validate AI response
        shell: bash
        run: |
          set -euo pipefail

          python3 <<'PY'
          import json
          import re
          from pathlib import Path

          raw = Path("generated-raw.txt").read_text(encoding="utf-8").strip()

          # Remove optional Markdown code fences.
          raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
          raw = re.sub(r"\s*```\s*$", "", raw)

          try:
              data = json.loads(raw)
          except json.JSONDecodeError:
              # Also tolerate explanatory text surrounding one JSON object.
              start = raw.find("{")
              end = raw.rfind("}")
              if start < 0 or end <= start:
                  raise SystemExit("ERROR: No valid JSON object in AI response.")
              try:
                  data = json.loads(raw[start:end + 1])
              except json.JSONDecodeError as exc:
                  raise SystemExit(f"ERROR: Invalid AI JSON: {exc}")

          expected_days = [
              "Monday", "Tuesday", "Wednesday", "Thursday",
              "Friday", "Saturday", "Sunday"
          ]
          fields = [
              "x_post", "facebook_post", "youtube_community_post",
              "image_prompt", "short_video_idea"
          ]

          if not isinstance(data, dict) or not isinstance(data.get("days"), list):
              raise SystemExit("ERROR: Response must contain a days array.")

          if len(data["days"]) != 7:
              raise SystemExit("ERROR: Expected exactly seven days.")

          for index, day in enumerate(data["days"]):
              if not isinstance(day, dict) or day.get("day") != expected_days[index]:
                  raise SystemExit(f"ERROR: Incorrect day at position {index + 1}.")
              for field in fields:
                  value = day.get(field)
                  if not isinstance(value, str) or not value.strip():
                      raise SystemExit(
                          f"ERROR: Missing or empty {field} for {expected_days[index]}."
                      )

          Path("generated.json").write_text(
              json.dumps(data, ensure_ascii=False, indent=2) + "\n",
              encoding="utf-8"
          )
          print("Validated seven days and all five content types.")
          PY

      - name: Create unique weekly and daily files
        shell: bash
        env:
          RUN_ID: ${{ github.run_id }}
          RUN_ATTEMPT: ${{ github.run_attempt }}
        run: |
          set -euo pipefail

          python3 <<'PY'
          import json
          import os
          from datetime import date, timedelta
          from pathlib import Path

          data = json.loads(Path("generated.json").read_text(encoding="utf-8"))

          today = date.today()
          week_start = today - timedelta(days=today.weekday())
          run_id = os.environ["RUN_ID"]
          attempt = os.environ["RUN_ATTEMPT"]

          weekly_dir = Path("social-posts/weekly")
          daily_dir = Path("social-posts/daily")
          approved_dir = Path("social-posts/approved")
          published_dir = Path("social-posts/published")

          for folder in (weekly_dir, daily_dir, approved_dir, published_dir):
              folder.mkdir(parents=True, exist_ok=True)

          fields = [
              ("X POST", "x_post"),
              ("FACEBOOK POST", "facebook_post"),
              ("YOUTUBE COMMUNITY POST", "youtube_community_post"),
              ("IMAGE GENERATION PROMPT", "image_prompt"),
              ("SHORT VIDEO IDEA", "short_video_idea"),
          ]

          def section(title, content):
              return f"## {title}\n\n{content.strip()}\n"

          calendar = [
              "# STRAYD Weekly Content Calendar",
              "",
              f"- Week starting: {week_start.isoformat()} (UTC)",
              f"- Generation run: {run_id}, attempt {attempt}",
              "- Status: DRAFT — review before publishing",
              "",
          ]

          for index, day in enumerate(data["days"]):
              post_date = week_start + timedelta(days=index)
              slug = day["day"].lower()
              daily_file = daily_dir / (
                  f"{post_date.isoformat()}-{slug}-run-{run_id}-attempt-{attempt}.txt"
              )

              parts = [
                  "STRAYD CONTENT DIRECTOR",
                  f"Date: {post_date.isoformat()} (UTC)",
                  f"Day: {day['day']}",
                  f"Generation run: {run_id}, attempt {attempt}",
                  "Status: DRAFT — NOT APPROVED FOR PUBLISHING",
                  "",
              ]

              for title, key in fields:
                  parts.extend([title, "=" * len(title), day[key].strip(), ""])

              # Exclusive creation: never overwrite an existing file.
              with daily_file.open("x", encoding="utf-8") as handle:
                  handle.write("\n".join(parts) + "\n")

              calendar.extend([f"## {day['day']}", ""])
              for title, key in fields:
                  calendar.extend([section(title, day[key]), ""])

              print(f"Created {daily_file}")

          weekly_file = weekly_dir / (
              f"{week_start.isoformat()}-calendar-run-{run_id}-attempt-{attempt}.md"
          )
          with weekly_file.open("x", encoding="utf-8") as handle:
              handle.write("\n".join(calendar) + "\n")

          print(f"Created {weekly_file}")

          readme = Path("social-posts/README.md")
          readme.write_text(
              "# STRAYD Social Content Library\n\n"
              "Generated by the Strayd Content Director GitHub Action.\n\n"
              "## Folders\n\n"
              "- `weekly/`: weekly Markdown calendars.\n"
              "- `daily/`: individual TXT files containing five content types.\n"
              "- `approved/`: reserved for explicitly approved content.\n"
              "- `published/`: reserved for confirmed publishing records.\n\n"
              "## Important\n\n"
              "Generated content is draft material. It is not automatically "
              "approved or published. Unique run IDs prevent later runs from "
              "overwriting earlier generated files.\n",
              encoding="utf-8"
          )

          (approved_dir / "README.md").write_text(
              "# Approved Posts\n\nReserved for content explicitly approved for publishing.\n",
              encoding="utf-8"
          )
          (published_dir / "README.md").write_text(
              "# Published Records\n\nReserved for confirmed publishing records.\n",
              encoding="utf-8"
          )
          PY

      - name: Commit generated files
        shell: bash
        env:
          TARGET_BRANCH: ${{ github.ref_name }}
        run: |
          set -euo pipefail

          git config user.name "github-actions[bot]"
          git config user.email \
            "41898282+github-actions[bot]@users.noreply.github.com"

          git add social-posts/

          if git diff --cached --quiet; then
            echo "No changes to commit."
            exit 0
          fi

          git commit -m "Generate STRAYD social content run $GITHUB_RUN_ID"

          git push origin "HEAD:${TARGET_BRANCH}"

          echo "Generated files committed to ${TARGET_BRANCH}."

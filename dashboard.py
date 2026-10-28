import streamlit as st
import requests
import json
from pathlib import Path
from github import Github

st.set_page_config(page_title="STRAYD Content Director", page_icon="🎵", layout="wide")

st.title("🎵 STRAYD Content Director Dashboard")
st.caption("Visual Approval Deck & Content Editor")

# Initialize GitHub API connection safely
try:
    github_token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    dahl_key = st.secrets.get("DAHL_API_KEY", "")
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
except Exception as e:
    st.warning("⚠️ GitHub / Dahl API secrets not detected in Streamlit settings. Running in Preview Mode.")
    st.info("To enable live commits and regeneration, add GITHUB_TOKEN, REPO_NAME, and DAHL_API_KEY to Streamlit Secrets.")
    repo = None

# Scan weekly calendar drafts
posts_dir = Path("social-posts/weekly")

if not posts_dir.exists() or not list(posts_dir.glob("*.md")):
    st.info("No generated calendars found in `social-posts/weekly/`.")
else:
    files = sorted(list(posts_dir.glob("*.md")), reverse=True)
    selected_file = st.sidebar.selectbox("Select Calendar Week", files, format_func=lambda x: x.name)

    if selected_file:
        file_path = str(selected_file)
        content = selected_file.read_text(encoding="utf-8")
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"**Selected File:** `{selected_file.name}`")

        # Editable Text Area
        edited_content = st.text_area("📄 Draft Content Editor", value=content, height=450)

        st.markdown("---")
        c1, c2, c3 = st.columns(3)

        # 1. REGENERATE PROMPTS BUTTON
        with c1:
            if st.button("🔄 Regenerate Visual Prompts", use_container_width=True):
                if not dahl_key:
                    st.error("Missing DAHL_API_KEY in Streamlit secrets.")
                else:
                    with st.spinner("Asking Dahl / MiniMax for fresh prompts..."):
                        try:
                            payload = {
                                "model": "MiniMaxAI/MiniMax-M2.7",
                                "messages": [
                                    {"role": "system", "content": "You are the STRAYD Visual Director."},
                                    {"role": "user", "content": f"Generate 3 fresh, high-impact image prompts for STRAYD music brand based on this content:\n\n{edited_content[:500]}"}
                                ]
                            }
                            res = requests.post(
                                "https://inference.dahl.global/v1/chat/completions",
                                headers={"Authorization": f"Bearer {dahl_key}", "Content-Type": "application/json"},
                                json=payload,
                                timeout=30
                            )
                            if res.status_code == 200:
                                new_prompts = res.json()["choices"][0]["message"]["content"]
                                st.success("Fresh Prompts Generated!")
                                st.markdown("### 🖼️ New Suggested Image Prompts:")
                                st.info(new_prompts)
                            else:
                                st.error(f"Dahl API Error: {res.status_code}")
                        except Exception as err:
                            st.error(f"Failed to connect to Dahl API: {err}")

        # 2. SAVE EDITS BUTTON
        with c2:
            if st.button("💾 Save Edits to GitHub", use_container_width=True):
                if not repo:
                    st.error("GitHub credentials not configured.")
                else:
                    try:
                        gh_file = repo.get_contents(file_path)
                        repo.update_file(
                            path=file_path,
                            message=f"Update content via Streamlit Dashboard: {selected_file.name}",
                            content=edited_content,
                            sha=gh_file.sha
                        )
                        st.success("Changes saved successfully to GitHub!")
                    except Exception as err:
                        st.error(f"Error saving to GitHub: {err}")

        # 3. APPROVE BUTTON
        with c3:
            if st.button("✅ APPROVE & MOVE TO QUEUE", type="primary", use_container_width=True):
                if not repo:
                    st.error("GitHub credentials not configured.")
                else:
                    try:
                        target_path = f"social-posts/approved/{selected_file.name}"
                        gh_file = repo.get_contents(file_path)
                        
                        # Save to approved folder in GitHub repo
                        repo.create_file(
                            path=target_path,
                            message=f"Approve content: {selected_file.name}",
                            content=edited_content
                        )
                        st.balloons()
                        st.success(f"Approved! Content moved to `social-posts/approved/{selected_file.name}`.")
                    except Exception as err:
                        st.error(f"Approval error: {err}")

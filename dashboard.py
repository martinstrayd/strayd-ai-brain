import streamlit as st
import github
import os

st.set_page_config(page_title="STRAYD Content Director", page_icon="🎵", layout="wide")

st.title("🎵 STRAYD Content Director Dashboard")
st.subheader("Post-Generation Review & Visual Approval Hub")

# Mock layout matching wireframe
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📱 Social Copy")
    st.text_area("X Post (280 chars)", "55 tracks deep. The journey continues...", height=100)
    st.text_area("Facebook Post", "Here is why rock after 50 is different...", height=150)

with col2:
    st.markdown("### 🖼️ Visual & Video Assets")
    st.info("Image Prompt: Cyberpunk neon guitar stage under red lights...")
    st.button("🔄 Regenerate Image Prompt")
    st.markdown("---")
    st.info("Short Video Hook: You won't guess how this track was written...")

st.markdown("---")

btn1, btn2, btn3 = st.columns(3)

with btn1:
    if st.button("✏️ Edit Content", use_container_width=True):
        st.toast("Editing mode enabled")

with btn2:
    if st.button("❌ Reject Draft", type="secondary", use_container_width=True):
        st.error("Draft Rejected")

with btn3:
    if st.button("✅ APPROVE & SCHEDULE", type="primary", use_container_width=True):
        st.success("Approved! Sent to Publishing Queue.")

"""
DevPulse Studio - Enterprise AI Autonomous Software Architect Engine
Main Streamlit Application Dashboard Interface
"""

import streamlit as st
import time
import google.generativeai as genai
from config import config, logger

# -----------------------------------------------------------------------------
# Global API Patching: Strictly Force 'gemini-2.5-flash' for ALL Calls
# -----------------------------------------------------------------------------
_original_GenerativeModel = genai.GenerativeModel

def _patched_GenerativeModel(model_name, *args, **kwargs):
    # Pro اور پرانے 1.5 تمام ماڈلز کو زبردستی Flash پر موڑ دیں تاکہ 429 Quota Error نہ آئے
    forced_model = "gemini-2.5-flash"
    return _original_GenerativeModel(forced_model, *args, **kwargs)

# Google API کے انیشلائزیشن کو گلوبلی پیچ کر دیا گیا ہے
genai.GenerativeModel = _patched_GenerativeModel

from core import GitHubManager, AIArchitect, AICoder, AIReviewer

def apply_active_model_override(instance, chosen_model):
    try:
        if hasattr(instance, "model_name"):
            instance.model_name = "gemini-2.5-flash"
        if hasattr(instance, "model"):
            instance.model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        pass
    return instance

def init_agent(agent_cls, api_key, model_name):
    agent = None
    try:
        agent = agent_cls(api_key=api_key, model_name="gemini-2.5-flash")
    except TypeError:
        try:
            agent = agent_cls(api_key=api_key)
        except TypeError:
            agent = agent_cls()
    
    return apply_active_model_override(agent, "gemini-2.5-flash")

# -----------------------------------------------------------------------------
# 1. Page Configuration & Layout
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DevPulse Studio - Autonomous Software Architect",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Sidebar Setup & Key Verification
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/512/code.png", width=80)
    st.title("DevPulse Studio")
    st.caption("v1.0.0 Enterprise Autonomous Engine")
    st.markdown("---")

    st.subheader("🔑 Security Credentials")
    
    user_gemini_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.get("gemini_key", config.gemini_api_key),
        type="password",
        help="Google AI Studio سے اپنی Gemini API Key درج کریں"
    )
    
    user_github_token = st.text_input(
        "GitHub Access Token",
        value=st.session_state.get("github_token", config.github_token),
        type="password",
        help="GitHub Personal Access Token درج کریں"
    )

    st.session_state["gemini_key"] = user_gemini_key
    st.session_state["github_token"] = user_github_token

    st.markdown("---")
    st.subheader("⚙️ System Configuration")
    
    st.info("⚡ **Active Engine:** `gemini-2.5-flash` (Optimized for Free Quota Limits)")
    is_private_repo = st.checkbox("Private GitHub Repository", value=False)

# -----------------------------------------------------------------------------
# 3. Main Dashboard Header
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🚀 DevPulse Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous Software Architect & Production-Ready Code Generator</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. Input Controls & Project Specs
# -----------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    project_name = st.text_input(
        "📦 Repository Name",
        placeholder="e.g., nexusvault-platform"
    )

with col2:
    target_framework = st.selectbox(
        "🎯 Core Tech Ecosystem",
        ["Auto-Detect / Best Fit", "Python (Streamlit / FastAPI)", "Node.js (Express / React)", "Full-Stack Web (HTML/CSS/JS/Backend)"]
    )

project_requirements = st.text_area(
    "📋 Project Architecture & Functional Requirements",
    height=180,
    placeholder="اپنے پروجیکٹ کی تفصیل درج کریں..."
)

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("🔥 Generate & Deploy Entire Architecture to GitHub", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# 5. Core Execution Logic
# -----------------------------------------------------------------------------
if generate_btn:
    if not user_gemini_key or not user_github_token:
        st.error("⚠️ برائے مہربانی سائڈ بار میں اپنی Gemini API Key اور GitHub Token درج کریں!")
        st.stop()
        
    if not project_name or not project_requirements:
        st.warning("⚠️ برائے مہربانی پروجیکٹ کا نام اور ریکوائرمنٹس دونوں درج کریں۔")
        st.stop()

    st.markdown("---")
    st.subheader("⚙️ Real-time Execution Pipeline")
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # API Key کو صاف ستھرا کر کے انیشلائز کریں
        clean_key = user_gemini_key.strip()
        genai.configure(api_key=clean_key)

        # Step 1: Initialize Core Agents
        status_text.text("🤖 DevPulse Core Agents انیشلائز کیے جا رہے ہیں...")
        github_mgr = GitHubManager(access_token=user_github_token.strip())
        
        architect = init_agent(AIArchitect, clean_key, "gemini-2.5-flash")
        coder = init_agent(AICoder, clean_key, "gemini-2.5-flash")
        reviewer = init_agent(AIReviewer, clean_key, "gemini-2.5-flash")
        
        progress_bar.progress(10)

        # Step 2: GitHub Repository Creation
        status_text.text(f"🐙 GitHub Repository '{project_name}' تیار کی جا رہی ہے...")
        repo = github_mgr.create_repository(
            repo_name=project_name,
            description=f"DevPulse Studio AI: {project_requirements[:100]}...",
            private=is_private_repo
        )
        progress_bar.progress(25)
        st.success(f"✅ GitHub Repo تیار ہو گئی: [{repo.html_url}]({repo.html_url})")

        # Step 3: Architecture Blueprint Planning
        status_text.text("🧠 AI Architect پروجیکٹ کا فائل اسٹرکچر اور ڈیزائن پلان کر رہا ہے...")
        full_requirements = f"Tech Ecosystem Preference: {target_framework}\nRequirements: {project_requirements}"
        
        apply_active_model_override(architect, "gemini-2.5-flash")
        plan = architect.plan_project(project_name=project_name, requirements=full_requirements)
        
        progress_bar.progress(40)

        st.subheader("📐 Engineered Architecture Blueprint")
        st.info(f"**Architecture Style:** {plan.get('architecture_style', 'N/A')}\n\n**Summary:** {plan.get('summary', '')}")
        
        files = plan.get("files", [])
        st.markdown(f"**کل جنریٹ ہونے والی فائلز:** `{len(files)}`")

        # Step 4: Code Generation & Push Loop with Safe Delay
        status_text.text("💻 Deep Coding Agent تمام فائلز کا مکمل کوڈ بنا کر GitHub پر Push کر رہا ہے...")
        
        total_files = len(files)
        files_list_names = [f.get("path") for f in files]
        file_progress_container = st.container()

        for idx, file_info in enumerate(files):
            file_path = file_info.get("path")
            file_purpose = file_info.get("purpose")
            
            status_text.text(f"🛠️ [فائل {idx+1}/{total_files}] کوڈ کی جا رہی ہے: `{file_path}`")
            
            # Rate limit سے بچنے کے لیے 3 سیکنڈز کا وقفہ
            time.sleep(3)

            apply_active_model_override(coder, "gemini-2.5-flash")
            code_content = coder.generate_file_code(
                project_name=project_name,
                file_path=file_path,
                purpose=file_purpose,
                architecture_summary=plan.get("summary", ""),
                all_files_list=files_list_names
            )
            
            github_mgr.push_file_to_repo(
                repo_name=project_name,
                file_path=file_path,
                content=code_content,
                commit_message=f"DevPulse: Implemented operational logic for {file_path}"
            )

            current_pct = 40 + int(((idx + 1) / total_files) * 45)
            progress_bar.progress(current_pct)
            
            with file_progress_container:
                st.caption(f"✔ Completed & Pushed: `{file_path}`")

        progress_bar.progress(90)

        # Step 5: Executive Code Audit & Review
        status_text.text("🛡️ AI Reviewer پروجیکٹ کا سیکیورٹی اور آرکیٹیکچر آڈٹ کر رہا ہے...")
        time.sleep(3)
        
        apply_active_model_override(reviewer, "gemini-2.5-flash")
        audit_report = reviewer.audit_project(
            project_name=project_name,
            requirements=project_requirements,
            project_plan=plan,
            repo_url=repo.html_url
        )

        progress_bar.progress(100)
        status_text.text("🎉 تمام مرحلے کامیابی سے مکمل ہو گئے!")

        # -----------------------------------------------------------------------------
        # 6. Final Results
        # -----------------------------------------------------------------------------
        st.balloons()
        st.success("🎉 **مبارک ہو! آپ کا پروجیکٹ 100% مکمل اور GitHub پر لائیو ہو چکا ہے۔**")
        st.markdown(f"### 🔗 Access Your Code Repository: [{repo.html_url}]({repo.html_url})")

        st.markdown("---")
        st.subheader("🛡️ Enterprise Quality & Security Audit Report")
        st.markdown(audit_report)

    except Exception as err:
        progress_bar.progress(0)
        status_text.empty()
        st.error(f"❌ پروجیکٹ جنریشن کے عمل میں مسئلہ پیش آیا: {str(err)}")
        logger.exception(err)

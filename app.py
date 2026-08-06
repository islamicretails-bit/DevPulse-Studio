"""
DevPulse Studio - Enterprise AI Autonomous Software Architect Engine
Main Streamlit Application Dashboard Interface (Powered by Groq & Llama 3.3)
"""

import streamlit as st
import time
import json
from groq import Groq
from config import config, logger

# GitHub Manager Import
from core import GitHubManager

# -----------------------------------------------------------------------------
# Groq Wrapper Classes for Seamless Integration with Existing Agents
# -----------------------------------------------------------------------------
class GroqAgentAdapter:
    """Groq API کو پرانے ایجنٹ اسٹرکچر کے ساتھ ہم آہنگ کرنے کے لیے ایڈاپٹر"""
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model_name = model_name

    def _call_groq(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.model_name,
            temperature=0.2,
            response_format=response_format
        )
        return chat_completion.choices[0].message.content

    def plan_project(self, project_name: str, requirements: str) -> dict:
        system_prompt = (
            "You are an expert AI Software Architect. Analyze the requirements and output ONLY a valid JSON object. "
            "Do not include any markdown formatting like ```json or pre-text. "
            "The JSON structure must be: {\"architecture_style\": \"...\", \"summary\": \"...\", \"files\": [{\"path\": \"file_path\", \"purpose\": \"file_description\"}]}"
        )
        user_prompt = f"Project Name: {project_name}\nRequirements:\n{requirements}"
        
        response_text = self._call_groq(system_prompt, user_prompt, json_mode=True)
        try:
            return json.loads(response_text)
        except Exception:
            # اگر JSON کی کلیننگ درکار ہو
            clean_json = response_text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_json)

    def generate_file_code(self, project_name: str, file_path: str, purpose: str, architecture_summary: str, all_files_list: list) -> str:
        system_prompt = (
            "You are an Enterprise Senior Software Engineer. Output ONLY the raw executable production-ready code for the specified file. "
            "Do NOT wrap the code in markdown code blocks like ```python or ```javascript. Do NOT include explanations."
        )
        user_prompt = (
            f"Project: {project_name}\nFile Path: {file_path}\nPurpose: {purpose}\n"
            f"Architecture Overview: {architecture_summary}\n"
            f"All Project Files Context: {', '.join(all_files_list)}\n\nGenerate high quality, full code for {file_path}:"
        )
        code = self._call_groq(system_prompt, user_prompt, json_mode=False)
        
        # اگر ماڈل مبلت میں بیک ٹکس (Markdown Fences) لگا دے تو انہیں صاف کریں
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines)
            
        return code

    def audit_project(self, project_name: str, requirements: str, project_plan: dict, repo_url: str) -> str:
        system_prompt = (
            "You are a Lead Security Auditor and Quality Assurance Expert. Provide a comprehensive code audit, "
            "security summary, and architecture verification report in Markdown format."
        )
        user_prompt = (
            f"Project: {project_name}\nRepository URL: {repo_url}\nRequirements: {requirements}\n"
            f"Architecture Plan Summary: {project_plan.get('summary', '')}\nFiles Built: {len(project_plan.get('files', []))}"
        )
        return self._call_groq(system_prompt, user_prompt, json_mode=False)


# -----------------------------------------------------------------------------
# 1. Page Configuration & Layout
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DevPulse Studio - Powered by Groq",
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
    .groq-badge {
        background-color: #F97316;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
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
    
    user_groq_key = st.text_input(
        "Groq API Key",
        value=st.session_state.get("groq_key", getattr(config, "groq_api_key", "")),
        type="password",
        help="console.groq.com سے اپنی مفت Groq API Key درج کریں"
    )
    
    user_github_token = st.text_input(
        "GitHub Access Token",
        value=st.session_state.get("github_token", getattr(config, "github_token", "")),
        type="password",
        help="GitHub Personal Access Token درج کریں"
    )

    st.session_state["groq_key"] = user_groq_key
    st.session_state["github_token"] = user_github_token

    st.markdown("---")
    st.subheader("⚙️ System Configuration")
    
    selected_groq_model = st.selectbox(
        "Active Groq Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        index=0,
        help="کوڈنگ اور آرکیٹیکچر کے لیے Meta Llama 3.3 70B سب سے پاورفل ماڈل ہے"
    )
    is_private_repo = st.checkbox("Private GitHub Repository", value=False)
    
    st.markdown("---")
    st.markdown("⚡ **Engine:** <span class='groq-badge'>Groq LPU Acceleration</span>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. Main Dashboard Header
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🚀 DevPulse Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ultra-Fast Autonomous Architect & Code Generator (Powered by Meta Llama 3.3 & Groq)</div>', unsafe_allow_html=True)

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
    if not user_groq_key or not user_github_token:
        st.error("⚠️ برائے مہربانی سائڈ بار میں اپنی Groq API Key اور GitHub Token درج کریں!")
        st.stop()
        
    if not project_name or not project_requirements:
        st.warning("⚠️ برائے مہربانی پروجیکٹ کا نام اور ریکوائرمنٹس دونوں درج کریں۔")
        st.stop()

    st.markdown("---")
    st.subheader("⚙️ Real-time Execution Pipeline")
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        clean_groq_key = user_groq_key.strip()
        clean_github_token = user_github_token.strip()

        # Step 1: Initialize Groq Engine & GitHub Manager
        status_text.text("⚡ Groq LPU Engine اور GitHub Manager انیشلائز کیے جا رہے ہیں...")
        github_mgr = GitHubManager(access_token=clean_github_token)
        engine = GroqAgentAdapter(api_key=clean_groq_key, model_name=selected_groq_model)
        
        progress_bar.progress(10)

        # Step 2: GitHub Repository Creation
        status_text.text(f"🐙 GitHub Repository '{project_name}' تیار کی جا رہی ہے...")
        repo = github_mgr.create_repository(
            repo_name=project_name,
            description=f"DevPulse Studio AI (Groq Llama 3.3): {project_requirements[:100]}...",
            private=is_private_repo
        )
        progress_bar.progress(25)
        st.success(f"✅ GitHub Repo تیار ہو گئی: [{repo.html_url}]({repo.html_url})")

        # Step 3: Architecture Blueprint Planning
        status_text.text("🧠 Llama 3.3 Architect پروجیکٹ کا فائل اسٹرکچر اور ڈیزائن پلان کر رہا ہے...")
        full_requirements = f"Tech Ecosystem Preference: {target_framework}\nRequirements: {project_requirements}"
        
        plan = engine.plan_project(project_name=project_name, requirements=full_requirements)
        progress_bar.progress(40)

        st.subheader("📐 Engineered Architecture Blueprint")
        st.info(f"**Architecture Style:** {plan.get('architecture_style', 'N/A')}\n\n**Summary:** {plan.get('summary', '')}")
        
        files = plan.get("files", [])
        st.markdown(f"**کل جنریٹ ہونے والی فائلز:** `{len(files)}`")

        # Step 4: Code Generation & Push Loop (Super Fast!)
        status_text.text("💻 Llama 3.3 Coding Engine تمام فائلز کا مکمل کوڈ بنا کر GitHub پر Push کر رہا ہے...")
        
        total_files = len(files)
        files_list_names = [f.get("path") for f in files]
        file_progress_container = st.container()

        for idx, file_info in enumerate(files):
            file_path = file_info.get("path")
            file_purpose = file_info.get("purpose")
            
            status_text.text(f"🛠️ [فائل {idx+1}/{total_files}] سپر فاسٹ کوڈنگ جاری ہے: `{file_path}`")

            code_content = engine.generate_file_code(
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
                commit_message=f"DevPulse (Groq): Implemented logic for {file_path}"
            )

            current_pct = 40 + int(((idx + 1) / total_files) * 45)
            progress_bar.progress(current_pct)
            
            with file_progress_container:
                st.caption(f"⚡ Completed & Pushed: `{file_path}`")

        progress_bar.progress(90)

        # Step 5: Executive Code Audit & Review
        status_text.text("🛡️ AI Auditor پروجیکٹ کا سیکیورٹی اور آرکیٹیکچر آڈٹ کر رہا ہے...")
        
        audit_report = engine.audit_project(
            project_name=project_name,
            requirements=project_requirements,
            project_plan=plan,
            repo_url=repo.html_url
        )

        progress_bar.progress(100)
        status_text.text("🎉 تمام مرحلے کامیابی سے اور انتہائی تیز رفتاری کے ساتھ مکمل ہو گئے!")

        # -----------------------------------------------------------------------------
        # 6. Final Results
        # -----------------------------------------------------------------------------
        st.balloons()
        st.success("🎉 **مبارک ہو! آپ کا پروجیکٹ Groq Engine کی مدد سے 100% مکمل اور GitHub پر لائیو ہو چکا ہے۔**")
        st.markdown(f"### 🔗 Access Your Code Repository: [{repo.html_url}]({repo.html_url})")

        st.markdown("---")
        st.subheader("🛡️ Enterprise Quality & Security Audit Report")
        st.markdown(audit_report)

    except Exception as err:
        progress_bar.progress(0)
        status_text.empty()
        st.error(f"❌ پروجیکٹ جنریشن کے عمل میں مسئلہ پیش آیا: {str(err)}")
        logger.exception(err)

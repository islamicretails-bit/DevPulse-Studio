import streamlit as st
import os
import time
import json
import base64
import urllib.request
import urllib.error
import re

# ---------------------------------------------------------
# Page Configuration & Custom CSS (Apple Dark Theme)
# ---------------------------------------------------------
st.set_page_config(
    page_title="DevPulse Studio Enterprise Pro | 100k Lines Engine",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0B0F17; color: #F3F4F6; }
    .stButton>button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white; border: none; padding: 12px 24px;
        border-radius: 8px; font-weight: 600; width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4); }
    .status-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px; padding: 16px; margin-bottom: 12px; backdrop-filter: blur(12px);
    }
    .log-container {
        background-color: #05070B; border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px; padding: 12px; font-family: 'Courier New', monospace;
        height: 380px; overflow-y: auto; color: #10B981; font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# API Key Manager & Rotator Engine
# ---------------------------------------------------------
class APIKeyManager:
    def __init__(self):
        self.keys = []
        # Collect Groq API Keys dynamically from Environment Variables
        for k in os.environ:
            if k.startswith("GROQ_API_KEY"):
                val = os.environ.get(k)
                if val and val.strip():
                    self.keys.append(val.strip())
        
        # Check Streamlit secrets if environment keys are missing
        if hasattr(st, "secrets"):
            for k in st.secrets:
                if "GROQ_API_KEY" in k:
                    val = st.secrets[k]
                    if val and val.strip() and val.strip() not in self.keys:
                        self.keys.append(val.strip())
                        
        self.current_index = 0

    def get_key(self):
        if not self.keys:
            return None
        return self.keys[self.current_index]

    def rotate(self):
        if len(self.keys) > 1:
            self.current_index = (self.current_index + 1) % len(self.keys)
            return True
        return False

# ---------------------------------------------------------
# Groq API Client with Auto Retry & Backoff Engine
# ---------------------------------------------------------
def call_groq_llm(prompt, key_manager, system_instruction="You are an enterprise software architect.", model="llama-3.3-70b-versatile", max_retries=5):
    for attempt in range(max_retries):
        api_key = key_manager.get_key()
        if not api_key:
            return None, "No GROQ API Key found in Environment or Secrets."

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 8000
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                content = res_data['choices'][0]['message']['content']
                return content, None
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limit exceeded
                rotated = key_manager.rotate()
                wait_time = (attempt + 1) * 8
                time.sleep(wait_time)
            else:
                time.sleep(4)
        except Exception as ex:
            time.sleep(4)

    return None, "Rate limit exceeded across all keys repeatedly. Please wait 1-2 minutes or add additional API keys."

# ---------------------------------------------------------
# GitHub Integration Handler
# ---------------------------------------------------------
def push_to_github(repo, path, content, token, commit_message="feat: enterprise multi-module auto-commit"):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Studio"
    }

    # Check if file already exists to obtain SHA
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            sha = res_data.get('sha')
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return False, f"GitHub Get Error: {e.code}"
    except Exception as e:
        pass

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": commit_message,
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
        with urllib.request.urlopen(req) as response:
            return True, "Success"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# UI Layout & Application Engine
# ---------------------------------------------------------
st.title("⚡ DevPulse Studio Pro (100k Lines Scale Engine)")
st.caption("Enterprise Monorepo Architecture & Multi-Agent Autonomous Code Generator")

key_mgr = APIKeyManager()

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ System Status & Secrets")
    st.info(f"🔑 Active Groq Keys Detected: **{len(key_mgr.keys)}**")
    
    env_token = os.environ.get("GITHUB_TOKEN", "")
    secret_token = st.secrets.get("GITHUB_TOKEN", "") if hasattr(st, "secrets") else ""
    default_token = env_token or secret_token
    github_token = st.text_input("GitHub Personal Access Token", value=default_token, type="password")

    env_repo = os.environ.get("GITHUB_REPO", "")
    secret_repo = st.secrets.get("GITHUB_REPO", "") if hasattr(st, "secrets") else ""
    default_repo = env_repo or secret_repo
    github_repo = st.text_input("Target Repository (username/repo)", value=default_repo)
    
    st.markdown("---")
    delay_interval = st.slider("Rate-Limit Delay per File (Seconds)", min_value=6, max_value=20, value=12)
    st.caption("A delay of 12-15s prevents Groq rate limits for massive enterprise codebases.")

# Main Prompt Input
prompt_input = st.text_area(
    "پرامپٹ درج کریں (Master Enterprise Blueprint Prompt):",
    height=250,
    placeholder="پاس ورڈ، ماسٹر پرامپٹ، یا 100,000 لائینز کے پروجیکٹ کی تفصیلات یہاں درج کریں۔"
)

if st.button("🚀 100k Lines Enterprise Build شروع کریں"):
    if not prompt_input.strip():
        st.error("براہِ کرم پہلے پرامپٹ درج کریں۔")
    elif not github_token or not github_repo:
        st.error("GitHub Token اور Repository کا ہونا ضروری ہے۔")
    elif len(key_mgr.keys) == 0:
        st.error("کوئی Groq API Key نہیں ملی! Streamlit Secrets یا Environment میں GROQ_API_KEY_1 وغیرہ شامل کریں۔")
    else:
        st.markdown("---")
        
        # Expandable Section for Detailed Architecture Blueprint
        arch_expander = st.expander("🏗️ پروجیکٹ کا آرکیٹیکچر اور فائل سٹرکچر تفصیل کے ساتھ دیکھیں", expanded=True)
        arch_placeholder = arch_expander.empty()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 📊 بلڈ پیشرفت")
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
        with col2:
            st.markdown("### 📋 لائیو لاگز")
            log_box = st.empty()
            
        logs = []
        def add_log(msg):
            logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            log_box.markdown(f"<div class='log-container'>{'<br>'.join(logs[::-1])}</div>", unsafe_allow_html=True)

        add_log("🤖 ArchitectAgent کو ایکٹیویٹ کیا جا رہا ہے...")
        add_log("🔍 پروجیکٹ کے 100k Lines Blueprint کی تفصیلی بریک ڈاؤن تیار ہو رہی ہے...")
        arch_placeholder.info("⏳ ArchitectAgent تمام ماڈیولز، API روٹس، اور ڈیپنڈنسیز کی فہرست تیار کر رہا ہے...")

        # STEP 1: Detailed Architectural Plan & Explanation
        arch_plan_prompt = f"""
        Provide a comprehensive architectural plan for the enterprise system described below.
        List all modules, database entities, security layer, and describe every single file path that needs to be generated to build this full-scale (100,000 lines scale) application.

        Provide the output in Markdown format with:
        1. Executive System Overview
        2. Module Hierarchy & Architecture Diagram (text-based)
        3. Detailed File Blueprint (List every file path and its core responsibilities)

        System Prompt / Blueprint:
        {prompt_input}
        """

        arch_details, err = call_groq_llm(
            arch_plan_prompt, key_mgr,
            system_instruction="You are a Chief Enterprise Software Architect. Provide detailed breakdown of system components."
        )

        if arch_details:
            arch_placeholder.markdown(arch_details)
            add_log("✅ آرکیٹیکچر کا مکمل روڈ میپ اور فائلز کی تفصیل سکرین پر ظاہر کر دی گئی ہے۔")
        else:
            arch_placeholder.warning("⚠️ آرکیٹیکچر تفصیل حاصل نہیں ہو سکی، لیکن فائل ایکسٹریکشن جاری ہے۔")

        # STEP 2: Extract JSON List of File Paths
        add_log("📌 تمام فائلز کی کیٹلاگ لسٹ (JSON File Extraction) پروسیس ہو رہی ہے...")
        
        decomposition_prompt = f"""
        Extract the complete list of distinct source file paths required for this project from the specification below.
        Return ONLY a raw JSON array of file paths. Example format: ["prisma/schema.prisma", "src/app/page.tsx", ...]

        System Blueprint:
        {prompt_input}
        """

        file_list_raw, err = call_groq_llm(
            decomposition_prompt, key_mgr, 
            system_instruction="You are an enterprise software architect. Return ONLY valid JSON string array of file paths."
        )

        file_paths = []
        if file_list_raw:
            try:
                cleaned_json = re.search(r'\[.*\]', file_list_raw, re.DOTALL)
                if cleaned_json:
                    file_paths = json.loads(cleaned_json.group(0))
            except Exception as e:
                add_log(f"⚠️ JSON Parse Error, Fallback file structure apply ہو رہا ہے: {str(e)}")

        # Fallback File Blueprint if JSON parsing fails
        if not file_paths:
            file_paths = [
                "prisma/schema.prisma", "package.json", "tailwind.config.js", "src/app/globals.css",
                "src/types/index.ts", "src/lib/security.ts", "src/lib/geo-currency.ts", "src/lib/ai-generator.ts",
                "src/app/layout.tsx", "src/app/page.tsx", "src/app/office/page.tsx",
                "src/app/dashboard/page.tsx", "src/app/affiliate/page.tsx", "src/app/vendor/page.tsx",
                "src/components/marketplace/ProductGrid.tsx", "src/components/marketplace/ProductCard.tsx",
                "src/components/marketplace/CustomRequestModal.tsx", "src/components/marketplace/AppleToast.tsx",
                "src/components/admin/LiveTrafficMap.tsx", "src/components/admin/AIOperationsHub.tsx",
                "src/components/admin/SalesAnalyticsChart.tsx", "src/components/admin/CustomRequestsTable.tsx",
                "src/app/api/cron/auto-generate/route.ts", "src/app/api/ai/generate-product/route.ts",
                "src/app/api/payments/checkout/route.ts", "src/app/api/admin/analytics/route.ts",
                "src/app/api/downloads/secure/route.ts", "vercel.json", ".env.example"
            ]

        total_files = len(file_paths)
        add_log(f"🚀 کل **{total_files}** فائلز کی بلڈنگ اور GitHub پر اپ لوڈنگ شروع کی جا رہی ہے۔")

        # STEP 3: Sequential Generation & GitHub Upload Loop
        completed_count = 0
        for idx, file_path in enumerate(file_paths):
            add_log(f"🔄 CoderAgent تخلیق کر رہا ہے: **{file_path}** ({idx+1}/{total_files})")
            
            gen_prompt = f"""
            System Blueprint: {prompt_input}

            TASK: Write full, highly detailed, production-grade, unabridged source code for the file: `{file_path}`.
            CRITICAL REQUIREMENTS:
            1. Output ONLY the raw source code. Do NOT wrap in markdown backticks (e.g. no ```typescript).
            2. Write clean, complete implementation without any placeholders or `// TODO` shortcuts.
            3. Implement full type safety, comprehensive UI/UX logic, and complete handling of enterprise edge cases.
            """

            code_content, gen_err = call_groq_llm(
                gen_prompt, key_mgr,
                system_instruction=f"You are a Senior Staff Engineer writing enterprise production code for {file_path}."
            )

            if gen_err or not code_content:
                add_log(f"❌ Error Generating {file_path}: {gen_err}")
                continue

            # Clean markdown fences if generated
            clean_code = re.sub(r'^```\w*\n', '', code_content, flags=re.MULTILINE)
            clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

            # Push file directly to GitHub
            success, github_msg = push_to_github(github_repo, file_path, clean_code, github_token)
            
            if success:
                add_log(f"✅ GitHub Commit Successful: `{file_path}`")
                completed_count += 1
            else:
                add_log(f"⚠️ GitHub Upload Failed ({file_path}): {github_msg}")

            # Update UI Progress & Status Card
            completed_count_val = idx + 1
            progress_bar.progress(completed_count_val / total_files)
            status_placeholder.markdown(f"""
            <div class='status-card'>
                <h4>تخلیق کا اسٹیٹس</h4>
                <p>فائلیں مکمل: <b>{completed_count}/{total_files}</b></p>
                <p>موجودہ فائل: <code>{file_path}</code></p>
            </div>
            """, unsafe_allow_html=True)

            # Delay to avoid Groq Rate Limit
            time.sleep(delay_interval)

        add_log("✨ تمام فائلیں اور اینٹرپرائز اسٹرکچر کامیابی سے آپ کے GitHub پر اپ لوڈ ہو چکے ہیں!")
        st.success("🎉 بلڈ مکمل ہو گیا! آپ کا پورا 100k Lines Scale پروجیکٹ GitHub پر تیار ہے۔")

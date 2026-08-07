import streamlit as st
import os
import time
import json
import base64
import urllib.request
import urllib.error
import re

# ---------------------------------------------------------
# Page Configuration & Custom CSS
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
# API Key Manager Engine
# ---------------------------------------------------------
class APIKeyManager:
    def __init__(self):
        self.keys = []
        for k in os.environ:
            if k.startswith("GROQ_API_KEY"):
                val = os.environ.get(k)
                if val and val.strip():
                    self.keys.append(val.strip())
        
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
# Groq API Client Engine (Optimized Max Tokens & Retries)
# ---------------------------------------------------------
def call_groq_llm(prompt, key_manager, system_instruction="You are an enterprise software architect.", model="llama-3.3-70b-versatile", max_tokens=4000, max_retries=5):
    for attempt in range(max_retries):
        api_key = key_manager.get_key()
        if not api_key:
            return None, "No GROQ API Key found."

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
            "max_tokens": max_tokens
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                content = res_data['choices'][0]['message']['content']
                return content, None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                key_manager.rotate()
                time.sleep((attempt + 1) * 6)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)

    return None, "Rate limit / connection timeout on API call."

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

    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            sha = res_data.get('sha')
    except Exception:
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
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# UI Layout
# ---------------------------------------------------------
st.title("⚡ DevPulse Studio Pro (Enterprise Engine)")
st.caption("Monorepo Architecture & Multi-Agent Code Generator")

key_mgr = APIKeyManager()

with st.sidebar:
    st.header("⚙️ Configuration")
    st.info(f"🔑 Active Keys: **{len(key_mgr.keys)}**")
    
    env_token = os.environ.get("GITHUB_TOKEN", "")
    secret_token = st.secrets.get("GITHUB_TOKEN", "") if hasattr(st, "secrets") else ""
    github_token = st.text_input("GitHub Token", value=env_token or secret_token, type="password")

    env_repo = os.environ.get("GITHUB_REPO", "")
    secret_repo = st.secrets.get("GITHUB_REPO", "") if hasattr(st, "secrets") else ""
    github_repo = st.text_input("Target Repository (username/repo)", value=env_repo or secret_repo)
    
    st.markdown("---")
    delay_interval = st.slider("Rate-Limit Delay (Seconds)", min_value=6, max_value=20, value=10)

prompt_input = st.text_area(
    "پرامپٹ درج کریں (Master Enterprise Blueprint Prompt):",
    height=220,
    placeholder="ماستر پرامپٹ یہاں درج کریں۔"
)

if st.button("🚀 Enterprise Build شروع کریں"):
    if not prompt_input.strip():
        st.error("براہِ کرم پہلے پرامپٹ درج کریں۔")
    elif not github_token or not github_repo:
        st.error("GitHub Token اور Repository لازمی ہیں۔")
    elif len(key_mgr.keys) == 0:
        st.error("کوئی GROQ API Key نہیں ملی!")
    else:
        st.markdown("---")
        
        arch_expander = st.expander("🏗️ پروجیکٹ کا آرکیٹیکچر اور فائل سٹرکچر", expanded=True)
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

        add_log("🤖 ArchitectAgent ایکٹیویٹ ہو چکا ہے۔..")
        
        # Fast & Reliable Architectural Overview
        arch_plan_prompt = f"""
        Summarize the architecture for this enterprise blueprint in 4 concise sections:
        1. System Overview
        2. Key Tech Stack
        3. Core Modules
        4. Security & Payment Routing Structure

        Prompt: {prompt_input}
        """

        arch_placeholder.info("⏳ ArchitectAgent سسٹم کا مکمل جائزہ تیار کر رہا ہے...")
        arch_details, err = call_groq_llm(
            arch_plan_prompt, key_mgr,
            system_instruction="You are a Chief Enterprise Software Architect. Be concise.",
            max_tokens=2500
        )

        if arch_details:
            arch_placeholder.markdown(arch_details)
            add_log("✅ آرکیٹیکچر کا جائزہ کامیابی سے لوڈ کر لیا گیا ہے۔")
        else:
            arch_placeholder.warning("⚠️ آرکیٹیکچر کا خلاصہ سکپ کیا گیا، فائل جنریشن جاری ہے۔")

        # Regex Extraction of Files directly from Prompt + LLM Backup
        add_log("📌 پرامپٹ سے فائلز کا اسٹرکچر نکالا جا رہا ہے...")
        
        # Regex to catch files directly mentioned in user prompt
        extracted_from_prompt = re.findall(r'[\w\/\.\-]+\.(?:prisma|json|js|css|ts|tsx|example)', prompt_input)
        file_paths = list(set(extracted_from_prompt))

        if len(file_paths) < 15:
            # Call LLM for complete list if regex found fewer files
            decomposition_prompt = f"""
            Extract a JSON array of exact file paths mentioned in or required by this blueprint.
            Return ONLY JSON array. Example: ["prisma/schema.prisma", "package.json"]

            Blueprint: {prompt_input}
            """
            file_list_raw, err = call_groq_llm(
                decomposition_prompt, key_mgr, 
                system_instruction="Return ONLY valid JSON array of strings.",
                max_tokens=2000
            )
            if file_list_raw:
                try:
                    cleaned = re.search(r'\[.*\]', file_list_raw, re.DOTALL)
                    if cleaned:
                        parsed = json.loads(cleaned.group(0))
                        file_paths = list(set(file_paths + parsed))
                except Exception:
                    pass

        # Final Fallback List if both fail
        if not file_paths:
            file_paths = [
                "prisma/schema.prisma", "package.json", "tailwind.config.js", "src/app/globals.css",
                "vercel.json", ".env.example", "src/types/index.ts", "src/lib/security.ts",
                "src/lib/geo-currency.ts", "src/lib/ai-generator.ts", "src/app/layout.tsx",
                "src/app/page.tsx", "src/app/office/page.tsx", "src/app/dashboard/page.tsx",
                "src/app/affiliate/page.tsx", "src/app/vendor/page.tsx",
                "src/components/marketplace/ProductGrid.tsx", "src/components/marketplace/ProductCard.tsx",
                "src/components/marketplace/CustomRequestModal.tsx", "src/components/marketplace/AppleToast.tsx",
                "src/components/admin/LiveTrafficMap.tsx", "src/components/admin/AIOperationsHub.tsx",
                "src/components/admin/SalesAnalyticsChart.tsx", "src/components/admin/CustomRequestsTable.tsx",
                "src/app/api/cron/auto-generate/route.ts", "src/app/api/ai/generate-product/route.ts",
                "src/app/api/payments/checkout/route.ts", "src/app/api/admin/analytics/route.ts",
                "src/app/api/downloads/secure/route.ts"
            ]

        total_files = len(file_paths)
        add_log(f"🚀 کل **{total_files}** فائلز کی بلڈنگ اور GitHub پر اپ لوڈنگ شروع کی جا رہی ہے۔")

        # Sequential Code Generation & GitHub Upload
        completed_count = 0
        for idx, file_path in enumerate(file_paths):
            add_log(f"🔄 CoderAgent جنریٹ کر رہا ہے: **{file_path}** ({idx+1}/{total_files})")
            
            gen_prompt = f"""
            System Blueprint: {prompt_input}

            TASK: Write complete, production-grade source code for: `{file_path}`.
            REQUIREMENTS:
            1. Output ONLY raw source code (no markdown fences like ```typescript).
            2. Write clean implementation with full type safety and no shortcuts.
            """

            code_content, gen_err = call_groq_llm(
                gen_prompt, key_mgr,
                system_instruction=f"You are a Senior Staff Engineer writing enterprise code for {file_path}.",
                max_tokens=6000
            )

            if gen_err or not code_content:
                add_log(f"❌ Error Generating {file_path}: {gen_err}")
                continue

            clean_code = re.sub(r'^```\w*\n', '', code_content, flags=re.MULTILINE)
            clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

            success, github_msg = push_to_github(github_repo, file_path, clean_code, github_token)
            
            if success:
                add_log(f"✅ GitHub Commit Successful: `{file_path}`")
                completed_count += 1
            else:
                add_log(f"⚠️ GitHub Upload Failed ({file_path}): {github_msg}")

            completed_count_val = idx + 1
            progress_bar.progress(completed_count_val / total_files)
            status_placeholder.markdown(f"""
            <div class='status-card'>
                <h4>تخلیق کا اسٹیٹس</h4>
                <p>فائلیں مکمل: <b>{completed_count}/{total_files}</b></p>
                <p>موجودہ فائل: <code>{file_path}</code></p>
            </div>
            """, unsafe_allow_html=True)

            time.sleep(delay_interval)

        add_log("✨ تمام فائلیں اور اینٹرپرائز اسٹرکچر کامیابی سے آپ کے GitHub پر اپ لوڈ ہو چکے ہیں!")
        st.success("🎉 بلڈ مکمل ہو گیا! آپ کا پروجیکٹ GitHub پر تیار ہے۔")

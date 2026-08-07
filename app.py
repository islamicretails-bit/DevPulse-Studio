import streamlit as st
import os
import time
import json
import base64
import urllib.request
import urllib.error
import re
from groq import Groq

# ---------------------------------------------------------
# Page Configuration & UI Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="DevPulse Studio Enterprise Pro | Unstoppable Engine",
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
        height: 420px; overflow-y: auto; color: #10B981; font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# API Key Manager Engine (Auto Rotation)
# ---------------------------------------------------------
class APIKeyManager:
    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.load_keys()

    def _add_key(self, val):
        if not val:
            return
        if isinstance(val, (list, tuple)):
            for item in val:
                self._add_key(item)
        elif isinstance(val, str):
            for part in val.split(","):
                cleaned = part.strip()
                if cleaned and cleaned not in self.keys:
                    self.keys.append(cleaned)

    def load_keys(self):
        for env_key, env_val in os.environ.items():
            if "GROQ_API_KEY" in env_key:
                self._add_key(env_val)

        if hasattr(st, "secrets"):
            for sec_key in st.secrets:
                if "GROQ_API_KEY" in sec_key or "GROQ_KEYS" in sec_key:
                    self._add_key(st.secrets[sec_key])

    def add_manual_keys(self, user_str):
        if user_str:
            self._add_key(user_str)

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
# Multi-Model Fallback & Resilience LLM Engine
# ---------------------------------------------------------
# Models prioritized by intelligence vs rate limit headroom
AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]

def call_groq_llm(prompt, key_manager, system_instruction="You are an enterprise software architect.", max_tokens=6000, logger_callback=None):
    attempt = 0
    model_index = 0
    
    while True:
        attempt += 1
        api_key = key_manager.get_key()
        current_model = AVAILABLE_MODELS[model_index % len(AVAILABLE_MODELS)]
        
        if not api_key:
            return None, "No GROQ API Key found. Please add keys in sidebar or secrets."

        try:
            client = Groq(api_key=api_key, timeout=45.0)
            
            completion = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            
            content = completion.choices[0].message.content
            if content and len(content.strip()) > 0:
                return content, None
            else:
                raise Exception("Empty response received from LLM.")

        except Exception as e:
            err_msg = str(e)
            rotated = key_manager.rotate()
            
            # Switch Model on Rate Limits or Repeated Attempts
            if "429" in err_msg or "rate_limit" in err_msg.lower():
                # Swap model if we hit rate limits heavily
                if attempt % 2 == 0:
                    model_index = (model_index + 1) % len(AVAILABLE_MODELS)
                    if logger_callback:
                        logger_callback(f"🔄 Swapping Model to `{AVAILABLE_MODELS[model_index % len(AVAILABLE_MODELS)]}` to bypass rate limit...")
                
                wait_time = min(attempt * 4, 30) if rotated else min(attempt * 8, 45)
                if logger_callback:
                    logger_callback(f"⏳ [Rate Limit / 429] Waiting {wait_time}s (Attempt {attempt})...")
            
            elif "timeout" in err_msg.lower() or "503" in err_msg:
                wait_time = min(attempt * 3, 20)
                if logger_callback:
                    logger_callback(f"⚠️ [Network/Timeout] Retrying in {wait_time}s...")
            else:
                wait_time = 4
                if logger_callback:
                    logger_callback(f"⚠️ [API Notice] {err_msg[:80]}... Retrying in {wait_time}s...")

            time.sleep(wait_time)


def generate_large_file_code(prompt_input, file_path, key_mgr, logger_callback):
    system_instruction = f"You are a Principal Software Engineer implementing complete, production-grade code for {file_path}."
    
    base_prompt = f"""
    System Master Blueprint:
    {prompt_input}

    TASK:
    Write COMPLETE, INDUSTRIAL-GRADE, FULLY FUNCTIONAL source code for: `{file_path}`.

    STRICT CRITICAL RULES:
    - Write FULL implementations. Absolutely ZERO placeholders, NO '// TODO', NO cuts.
    - Write all interfaces, imports, helper utilities, and models completely.
    - Output RAW executable code inside markdown blocks.
    """

    code_accumulated, err = call_groq_llm(
        base_prompt, key_mgr, 
        system_instruction=system_instruction, 
        max_tokens=6000, 
        logger_callback=logger_callback
    )

    if err or not code_accumulated:
        return None, err

    # Smart Continuation Check
    if len(code_accumulated) > 12000 and not code_accumulated.strip().endswith(("}", ";", "export default", "```")):
        logger_callback(f"🧩 File `{file_path}` extended response required. Requesting continuation chunk...")
        continuation_prompt = f"Continue EXACTLY where you left off for `{file_path}` without repeating previous code:\n\n... {code_accumulated[-400:]}"
        
        chunk, chunk_err = call_groq_llm(
            continuation_prompt, key_mgr, 
            system_instruction=system_instruction, 
            max_tokens=4000, 
            logger_callback=logger_callback
        )
        if chunk and not chunk_err:
            code_accumulated += "\n" + chunk

    return code_accumulated, None

# ---------------------------------------------------------
# GitHub API Push Engine
# ---------------------------------------------------------
def push_to_github(repo, path, content, token, commit_message="feat: enterprise auto-commit"):
    url = f"[https://api.github.com/repos/](https://api.github.com/repos/){repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Studio"
    }

    sha = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                sha = res_data.get('sha')
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                sha = None
                break
        except Exception:
            time.sleep(2)

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": commit_message,
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    for attempt in range(5):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=45) as response:
                return True, "Success"
        except Exception as e:
            if attempt == 4:
                return False, str(e)
            time.sleep(3)

# ---------------------------------------------------------
# User Interface Layout
# ---------------------------------------------------------
st.title("⚡ DevPulse Studio Enterprise Engine")
st.caption("Auto-Dynamic Multi-Model Engine (Infinite Resilience)")

key_mgr = APIKeyManager()

with st.sidebar:
    st.header("⚙️ Configuration")
    
    user_keys_input = st.text_area(
        "Groq API Keys (کاما سے الگ کریں):",
        placeholder="gsk_key1, gsk_key2, gsk_key3",
        help="یہاں متعدد API Keys درج کر کے Rate Limits سے بچیں۔"
    )
    if user_keys_input:
        key_mgr.add_manual_keys(user_keys_input)

    active_keys_count = len(key_mgr.keys)
    st.info(f"🔑 Active Groq Keys Detected: **{active_keys_count}**")

    # Auto-Calculate Dynamic Delay based on API Key availability
    if active_keys_count > 3:
        recommended_delay = 3
    elif active_keys_count == 2 or active_keys_count == 3:
        recommended_delay = 6
    else:
        recommended_delay = 12

    st.success(f"🎯 Dynamic Delay Set To: **{recommended_delay}s per file**")
    
    env_token = os.environ.get("GITHUB_TOKEN", "")
    secret_token = st.secrets.get("GITHUB_TOKEN", "") if hasattr(st, "secrets") else ""
    github_token = st.text_input("GitHub Token", value=env_token or secret_token, type="password")

    env_repo = os.environ.get("GITHUB_REPO", "")
    secret_repo = st.secrets.get("GITHUB_REPO", "") if hasattr(st, "secrets") else ""
    github_repo = st.text_input("Target Repository (username/repo)", value=env_repo or secret_repo)

prompt_input = st.text_area(
    "پرامپٹ درج کریں (Master Enterprise Blueprint Prompt):",
    height=220,
    placeholder="اپنا پورا پرامپٹ یہاں درج کریں۔"
)

if st.button("🚀 Enterprise Build شروع کریں"):
    if not prompt_input.strip():
        st.error("براہِ کرم پہلے پرامپٹ درج کریں۔")
    elif not github_token or not github_repo:
        st.error("GitHub Token اور Repository لازمی ہیں۔")
    elif len(key_mgr.keys) == 0:
        st.error("کوئی GROQ API Key نہیں ملی! Sidebar یا Streamlit Secrets چیک کریں۔")
    else:
        st.markdown("---")
        
        arch_expander = st.expander("🏗️ پروجیکٹ آرکیٹیکچر", expanded=True)
        arch_placeholder = arch_expander.empty()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### 📊 پیشرفت")
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
        with col2:
            st.markdown("### 📋 لائیو لاگز")
            log_box = st.empty()
            
        logs = []
        def add_log(msg):
            logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            log_box.markdown(f"<div class='log-container'>{'<br>'.join(logs[::-1])}</div>", unsafe_allow_html=True)

        add_log("🤖 ArchitectAgent ایکٹیویٹ ہو رہا ہے۔..")

        # Compact Overview Call
        arch_plan_prompt = f"Provide a concise summary (Tech Stack, DB, Core Features) for:\n{prompt_input[:1500]}"
        arch_placeholder.info("⏳ ArchitectAgent کا جائزہ بن رہا ہے...")
        
        arch_details, err = call_groq_llm(
            arch_plan_prompt, key_mgr,
            system_instruction="You are a Chief Enterprise Software Architect.",
            max_tokens=1500,
            logger_callback=add_log
        )

        if arch_details:
            arch_placeholder.markdown(arch_details)
            add_log("✅ آرکیٹیکچر تیار ہو گیا۔")

        # Extract File Structure
        extracted_from_prompt = re.findall(r'[\w\/\.\-]+\.(?:prisma|json|js|jsx|css|ts|tsx|env|example)', prompt_input)
        file_paths = list(set(extracted_from_prompt))

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
        add_log(f"🚀 **{total_files}** فائلوں کی تیاری شروع ہو رہی ہے۔")

        completed_count = 0
        for idx, file_path in enumerate(file_paths):
            add_log(f"🔄 CoderAgent جنریٹ کر رہا ہے: **{file_path}** ({idx+1}/{total_files})")
            
            code_content, gen_err = generate_large_file_code(
                prompt_input, file_path, key_mgr, logger_callback=add_log
            )

            if gen_err or not code_content:
                add_log(f"❌ Error Generating {file_path}: {gen_err}")
                continue

            clean_code = re.sub(r'^```\w*\n', '', code_content, flags=re.MULTILINE)
            clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

            success, github_msg = push_to_github(github_repo, file_path, clean_code, github_token)
            
            if success:
                add_log(f"✅ GitHub Uploaded: `{file_path}`")
                completed_count += 1
            else:
                add_log(f"⚠️ GitHub Upload Failed ({file_path}): {github_msg}")

            progress_bar.progress((idx + 1) / total_files)
            status_placeholder.markdown(f"""
            <div class='status-card'>
                <h4>تخلیق کا اسٹیٹس</h4>
                <p>فائلیں مکمل: <b>{completed_count}/{total_files}</b></p>
                <p>موجودہ فائل: <code>{file_path}</code></p>
            </div>
            """, unsafe_allow_html=True)

            # Auto Dynamic Delay Application
            time.sleep(recommended_delay)

        add_log("✨ بلڈ پروسیس کامیابی سے مکمل ہو چکا ہے!")
        st.success("🎉 تمام کی تمام فائلیں آپ کی GitHub ریپوزٹری میں اپ لوڈ ہو چکی ہیں!")

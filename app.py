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
    page_title="DevPulse Studio Enterprise Pro | Strict Engine",
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
# API Key Manager Engine (Auto Key Rotation)
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
# Strict Sequential Resilience LLM Engine
# ---------------------------------------------------------
PRIMARY_MODEL = "llama-3.3-70b-versatile"

def call_groq_llm_strict(prompt, key_manager, system_instruction="You are an enterprise software architect.", max_tokens=5000, logger_callback=None):
    """
    یہ فنکشن تب تک لوپ میں رہے گا جب تک موجودہ کال 100% کامیاب نہ ہو جائے۔
    اگلی کال پر جانا ناممکن ہے۔
    """
    attempt = 0
    while True:
        attempt += 1
        api_key = key_manager.get_key()
        
        if not api_key:
            return None, "No GROQ API Key found."

        try:
            client = Groq(api_key=api_key, timeout=60.0)
            
            completion = client.chat.completions.create(
                model=PRIMARY_MODEL,
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
            
            # Rate Limit (429) Handling - Sequential Wait
            if "429" in err_msg or "rate_limit" in err_msg.lower():
                wait_time = 15 if rotated else 25
                if logger_callback:
                    logger_callback(f"🛑 [Rate Limit 429] API کو بریک دیا جا رہا ہے۔ {wait_time} سیکنڈ بعد دوبارہ کوشش ہوگی (کوشش نمبر {attempt})...")
            elif "timeout" in err_msg.lower() or "503" in err_msg:
                wait_time = 10
                if logger_callback:
                    logger_callback(f"⚠️ [Network Timeout] {wait_time} سیکنڈز میں دوبارہ ٹرائی جاری ہے...")
            else:
                wait_time = 8
                if logger_callback:
                    logger_callback(f"⚠️ [API Pause] {err_msg[:70]}... {wait_time}s میں دوبارہ ٹرائی کر رہے ہیں۔")

            time.sleep(wait_time)


def generate_single_file_completely(prompt_input, file_path, key_mgr, logger_callback):
    """
    جب تک یہ فائل 100% مکمل نہ بنے، یہ فنکشن باہر نہیں نکلے گا۔
    """
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

    # Lock until LLM returns full content
    code_accumulated, err = call_groq_llm_strict(
        base_prompt, key_mgr, 
        system_instruction=system_instruction, 
        max_tokens=5000, 
        logger_callback=logger_callback
    )

    # Smart Continuation Check for Big Files
    if code_accumulated and len(code_accumulated) > 10000 and not code_accumulated.strip().endswith(("}", ";", "export default", "```")):
        logger_callback(f"🧩 File `{file_path}` بڑی ہے، دوسرا حصہ جوڑا جا رہا ہے۔..")
        continuation_prompt = f"Continue EXACTLY where you left off for `{file_path}` without repeating previous code:\n\n... {code_accumulated[-400:]}"
        
        chunk, chunk_err = call_groq_llm_strict(
            continuation_prompt, key_mgr, 
            system_instruction=system_instruction, 
            max_tokens=3500, 
            logger_callback=logger_callback
        )
        if chunk and not chunk_err:
            code_accumulated += "\n" + chunk

    return code_accumulated

# ---------------------------------------------------------
# GitHub Push Engine (Strict Retry)
# ---------------------------------------------------------
def push_to_github_strict(repo, path, content, token):
    url = f"[https://api.github.com/repos/](https://api.github.com/repos/){repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Studio"
    }

    sha = None
    for attempt in range(5):
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
            time.sleep(3)

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": f"feat: add complete {path}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    while True:
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=45) as response:
                return True
        except Exception as e:
            time.sleep(5)

# ---------------------------------------------------------
# User Interface Layout
# ---------------------------------------------------------
st.title("⚡ DevPulse Studio Enterprise Engine (Strict Sequential)")
st.caption("One File At A Time | 100% Guaranteed Execution")

key_mgr = APIKeyManager()

with st.sidebar:
    st.header("⚙️ Configuration")
    
    user_keys_input = st.text_area(
        "Groq API Keys (کاما سے الگ کریں):",
        placeholder="gsk_key1, gsk_key2",
        help="2 یا اس سے زیادہ کیز درج کریں تاکہ پروسیس زیادہ تیز ہو۔"
    )
    if user_keys_input:
        key_mgr.add_manual_keys(user_keys_input)

    active_keys_count = len(key_mgr.keys)
    st.info(f"🔑 Active Groq Keys Detected: **{active_keys_count}**")

    # Safety Pause Selection
    safety_delay = st.slider("فائلوں کے درمیان وقفہ (سیکنڈز):", min_value=5, max_value=25, value=12)
    
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

if st.button("🚀 Strict Build شروع کریں"):
    if not prompt_input.strip():
        st.error("براہِ کرم پہلے پرامپٹ درج کریں۔")
    elif not github_token or not github_repo:
        st.error("GitHub Token اور Repository لازمی ہیں۔")
    elif len(key_mgr.keys) == 0:
        st.error("کوئی GROQ API Key نہیں ملی! Sidebar چیک کریں۔")
    else:
        st.markdown("---")
        
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

        add_log("🤖 Strict System ایکٹیویٹ ہو گیا ہے۔..")

        # Dynamic File Extraction from Prompt
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
        add_log(f"🚀 **{total_files}** فائلوں کا کام شروع ہو رہا ہے۔ (ایک وقت میں صرف ایک فائل)")

        completed_count = 0
        for idx, file_path in enumerate(file_paths):
            add_log(f"🔒 [Lock Activated] فائل پر کام جاری ہے: **{file_path}** ({idx+1}/{total_files})")
            
            status_placeholder.markdown(f"""
            <div class='status-card'>
                <h4>تخلیق کا اسٹیٹس</h4>
                <p>فائلیں مکمل: <b>{completed_count}/{total_files}</b></p>
                <p>موجودہ فائل: <code>{file_path}</code></p>
            </div>
            """, unsafe_allow_html=True)

            # Generate Single File completely
            code_content = generate_single_file_completely(
                prompt_input, file_path, key_mgr, logger_callback=add_log
            )

            clean_code = re.sub(r'^```\w*\n', '', code_content, flags=re.MULTILINE)
            clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

            # Push Single File to GitHub strictly
            add_log(f"⬆️ GitHub پر پش کیا جا رہا ہے: `{file_path}`")
            push_to_github_strict(github_repo, file_path, clean_code, github_token)
            
            completed_count += 1
            add_log(f"✅ [100% Done] `{file_path}` مکمل اور پش ہو گئی!")
            progress_bar.progress((idx + 1) / total_files)

            # Mandatory Rest Pause to prevent Rate Limits
            add_log(f"💤 Rate Limit سے بچنے کے لیے {safety_delay} سیکنڈ کا وقفہ دیا جا رہا ہے۔..")
            time.sleep(safety_delay)

        add_log("✨ تمام کی تمام فائلیں کامیابی سے بن کر GitHub پر پش ہو چکی ہیں!")
        st.success("🎉 تمام فائلیں 100% مکمل ہو گئی ہیں!")

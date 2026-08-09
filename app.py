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
# UI Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="DevPulse Enterprise Mega Engine v4.0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #070A0F; color: #F3F4F6; }
    .stButton>button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white; border: none; padding: 14px 28px;
        border-radius: 8px; font-weight: 700; width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(37, 99, 235, 0.4); }
    .status-card {
        background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px; padding: 18px; margin-bottom: 15px; backdrop-filter: blur(16px);
    }
    .log-container {
        background-color: #030508; border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px; padding: 14px; font-family: 'Courier New', monospace;
        height: 400px; overflow-y: auto; color: #10B981; font-size: 13px; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Robust Multi-Key Manager Engine
# ---------------------------------------------------------
class MultiKeyManager:
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
            return self.current_index
        return 0

# ---------------------------------------------------------
# Infinite Resilient LLM Call Core
# ---------------------------------------------------------
MODEL_NAME = "llama-3.3-70b-versatile"

def call_groq_ultra_safe(prompt, key_manager, system_instruction="You are an enterprise software architect.", max_tokens=6000):
    attempt = 0
    while True:
        attempt += 1
        api_key = key_manager.get_key()
        
        if not api_key:
            return None, "No GROQ API Key provided!"

        try:
            client = Groq(api_key=api_key, timeout=90.0)
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            
            content = completion.choices[0].message.content
            if content and len(content.strip()) > 0:
                # Rotate key after every successful call to distribute load evenly
                key_manager.rotate()
                return content, None
            else:
                raise Exception("LLM provided blank response.")

        except Exception as e:
            err_msg = str(e)
            next_idx = key_manager.rotate()
            
            # Smart Delay handling for Rate Limits
            if "429" in err_msg or "rate_limit" in err_msg.lower():
                wait_time = 45 + (attempt * 5)
                st.warning(f"🛑 Rate Limit (429) Triggered! Swapped to Key #{next_idx + 1}. Pausing for {wait_time} seconds (Attempt {attempt})...")
            else:
                wait_time = 15
                st.warning(f"⚠️ API Temporary Delay: {err_msg[:80]}... Auto Retrying in {wait_time}s...")

            time.sleep(wait_time)


def build_large_file_content(prompt_input, file_path, key_mgr):
    system_instruction = f"You are a Senior Principal Software Architect generating full production source code for: {file_path}"
    
    base_prompt = f"""
    System Blueprint Prompt:
    {prompt_input}

    TASK:
    Write COMPLETE, INDUSTRIAL-GRADE, FULLY FUNCTIONAL source code for file: `{file_path}`.

    CRITICAL INSTRUCTIONS:
    - Write complete, compilable implementations. Absolutely ZERO placeholders, NO '// TODO', NO cuts.
    - Write all type interfaces, dependencies, data models, and logic completely.
    - Output ONLY raw executable code wrapped inside standard markdown codeblocks.
    """

    code_accumulated, err = call_groq_ultra_safe(
        base_prompt, key_mgr, 
        system_instruction=system_instruction, 
        max_tokens=6000
    )

    # Automatic continuation check for massive files
    if code_accumulated and len(code_accumulated) > 12000 and not code_accumulated.strip().endswith(("}", ";", "export default", "```")):
        continuation_prompt = f"Continue EXACTLY where you left off for `{file_path}` without repeating previous code:\n\n... {code_accumulated[-500:]}"
        chunk, chunk_err = call_groq_ultra_safe(
            continuation_prompt, key_mgr, 
            system_instruction=system_instruction, 
            max_tokens=4000
        )
        if chunk and not chunk_err:
            code_accumulated += "\n" + chunk

    return code_accumulated

# ---------------------------------------------------------
# GitHub Push Engine with Guaranteed Retries
# ---------------------------------------------------------
def push_file_to_github_safe(repo, path, content, token):
    url = f"[https://api.github.com/repos/](https://api.github.com/repos/){repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Mega-Engine"
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
        "message": f"feat(auto): generate complete {path}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    while True:
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=60) as response:
                return True
        except Exception as e:
            time.sleep(6)

# ---------------------------------------------------------
# Streamlit Session State & Interface Configuration
# ---------------------------------------------------------
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0
if "file_queue" not in st.session_state:
    st.session_state.file_queue = []
if "logs" not in st.session_state:
    st.session_state.logs = []

st.title("🛡️ DevPulse Enterprise Mega Engine (100+ Files Capacity)")
st.caption("Infinite Resilient Loop | Auto-Key Cycler | Strict File Lock")

key_mgr = MultiKeyManager()

with st.sidebar:
    st.header("⚙️ Core Configuration")
    user_keys_input = st.text_area(
        "Groq API Keys (4 کیز کاما سے الگ کر کے درج کریں):",
        placeholder="gsk_key1, gsk_key2, gsk_key3, gsk_key4",
        help="4 API کیز شامل کرنے سے Rate Limit کا مسئلہ 90% کم ہو جاتا ہے۔"
    )
    if user_keys_input:
        key_mgr.add_manual_keys(user_keys_input)

    st.info(f"🔑 Detected Active API Keys: **{len(key_mgr.keys)}**")

    # Dynamic delay based on total keys
    safety_delay = st.slider("فائلوں کے درمیان کول ڈاؤن (سیکنڈز):", min_value=5, max_value=30, value=12)
    
    env_token = os.environ.get("GITHUB_TOKEN", "")
    secret_token = st.secrets.get("GITHUB_TOKEN", "") if hasattr(st, "secrets") else ""
    github_token = st.text_input("GitHub Personal Access Token", value=env_token or secret_token, type="password")

    env_repo = os.environ.get("GITHUB_REPO", "")
    secret_repo = st.secrets.get("GITHUB_REPO", "") if hasattr(st, "secrets") else ""
    github_repo = st.text_input("GitHub Target Repo (username/repository)", value=env_repo or secret_repo)

prompt_input = st.text_area(
    "اپنا Blueprint / Manifest Prompt درج کریں:",
    height=220,
    placeholder="یہاں اپنا 100+ فائلوں کا مکمل پرامپٹ پیسٹ کریں۔..."
)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🚀 Heavy Master Build شروع کریں", disabled=st.session_state.is_running):
        if not prompt_input.strip():
            st.error("پرامپٹ درج کرنا لازمی ہے۔")
        elif not github_token or not github_repo:
            st.error("GitHub Credentials لازمی ہیں۔")
        elif len(key_mgr.keys) == 0:
            st.error("کم از کم ایک Groq API Key درج کریں۔")
        else:
            # Dynamically extract all file paths from the prompt
            extracted_paths = re.findall(r'[\w\/\.\-]+\.(?:prisma|json|js|jsx|css|ts|tsx|env|example|txt|md|sql)', prompt_input)
            final_paths = list(dict.fromkeys(extracted_paths))  # Remove duplicates keeping order
            
            if not final_paths:
                st.error("پرامپٹ میں سے کوئی بھی فائل پاتھ (File Path) نہیں مل سکا۔")
            else:
                st.session_state.file_queue = final_paths
                st.session_state.current_file_idx = 0
                st.session_state.is_running = True
                st.session_state.logs = [f"[{time.strftime('%H:%M:%S')}] 🏁 Master Engine initialized. Queue length: {len(final_paths)} modules."]
                st.rerun()

with col_b2:
    if st.button("🛑 Force Stop"):
        st.session_state.is_running = False
        st.warning("پروسیس صارف کی طرف سے روک دیا گیا ہے۔")

# Execution Machine
if st.session_state.is_running and st.session_state.file_queue:
    total_files = len(st.session_state.file_queue)
    curr_idx = st.session_state.current_file_idx

    if curr_idx < total_files:
        current_file = st.session_state.file_queue[curr_idx]

        st.markdown("---")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("### 📊 Mega Build Progress")
            st.markdown(f"""
            <div class='status-card'>
                <h4>پیشرفت کی صورتحال</h4>
                <p>فائلیں مکمل: <b>{curr_idx + 1} / {total_files}</b></p>
                <p>موجودہ ایکٹیو فائل: <br><code>{current_file}</code></p>
            </div>
            """, unsafe_allow_html=True)
            st.progress((curr_idx + 1) / total_files)

        with c2:
            st.markdown("### 📋 Engine Operations Console")
            log_box = st.empty()
            log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        # STRICT SEQUENTIAL PROCESS FOR 1 FILE AT A TIME
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] 🔒 [Lock Active] Generating file: `{current_file}` ({curr_idx + 1}/{total_files})")
        log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        # Generate Single File Content
        code_out = build_large_file_content(prompt_input, current_file, key_mgr)

        clean_code = re.sub(r'^```\w*\n', '', code_out, flags=re.MULTILINE)
        clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

        # Push to GitHub strictly
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ⬆️ Uploading to GitHub repo: `{current_file}`...")
        log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        push_file_to_github_safe(github_repo, current_file, clean_code, github_token)

        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Success! File `{current_file}` uploaded.")
        
        # Advance Queue Index
        st.session_state.current_file_idx += 1
        
        # Cool-down Pause & Dynamic Session Refresh
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] 💤 Cooling down for {safety_delay}s to respect API rate limits...")
        time.sleep(safety_delay)
        st.rerun()

    else:
        st.session_state.is_running = False
        st.success("🎉 تمام کی تمام فائلیں 100% مکمل ہو کر آپ کی GitHub ریپوزٹری میں محفوظ ہو چکی ہیں!")
        st.balloons()

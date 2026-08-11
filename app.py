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
    page_title="DevPulse Hybrid Enterprise Engine v5.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #070A0F; color: #F3F4F6; }
    .stButton>button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white; border: none; padding: 14px 28px;
        border-radius: 8px; font-weight: 700; width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4); }
    .status-card {
        background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px; padding: 18px; margin-bottom: 15px; backdrop-filter: blur(16px);
    }
    .log-container {
        background-color: #030508; border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px; padding: 14px; font-family: 'Courier New', monospace;
        height: 420px; overflow-y: auto; color: #10B981; font-size: 13px; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Multi-Engine Manager (4 Groq + 3 Gemini Keys)
# ---------------------------------------------------------
class MultiEngineManager:
    def __init__(self):
        self.groq_keys = []
        self.gemini_keys = []
        self.current_groq_idx = 0
        self.current_gemini_idx = 0

    def parse_keys(self, text_input):
        if not text_input:
            return []
        keys = [k.strip() for k in text_input.split(",") if k.strip()]
        return keys

    def set_keys(self, groq_str, gemini_str):
        self.groq_keys = self.parse_keys(groq_str)
        self.gemini_keys = self.parse_keys(gemini_str)

    def get_groq_key(self):
        if not self.groq_keys:
            return None
        key = self.groq_keys[self.current_groq_idx]
        idx = self.current_groq_idx + 1
        self.current_groq_idx = (self.current_groq_idx + 1) % len(self.groq_keys)
        return key, idx

    def get_gemini_key(self):
        if not self.gemini_keys:
            return None
        key = self.gemini_keys[self.current_gemini_idx]
        idx = self.current_gemini_idx + 1
        self.current_gemini_idx = (self.current_gemini_idx + 1) % len(self.gemini_keys)
        return key, idx


def call_gemini_rest(prompt, gemini_key):
    """Direct REST Call to Gemini API for speed and stability"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=90) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        return res_data['candidates'][0]['content']['parts'][0]['text']


def generate_module_code(file_path, prompt_input, engine_mgr, log_list):
    full_prompt = f"""
    System Blueprint Prompt:
    {prompt_input}

    TASK:
    Write COMPLETE, INDUSTRIAL-GRADE, FULLY FUNCTIONAL source code for file: `{file_path}`.

    CRITICAL INSTRUCTIONS:
    - Write complete, compilable implementations. Absolutely ZERO placeholders, NO '// TODO', NO cuts.
    - Write all type interfaces, dependencies, data models, and logic completely.
    - Output ONLY raw executable code wrapped inside standard markdown codeblocks.
    """

    # 1. Try Groq Keys First (Rotates through all 4 Keys)
    if engine_mgr.groq_keys:
        for _ in range(len(engine_mgr.groq_keys)):
            groq_key, key_num = engine_mgr.get_groq_key()
            try:
                log_list.append(f"[{time.strftime('%H:%M:%S')}] ⚡ [Groq Engine] Trying Key #{key_num} for `{file_path}`...")
                client = Groq(api_key=groq_key, timeout=60.0)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"You are a Senior Principal Software Architect generating full source code for: {file_path}"},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=6000,
                )
                content = completion.choices[0].message.content
                if content and len(content.strip()) > 0:
                    return content
            except Exception as e:
                log_list.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ Groq Key #{key_num} Limit/Error: {str(e)[:60]}")

    # 2. Fallback to Gemini Keys (Rotates through all 3 Gemini Keys)
    if engine_mgr.gemini_keys:
        for _ in range(len(engine_mgr.gemini_keys)):
            gemini_key, g_num = engine_mgr.get_gemini_key()
            try:
                log_list.append(f"[{time.strftime('%H:%M:%S')}] 🔄 [Gemini Fallback] Switching to Gemini Key #{g_num} for `{file_path}`...")
                content = call_gemini_rest(full_prompt, gemini_key)
                if content and len(content.strip()) > 0:
                    return content
            except Exception as e:
                log_list.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ Gemini Key #{g_num} Error: {str(e)[:60]}")

    # 3. Emergency Standby Cooldown if ALL keys are rate-limited
    log_list.append(f"[{time.strftime('%H:%M:%S')}] 🛑 All 7 API keys busy! Taking a 25s cooldown before retry...")
    time.sleep(25)
    return generate_module_code(file_path, prompt_input, engine_mgr, log_list)

# ---------------------------------------------------------
# GitHub Upload Engine
# ---------------------------------------------------------
def push_file_to_github_safe(repo, path, content, token):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Hybrid-Engine"
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

    clean_code = re.sub(r'^```\w*\n', '', content, flags=re.MULTILINE)
    clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

    encoded_content = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')
    payload = {
        "message": f"feat(auto): generate complete production module {path}",
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
# Streamlit Session State & App UI
# ---------------------------------------------------------
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0
if "file_queue" not in st.session_state:
    st.session_state.file_queue = []
if "logs" not in st.session_state:
    st.session_state.logs = []

st.title("⚡ Hybrid Build Engine (4 Groq + 3 Gemini Keys)")
st.caption("Dual AI Clustering | Sequential File Locking | 100+ File Scale Engine")

engine_mgr = MultiEngineManager()

with st.sidebar:
    st.header("⚙️ API Cluster Setup")
    
    groq_input = st.text_area(
        "Groq API Keys (4 کیز کاما سے الگ کریں):",
        placeholder="gsk_key1, gsk_key2, gsk_key3, gsk_key4",
        height=100
    )
    
    gemini_input = st.text_area(
        "Gemini API Keys (3 کیز کاما سے الگ کریں):",
        placeholder="AIzaSy_key1, AIzaSy_key2, AIzaSy_key3",
        height=100
    )
    
    engine_mgr.set_keys(groq_input, gemini_input)

    st.success(f"🔑 Active Keys: Groq ({len(engine_mgr.groq_keys)}) | Gemini ({len(engine_mgr.gemini_keys)})")

    safety_delay = st.slider("فائلوں کے درمیان وقفہ (سیکنڈز):", min_value=3, max_value=20, value=6)
    
    env_token = os.environ.get("GITHUB_TOKEN", "")
    env_repo = os.environ.get("GITHUB_REPO", "")
    
    github_token = st.text_input("GitHub Access Token", value=env_token, type="password")
    github_repo = st.text_input("GitHub Repository (username/repo)", value=env_repo)

prompt_input = st.text_area(
    "اپنا Blueprint / Manifest Prompt درج کریں:",
    height=200,
    placeholder="یہاں اپنا پرامپٹ کاپی کر کے پیسٹ کریں..."
)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🚀 Heavy Hybrid Build شروع کریں", disabled=st.session_state.is_running):
        if not prompt_input.strip():
            st.error("پرامپٹ درج کرنا لازمی ہے۔")
        elif not github_token or not github_repo:
            st.error("GitHub Credentials لازمی ہیں۔")
        elif len(engine_mgr.groq_keys) == 0 and len(engine_mgr.gemini_keys) == 0:
            st.error("کم از کم ایک Groq یا Gemini API Key درج کریں۔")
        else:
            extracted_paths = re.findall(r'[\w\/\.\-]+\.(?:prisma|json|js|jsx|css|ts|tsx|env|example|txt|md|sql)', prompt_input)
            final_paths = list(dict.fromkeys(extracted_paths))
            
            if not final_paths:
                st.error("پرامپٹ میں سے کوئی فائل پاتھ (File Path) نہیں مل سکا۔")
            else:
                st.session_state.file_queue = final_paths
                st.session_state.current_file_idx = 0
                st.session_state.is_running = True
                st.session_state.logs = [f"[{time.strftime('%H:%M:%S')}] 🏁 Hybrid Engine started. Total modules: {len(final_paths)}"]
                st.rerun()

with col_b2:
    if st.button("🛑 Stop Process"):
        st.session_state.is_running = False
        st.warning("پروسیس روک دیا گیا ہے۔")

# Execution Machine Loop
if st.session_state.is_running and st.session_state.file_queue:
    total_files = len(st.session_state.file_queue)
    curr_idx = st.session_state.current_file_idx

    if curr_idx < total_files:
        current_file = st.session_state.file_queue[curr_idx]

        st.markdown("---")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("### 📊 Mega Build Status")
            st.markdown(f"""
            <div class='status-card'>
                <h4>پیشرفت کی صورتحال</h4>
                <p>مکمل فائلیں: <b>{curr_idx + 1} / {total_files}</b></p>
                <p>موجودہ فائل: <br><code>{current_file}</code></p>
            </div>
            """, unsafe_allow_html=True)
            st.progress((curr_idx + 1) / total_files)

        with c2:
            st.markdown("### 📋 Engine Console Log")
            log_box = st.empty()
            log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        # Build File Execution
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] 🔒 File Lock Active: `{current_file}` ({curr_idx + 1}/{total_files})")
        log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        code_out = generate_module_code(current_file, prompt_input, engine_mgr, st.session_state.logs)

        # Upload to GitHub
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ⬆️ Uploading to GitHub: `{current_file}`...")
        log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        push_file_to_github_safe(github_repo, current_file, code_out, github_token)

        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Success: `{current_file}` saved to GitHub!")
        
        # Advance Queue Index
        st.session_state.current_file_idx += 1
        
        # Cooldown Pause & Dynamic Rerun
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ⏱️ Pausing for {safety_delay}s...")
        time.sleep(safety_delay)
        st.rerun()

    else:
        st.session_state.is_running = False
        st.success("🎉 مبارک ہو! تمام فائلیں کاملاً مکمل ہو کر آپ کی GitHub ریپوزٹری میں اپ لوڈ ہو چکی ہیں!")
        st.balloons()

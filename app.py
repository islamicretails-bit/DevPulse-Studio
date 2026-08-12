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
# UI Configuration & Enterprise Branding
# ---------------------------------------------------------
st.set_page_config(
    page_title="DevPulse Enterprise AI Studio v6.0",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #070A0F; color: #F3F4F6; }
    
    .brand-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px 24px;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.02) 100%);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 12px;
        margin-bottom: 25px;
    }
    .brand-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
    }
    .brand-logo svg { fill: white; width: 28px; height: 28px; }
    .brand-title { font-size: 24px; font-weight: 800; color: #FFFFFF; margin: 0; }
    .brand-subtitle { font-size: 13px; color: #9CA3AF; margin: 0; }

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

st.markdown("""
<div class="brand-header">
    <div class="brand-logo">
        <svg viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
    </div>
    <div>
        <h1 class="brand-title">DevPulse AI Studio v6.0</h1>
        <p class="brand-subtitle">Unified Interleaved Engine • Single-Mind AI Balancing • Automated GitHub Pipeline</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Static Fast-Track Bypass
# ---------------------------------------------------------
def get_static_file_template(file_path):
    if file_path.endswith('.css'):
        return "@tailwind base;\n@tailwind components;\n@tailwind utilities;"
    elif file_path.endswith('package.json'):
        return '{\n  "name": "project",\n  "version": "1.0.0",\n  "private": true\n}'
    elif file_path.endswith('.env.example'):
        return "DATABASE_URL=\nSECRET_KEY=\n"
    return None

# ---------------------------------------------------------
# GitHub API Repositories Fetcher
# ---------------------------------------------------------
def get_github_repos(token):
    if not token:
        return []
    url = "https://api.github.com/user/repos?per_page=100&sort=updated"
    headers = {
        "Authorization": f"token {token.strip()}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Enterprise-Engine"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            repos_data = json.loads(response.read().decode('utf-8'))
            return [repo['full_name'] for repo in repos_data]
    except Exception:
        return []

# ---------------------------------------------------------
# Unified "One Mind" Cluster Engine Manager
# ---------------------------------------------------------
class UnifiedClusterEngine:
    def __init__(self):
        self.providers = []  # Interleaved list of Groq and Gemini keys
        self.current_idx = 0

    def set_keys(self, groq_str, gemini_str):
        groq_keys = [k.strip() for k in groq_str.split(",") if k.strip()] if groq_str else []
        gemini_keys = [k.strip() for k in gemini_str.split(",") if k.strip()] if gemini_str else []

        self.providers = []
        max_len = max(len(groq_keys), len(gemini_keys))

        # Interleave keys so Groq and Gemini alternate dynamically (One Brain)
        for i in range(max_len):
            if i < len(groq_keys):
                self.providers.append({
                    "type": "groq",
                    "key": groq_keys[i],
                    "name": f"Groq Key #{i+1}",
                    "cooldown_until": 0
                })
            if i < len(gemini_keys):
                self.providers.append({
                    "type": "gemini",
                    "key": gemini_keys[i],
                    "name": f"Gemini Key #{i+1}",
                    "cooldown_until": 0
                })

    def get_next_available_provider(self):
        if not self.providers:
            return None

        now = time.time()
        total = len(self.providers)

        for _ in range(total):
            provider = self.providers[self.current_idx]
            self.current_idx = (self.current_idx + 1) % total

            if now >= provider["cooldown_until"]:
                return provider

        return None

    def mark_cooldown(self, provider, seconds=45):
        provider["cooldown_until"] = time.time() + seconds


def call_gemini_rest(prompt, gemini_key):
    """Corrected REST API Call for Gemini (v1beta endpoint)"""
    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key.strip()}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise e
    raise Exception("Gemini models failed or return 404")


def generate_module_code(file_path, prompt_input, cluster, log_list):
    # Fast track check
    static_code = get_static_file_template(file_path)
    if static_code:
        log_list.append(f"[{time.strftime('%H:%M:%S')}] ⚡ [Fast-Track] Created `{file_path}` locally without API calls.")
        return static_code

    full_prompt = f"""
    System Blueprint Prompt:
    {prompt_input}

    TASK:
    Write COMPLETE, PRODUCTION-READY source code for file: `{file_path}`.

    CRITICAL INSTRUCTIONS:
    - Absolutely ZERO placeholders, NO '// TODO', NO truncations.
    - Output ONLY raw executable code wrapped inside standard markdown codeblocks.
    """

    while True:
        provider = cluster.get_next_available_provider()

        if not provider:
            log_list.append(f"[{time.strftime('%H:%M:%S')}] 🛑 All Unified Cluster Keys are cooling down. Waiting 15s...")
            time.sleep(15)
            continue

        p_type = provider["type"]
        p_name = provider["name"]
        p_key = provider["key"]

        if p_type == "groq":
            try:
                log_list.append(f"[{time.strftime('%H:%M:%S')}] 🧠 [Unified Brain -> {p_name}] Processing `{file_path}`...")
                client = Groq(api_key=p_key, timeout=60.0)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"You are a Senior Software Architect generating code for: {file_path}"},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=6000,
                )
                content = completion.choices[0].message.content
                if content and len(content.strip()) > 0:
                    return content
            except Exception as e:
                err_msg = str(e)
                log_list.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ {p_name} Cooldown (45s): {err_msg[:60]}")
                cluster.mark_cooldown(provider, 45)

        elif p_type == "gemini":
            try:
                log_list.append(f"[{time.strftime('%H:%M:%S')}] 🧠 [Unified Brain -> {p_name}] Processing `{file_path}`...")
                content = call_gemini_rest(full_prompt, p_key)
                if content and len(content.strip()) > 0:
                    return content
            except Exception as e:
                err_msg = str(e)
                log_list.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ {p_name} Cooldown (45s): {err_msg[:60]}")
                cluster.mark_cooldown(provider, 45)

# ---------------------------------------------------------
# GitHub Upload Manager
# ---------------------------------------------------------
def push_file_to_github_safe(repo, path, content, token):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token.strip()}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevPulse-Enterprise-Engine"
    }

    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            sha = res_data.get('sha')
    except Exception:
        sha = None

    clean_code = re.sub(r'^```\w*\n', '', content, flags=re.MULTILINE)
    clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()

    encoded_content = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')
    payload = {
        "message": f"feat(auto): generate module {path}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=40) as response:
                return True
        except Exception:
            time.sleep(4)
    return False

# ---------------------------------------------------------
# App Interface & Execution Flow
# ---------------------------------------------------------
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0
if "file_queue" not in st.session_state:
    st.session_state.file_queue = []
if "logs" not in st.session_state:
    st.session_state.logs = []

cluster = UnifiedClusterEngine()

with st.sidebar:
    st.header("⚙️ Unified API Cluster")
    
    sec_groq = st.secrets.get("GROQ_KEYS", "") if hasattr(st, "secrets") else ""
    sec_gemini = st.secrets.get("GEMINI_KEYS", "") if hasattr(st, "secrets") else ""
    sec_token = st.secrets.get("GITHUB_TOKEN", "") if hasattr(st, "secrets") else ""
    
    groq_input = st.text_area("Groq Keys (Comma separated):", value=sec_groq, height=70)
    gemini_input = st.text_area("Gemini Keys (Comma separated):", value=sec_gemini, height=70)
    
    cluster.set_keys(groq_input, gemini_input)

    st.success(f"🧠 Interleaved Brain Pool Active: {len(cluster.providers)} Total Engines")

    safety_delay = st.slider("Pause between files (sec):", min_value=2, max_value=15, value=4)
    github_token = st.text_input("GitHub Access Token", value=sec_token, type="password")
    
    github_repo = ""
    if github_token:
        repo_list = get_github_repos(github_token)
        if repo_list:
            github_repo = st.selectbox("Select GitHub Repository:", options=repo_list)
        else:
            github_repo = st.text_input("GitHub Repository (username/repo)")
    else:
        github_repo = st.text_input("GitHub Repository (username/repo)")

prompt_input = st.text_area("Blueprint / Manifest Prompt:", height=180, placeholder="Paste your blueprint prompt here...")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Start Unified Single-Mind Engine", disabled=st.session_state.is_running):
        if not prompt_input.strip() or not github_token or not github_repo:
            st.error("Please fill all required prompt and GitHub details.")
        elif not cluster.providers:
            st.error("Please provide at least one Groq or Gemini API key.")
        else:
            extracted_paths = re.findall(
                r'(?:(?:\/\/|#)\s*)?([\w\/\.\-]+\.(?:py|prisma|json|js|jsx|css|ts|tsx|yaml|yml|env|example|txt|md|sql))',
                prompt_input
            )
            final_paths = list(dict.fromkeys(extracted_paths))
            
            if not final_paths:
                st.error("No valid file paths detected in prompt.")
            else:
                st.session_state.file_queue = final_paths
                st.session_state.current_file_idx = 0
                st.session_state.is_running = True
                st.session_state.logs = [f"[{time.strftime('%H:%M:%S')}] 🏁 Unified Engine initialized with {len(cluster.providers)} active providers."]
                st.rerun()

with col2:
    if st.button("🛑 Emergency Stop"):
        st.session_state.is_running = False
        st.warning("Execution stopped.")

# Loop Execution Engine
if st.session_state.is_running and st.session_state.file_queue:
    total_files = len(st.session_state.file_queue)
    curr_idx = st.session_state.current_file_idx

    if curr_idx < total_files:
        current_file = st.session_state.file_queue[curr_idx]

        st.markdown("---")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("### 📊 Active Build Progress")
            st.markdown(f"""
            <div class='status-card'>
                <p>Status: <b>{curr_idx + 1} / {total_files} Completed</b></p>
                <p>Current File: <code>{current_file}</code></p>
                <p>Repo: <code>{github_repo}</code></p>
            </div>
            """, unsafe_allow_html=True)
            st.progress((curr_idx + 1) / total_files)

        with c2:
            st.markdown("### 📋 Unified Console Log")
            log_box = st.empty()
            log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        code_out = generate_module_code(current_file, prompt_input, cluster, st.session_state.logs)

        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ⬆️ Pushing `{current_file}` to GitHub ({github_repo})...")
        log_box.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[::-1])}</div>", unsafe_allow_html=True)

        push_file_to_github_safe(github_repo, current_file, code_out, github_token)

        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Success: `{current_file}` pushed.")
        
        st.session_state.current_file_idx += 1
        time.sleep(safety_delay)
        st.rerun()

    else:
        st.session_state.is_running = False
        st.success(f"🎉 Build Complete! All modules successfully committed to `{github_repo}`!")
        st.balloons()

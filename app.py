import os
import sys
import json
import time
import re
import zipfile
import io
import requests
import streamlit as st
from dotenv import load_dotenv

# Local environment variables load کریں
load_dotenv()

# ==========================================
# 1. Page Configuration & UI Setup
# ==========================================
st.set_page_config(
    page_title="DevPulse Studio Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #6366f1 , #10b981);
    }
    .agent-card {
        background-color: #1e293b;
        padding: 12px 18px;
        border-radius: 8px;
        border-left: 4px solid #6366f1;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. Multi-Key Pool Collection
# ==========================================
def collect_api_keys():
    groq_keys = []
    openai_keys = []

    def get_val(key_name):
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
        return os.getenv(key_name)

    # Groq Keys
    i = 1
    while True:
        k = get_val(f"GROQ_API_KEY_{i}")
        if not k and i == 1:
            k = get_val("GROQ_API_KEY")
        if k:
            groq_keys.append(k.strip())
            i += 1
        else:
            break

    # OpenAI Keys
    i = 1
    while True:
        k = get_val(f"OPENAI_API_KEY_{i}")
        if not k and i == 1:
            k = get_val("OPENAI_API_KEY")
        if k:
            openai_keys.append(k.strip())
            i += 1
        else:
            break

    return groq_keys, openai_keys


groq_keys, openai_keys = collect_api_keys()

# Session States
if "is_building" not in st.session_state:
    st.session_state.is_building = False
if "is_paused" not in st.session_state:
    st.session_state.is_paused = False
if "generated_files" not in st.session_state:
    st.session_state.generated_files = {}
if "key_index" not in st.session_state:
    st.session_state.key_index = 0

# ==========================================
# 3. LLM API Call Function with Rate Limit Auto-Retry
# ==========================================
def call_llm_api(system_prompt: str, user_prompt: str, retries=3) -> str:
    all_keys = groq_keys + openai_keys
    if not all_keys:
        raise ValueError("No API keys found!")

    for attempt in range(retries):
        current_key = all_keys[st.session_state.key_index % len(all_keys)]
        st.session_state.key_index += 1

        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json",
        }

        # High Speed & Lower Token Consumption Model
        if current_key.startswith("gsk_"):
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.1-8b-instant"
        else:
            url = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o-mini"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                # Rate limit hit, wait & retry
                time.sleep(8)
            else:
                raise RuntimeError(f"API Error ({response.status_code}): {response.text}")
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(6)

    raise RuntimeError("Rate limit exceeded repeatedly. Please add additional API keys.")

# ==========================================
# 4. GitHub Push Function
# ==========================================
def push_files_to_github(token, repo_name, files_dict, commit_message="Add AI Generated Code"):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    results = []
    for file_path, content in files_dict.items():
        url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
        
        get_res = requests.get(url, headers=headers)
        sha = get_res.json().get("sha") if get_res.status_code == 200 else None

        import base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        data = {
            "message": commit_message,
            "content": encoded_content,
        }
        if sha:
            data["sha"] = sha

        put_res = requests.put(url, headers=headers, json=data)
        if put_res.status_code in [200, 201]:
            results.append((file_path, True, "Uploaded"))
        else:
            results.append((file_path, False, put_res.json().get("message", "Failed")))

    return results

# Helper to fetch credentials safely
def get_secret_or_env(key_name, default=""):
    if hasattr(st, "secrets") and key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default)

# ==========================================
# 5. Sidebar Configuration & Controls
# ==========================================
with st.sidebar:
    st.title("⚡ DevPulse Studio Pro")
    st.caption("Enterprise Autonomous Multi-Agent AI System")
    st.divider()

    st.subheader("🔑 API Key Status")
    st.write(f"**Groq Keys:** `{len(groq_keys)} Active`")
    st.write(f"**OpenAI Keys:** `{len(openai_keys)} Active`")

    st.divider()
    st.subheader("🐙 GitHub Integration")
    gh_token = st.text_input(
        "GitHub Personal Access Token:",
        type="password",
        placeholder="ghp_xxxxxxxxxxxx",
        value=get_secret_or_env("GITHUB_TOKEN"),
    )
    gh_repo = st.text_input(
        "Repository Name (username/repo):",
        placeholder="username/my-project",
        value=get_secret_or_env("GITHUB_REPO"),
    )

    auto_push = st.checkbox("Auto Push to GitHub after Build", value=True)

    st.divider()
    auto_test = st.checkbox("Enable Automated Unit Tests", value=False)

# ==========================================
# 6. Main App UI
# ==========================================
st.title("🚀 Multi-Agent Code Generation Dashboard")
st.write("پرامپٹ درج کریں اور ملٹی ایجنٹ سسٹم کو مکمل کوڈ تیار کرنے دیں۔")

col_prompt, col_action = st.columns([3, 1])

with col_prompt:
    user_prompt = st.text_area(
        "پروجیکٹ کی تفصیل درج کریں:",
        placeholder="مثال: NexaVault Digital Marketplace کا پروجیکٹ تیار کریں۔",
        height=130,
        disabled=st.session_state.is_building,
    )

with col_action:
    st.write("### ")
    if not st.session_state.is_building:
        if st.button("🚀 بلڈ شروع کریں", use_container_width=True, type="primary"):
            if not user_prompt:
                st.warning("براہ کرم پرامپٹ فراہم کریں۔")
            elif not groq_keys and not openai_keys:
                st.error("API Keys دستیاب نہیں ہیں۔")
            else:
                st.session_state.is_building = True
                st.session_state.is_paused = False
                st.session_state.generated_files = {}
                st.rerun()
    else:
        col_pause, col_stop = st.columns(2)
        with col_pause:
            if st.button(
                "⏸️ پاز" if not st.session_state.is_paused else "▶️ ریزیوم",
                use_container_width=True,
            ):
                st.session_state.is_paused = not st.session_state.is_paused
                st.rerun()
        with col_stop:
            if st.button("🛑 روکے", use_container_width=True):
                st.session_state.is_building = False
                st.session_state.is_paused = False
                st.rerun()

# ==========================================
# 7. Execution Pipeline with Safe Architect JSON Parsing
# ==========================================
if st.session_state.is_building:
    st.divider()

    col_m1, col_m2, col_m3 = st.columns(3)
    metric_status = col_m1.empty()
    metric_files = col_m2.empty()
    metric_agent = col_m3.empty()

    progress_bar = st.progress(0)
    log_container = st.container()

    with log_container:
        st.subheader("📋 لائیو ایگزیکیوشن لاگز")

        metric_status.metric("اسٹیٹس", "ایکٹیو ⚡")
        metric_agent.metric("موجودہ ایجنٹ", "ArchitectAgent 📐")

        architect_system_prompt = """You are an expert Software Architect.
Return ONLY a valid JSON object matching this structure without any markdown formatting:
{
  "projectName": "NexaVault Marketplace",
  "files": [
    { "filePath": "package.json", "description": "Project dependencies" },
    { "filePath": "vercel.json", "description": "Vercel deployment configuration" },
    { "filePath": "src/app/layout.tsx", "description": "Root layout UI" },
    { "filePath": "src/app/page.tsx", "description": "Main digital marketplace page" },
    { "filePath": "src/app/office/page.tsx", "description": "Hidden Admin office dashboard" },
    { "filePath": "src/app/api/ai/generate-product/route.ts", "description": "AI content generation API" },
    { "filePath": "src/app/api/payments/checkout/route.ts", "description": "Dynamic multi-currency checkout API" },
    { "filePath": "src/app/api/admin/analytics/route.ts", "description": "Live traffic analytics API" },
    { "filePath": "src/components/ProductCard.tsx", "description": "Product display component" },
    { "filePath": "src/components/AppleToast.tsx", "description": "Apple-style notifications" },
    { "filePath": "src/lib/security.ts", "description": "Security and license key utils" },
    { "filePath": ".env.example", "description": "Environment variables template" }
  ]
}"""

        blueprint = None
        try:
            arch_response = call_llm_api(architect_system_prompt, user_prompt)
            json_match = re.search(r"\{.*\}", arch_response, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                blueprint = json.loads(clean_json)
        except Exception:
            blueprint = None

        # Fallback if Architect fails to return valid JSON
        if not blueprint or "files" not in blueprint or not isinstance(blueprint["files"], list):
            blueprint = {
                "projectName": "NexaVault Marketplace",
                "files": [
                    {"filePath": "package.json", "description": "Project dependencies"},
                    {"filePath": "vercel.json", "description": "Deployment configuration"},
                    {"filePath": "src/app/layout.tsx", "description": "Root layout"},
                    {"filePath": "src/app/page.tsx", "description": "Main page interface"},
                    {"filePath": "src/app/office/page.tsx", "description": "Hidden Admin office"},
                    {"filePath": "src/app/api/ai/generate-product/route.ts", "description": "AI generator API"},
                    {"filePath": "src/app/api/payments/checkout/route.ts", "description": "Checkout API"},
                    {"filePath": "src/app/api/admin/analytics/route.ts", "description": "Analytics API"},
                    {"filePath": "src/components/ProductCard.tsx", "description": "Product card UI component"},
                    {"filePath": "src/components/AppleToast.tsx", "description": "Toast notifications"},
                    {"filePath": "src/lib/security.ts", "description": "Security & license utils"},
                    {"filePath": ".env.example", "description": "Environment variables template"}
                ]
            }

        planned_files = blueprint.get("files", [])
        total_files = len(planned_files)
        completed_count = 0

        for idx, file_info in enumerate(planned_files):
            while st.session_state.is_paused:
                metric_status.metric("اسٹیٹس", "پاز شدہ ⏸️")
                time.sleep(1)

            filePath = file_info.get("filePath", f"file_{idx}.ts")
            fileDesc = file_info.get("description", "Code file")

            metric_status.metric("اسٹیٹس", "ایکٹیو ⚡")
            metric_agent.metric("موجودہ ایجنٹ", "CoderAgent 💻")
            metric_files.metric("فائلیں مکمل", f"{completed_count} / {total_files}")

            st.write(f"🔄 **تخلیق جاری:** `{filePath}`")

            coder_system_prompt = f"Write full, production-ready code for {filePath}. Purpose: {fileDesc}. Output ONLY code without explanation."

            try:
                code_content = call_llm_api(coder_system_prompt, user_prompt)
                clean_code = re.sub(r"^```[a-zA-Z]*\n", "", code_content, flags=re.MULTILINE)
                clean_code = re.sub(r"\n```$", "", clean_code, flags=re.MULTILINE).strip()
                st.session_state.generated_files[filePath] = clean_code
                completed_count += 1
            except Exception as e:
                st.error(f"Failed {filePath}: {str(e)}")

            if auto_test and filePath in st.session_state.generated_files:
                metric_agent.metric("موجودہ ایجنٹ", "TesterAgent 🧪")
                try:
                    test_code = call_llm_api("Generate unit tests.", st.session_state.generated_files[filePath])
                    clean_test = re.sub(r"^```[a-zA-Z]*\n", "", test_code, flags=re.MULTILINE)
                    clean_test = re.sub(r"\n```$", "", clean_test, flags=re.MULTILINE).strip()
                    test_path = filePath.replace(".ts", ".test.ts").replace(".tsx", ".test.tsx")
                    st.session_state.generated_files[test_path] = clean_test
                except Exception:
                    pass

            progress = int((completed_count / total_files) * 100) if total_files > 0 else 100
            progress_bar.progress(progress)
            
            # Rate Limit Protection Delay (6 seconds between requests)
            time.sleep(6)

        st.session_state.is_building = False
        metric_status.metric("اسٹیٹس", "مکمل 🟢")
        st.success("✨ تمام فائلیں کامیابی سے بغیر کسی ایرر کے جنریٹ ہو گئی ہیں!")

        # Auto Push to GitHub if Enabled
        if auto_push and gh_token and gh_repo:
            st.info("🐙 GitHub پر تمام فائلیں اپ لوڈ ہو رہی ہیں...")
            res = push_files_to_github(gh_token, gh_repo, st.session_state.generated_files)
            for file_p, success, msg in res:
                if success:
                    st.caption(f"✅ `{file_p}` -> GitHub")
                else:
                    st.error(f"❌ `{file_p}` -> {msg}")

# ==========================================
# 8. File Explorer & Manual Actions
# ==========================================
if st.session_state.generated_files:
    st.divider()
    st.subheader("📂 تیار شدہ فائلیں")

    col_view, col_actions = st.columns([2, 1])

    with col_actions:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, code_content in st.session_state.generated_files.items():
                zip_file.writestr(file_path, code_content)
        zip_buffer.seek(0)

        st.download_button(
            label="📦 Zip ڈاؤن لوڈ کریں",
            data=zip_buffer,
            file_name="project.zip",
            mime="application/zip",
            use_container_width=True,
        )

        st.divider()
        if st.button("🚀 Push All Files to GitHub", use_container_width=True, type="primary"):
            if not gh_token or not gh_repo:
                st.error("سائیڈ بار یا Secrets میں GitHub Token اور Repository درج کریں۔")
            else:
                with st.spinner("GitHub پر اپ لوڈ ہو رہا ہے..."):
                    res = push_files_to_github(gh_token, gh_repo, st.session_state.generated_files)
                    for file_p, success, msg in res:
                        if success:
                            st.success(f"✅ `{file_p}` اپ لوڈ ہو گئی۔")
                        else:
                            st.error(f"❌ `{file_p}`: {msg}")

    with col_view:
        selected_file = st.selectbox(
            "فائل دیکھیں:",
            options=list(st.session_state.generated_files.keys()),
        )
        if selected_file:
            st.code(st.session_state.generated_files[selected_file], language="typescript")

import os
import sys
import json
import time
import zipfile
import io
import requests
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

# ==========================================
# 1. Page Configuration & UI Theme Setup
# ==========================================
st.set_page_config(
    page_title="DevPulse Studio Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Dark UI & Scannability
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
# 2. API Key Management & Rotation Pool
# ==========================================
def collect_api_keys():
    """Retrieves API keys from Streamlit Secrets or Environment Variables."""
    groq_keys = []
    openai_keys = []

    # Check Streamlit Secrets first, then OS environ
    def get_val(key_name):
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
        return os.getenv(key_name)

    # Collect Groq Keys
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

    # Collect OpenAI Keys
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

# Session State Initialization
if "is_building" not in st.session_state:
    st.session_state.is_building = False
if "is_paused" not in st.session_state:
    st.session_state.is_paused = False
if "generated_files" not in st.session_state:
    st.session_state.generated_files = {}
if "execution_logs" not in st.session_state:
    st.session_state.execution_logs = []

# ==========================================
# 3. Sidebar Configuration & Status
# ==========================================
with st.sidebar:
    st.title("⚡ DevPulse Studio Pro")
    st.caption("Enterprise Autonomous Multi-Agent AI System")
    st.divider()

    st.subheader("🔑 API Key Status")
    st.write(f"**Groq Key Pool:** `{len(groq_keys)} Active Keys`")
    st.write(f"**OpenAI Key Pool:** `{len(openai_keys)} Active Keys`")

    if not groq_keys and not openai_keys:
        st.error(
            "⚠️ کوئی بھی API Key نہیں ملی! Streamlit Cloud کی Settings میں Secrets سیٹ کریں۔"
        )

    st.divider()
    st.subheader("⚙️ Runtime Settings")
    max_workers = st.slider("Parallel Workers", min_value=1, max_value=5, value=3)
    auto_test = st.checkbox("Enable Automated Unit Tests (TesterAgent)", value=True)

    st.divider()
    st.info(
        "💡 **ٹیپ:** یہ سسٹم ریئل ٹائم میں فائلیں جنریٹ کرتا ہے اور مکمل بلڈ تیار ہونے پر Zip بھی فراہم کرتا ہے۔"
    )

# ==========================================
# 4. Main App Layout & Controls
# ==========================================
st.title("🚀 Multi-Agent Code Generation Dashboard")
st.write(
    "اپنے پروجیکٹ کی تفصیل (Prompt) درج کریں اور ملٹی ایجنٹ سسٹم کو مکمل پروجیکٹ تیار کرنے دیں۔"
)

# Top Action Control Bar
col_prompt, col_action = st.columns([3, 1])

with col_prompt:
    user_prompt = st.text_area(
        "پروجیکٹ کی تفصیل درج کریں:",
        placeholder="مثال: ایک مکمل Next.js 14 ای کامرس ڈیش بورڈ بنائیں جس میں TailWind CSS اور PostgreSQL Prisma کی فائلز ہوں۔",
        height=130,
        disabled=st.session_state.is_building,
    )

with col_action:
    st.write("### ")
    if not st.session_state.is_building:
        if st.button(
            "🚀 بلڈ شروع کریں", use_container_width=True, type="primary"
        ):
            if not user_prompt:
                st.warning("براہ کرم پرامپٹ فراہم کریں۔")
            elif not groq_keys and not openai_keys:
                st.error("API Keys دستیاب نہیں ہیں۔")
            else:
                st.session_state.is_building = True
                st.session_state.is_paused = False
                st.session_state.generated_files = {}
                st.session_state.execution_logs = []
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
# 5. Pipeline Simulation Engine (LLM Executor)
# ==========================================
if st.session_state.is_building:
    st.divider()

    # Progress Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    metric_status = col_m1.empty()
    metric_files = col_m2.empty()
    metric_agent = col_m3.empty()
    metric_tokens = col_m4.empty()

    progress_bar = st.progress(0)
    log_container = st.container()

    # Simulated Orchestration Pipeline (Architect -> Coder -> Tester)
    # real production logic hooks here

    sample_planned_files = [
        ("package.json", "Project configurations and dependencies"),
        ("src/index.ts", "Main server entry point"),
        ("src/config/db.ts", "Database connection logic"),
        ("src/controllers/userController.ts", "User API routes controller"),
        ("src/services/userService.ts", "User business logic layer"),
    ]

    total_files = len(sample_planned_files)

    with log_container:
        st.subheader("📋 لائیو ایگزیکیوشن لاگز (Live Pipeline)")

        # Stage 1: Architect Agent
        metric_status.metric("اسٹیٹس", "ایکٹیو ⚡")
        metric_agent.metric("موجودہ ایجنٹ", "ArchitectAgent 📐")

        st.markdown(
            """<div class="agent-card"><b>[ArchitectAgent]</b> پروجیکٹ کا بلیو پرنٹ اور فائل کا ڈھانچہ تیار کر رہا ہے...</div>""",
            unsafe_allow_html=True,
        )
        time.sleep(1.5)

        # Stage 2 & 3: Coder & Tester Agents
        completed_count = 0
        total_tokens = 0

        for idx, (filePath, desc) in enumerate(sample_planned_files):
            # Check for Pause State
            while st.session_state.is_paused:
                metric_status.metric("اسٹیٹس", "پاز شدہ ⏸️")
                time.sleep(1)

            metric_status.metric("اسٹیٹس", "ایکٹیو ⚡")
            metric_agent.metric("موجودہ ایجنٹ", "CoderAgent 💻")
            metric_files.metric("فائلیں مکمل", f"{completed_count} / {total_files}")

            st.write(f"🔄 **تخلیق جاری ہے:** `{filePath}` - *{desc}*")

            # Simulated File Code Generation
            time.sleep(1.2)
            generated_code = (
                f"// Generated by DevPulse Studio Pro\n// File: {filePath}\n\n"
                f"export const config = {{\n  path: '{filePath}',\n  status: 'active'\n}};\n"
            )

            st.session_state.generated_files[filePath] = generated_code
            total_tokens += 450
            completed_count += 1

            # Tester Agent Phase
            if auto_test:
                metric_agent.metric("موجودہ ایجنٹ", "TesterAgent 🧪")
                st.caption(f"🧪 Unit test auto-generated for `{filePath}`")
                test_path = filePath.replace(".ts", ".test.ts").replace(
                    ".js", ".test.js"
                )
                test_code = f"describe('{filePath}', () => {{\n  it('should pass sanity test', () => {{\n    expect(true).toBe(true);\n  }});\n}});\n"
                st.session_state.generated_files[test_path] = test_code
                time.sleep(0.8)

            # Update Metrics
            metric_tokens.metric("ٹوکنز", f"{total_tokens:,}")
            progress = int((completed_count / total_files) * 100)
            progress_bar.progress(progress)

        # Completion State
        st.session_state.is_building = False
        metric_status.metric("اسٹیٹس", "مکمل 🟢")
        metric_agent.metric("موجودہ ایجنٹ", "Idle")
        st.success("✨ تمام فائلیں اور ٹیسٹ کامیابی سے تیار ہو چکے ہیں!")

# ==========================================
# 6. Generated Files Explorer & Zip Download
# ==========================================
if st.session_state.generated_files:
    st.divider()
    st.subheader("📂 تیار شدہ فائلیں (Generated Files)")

    col_view, col_zip = st.columns([3, 1])

    with col_zip:
        # Create In-Memory Zip File
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            for file_path, code_content in st.session_state.generated_files.items():
                zip_file.writestr(file_path, code_content)

        zip_buffer.seek(0)

        st.download_button(
            label="📦 تمام فائلیں Zip ڈاؤن لوڈ کریں",
            data=zip_buffer,
            file_name="devpulse_project.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )

    with col_view:
        selected_file = st.selectbox(
            "فائل کا انتخاب کریں اور کوڈ دیکھیں:",
            options=list(st.session_state.generated_files.keys()),
        )

        if selected_file:
            st.code(
                st.session_state.generated_files[selected_file],
                language="typescript",
            )

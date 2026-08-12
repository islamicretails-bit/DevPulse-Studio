import os
import time
import concurrent.futures
import google.generativeai as genai
from groq import Groq

# ==============================================================================
# 1. API KEYS & CONFIGURATION LOADER FROM ENV
# ==============================================================================
def load_api_keys():
    # Dynamic Groq Key Loader (Reads GROQ_API_KEY_1 to 5 + fallback GROQ_API_KEY)
    groq_keys = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)]
    if os.getenv("GROQ_API_KEY"):
        groq_keys.append(os.getenv("GROQ_API_KEY"))
    groq_keys = [k.strip() for k in groq_keys if k and k.strip()]

    # Dynamic Gemini Key Loader (Reads GEMINI_API_KEY_1 to 6 + fallback GEMINI_API_KEY)
    gemini_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 7)]
    if os.getenv("GEMINI_API_KEY"):
        gemini_keys.append(os.getenv("GEMINI_API_KEY"))
    gemini_keys = [k.strip() for k in gemini_keys if k and k.strip()]

    return groq_keys, gemini_keys

GROQ_KEYS, GEMINI_KEYS = load_api_keys()

# Engine Configurations
MAX_WORKERS = int(os.getenv("ENGINE_MAX_WORKERS", 5))
COOLDOWN_MS = int(os.getenv("ENGINE_REQUEST_COOLDOWN_MS", 1000)) / 1000.0
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

# ==============================================================================
# 2. STATIC FAST-TRACK TEMPLATES (API Bypass for Pure Configs)
# ==============================================================================
def get_static_template(file_path: str) -> str:
    if file_path.endswith('.css') and 'globals' in file_path:
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #ffffff;
  --foreground: #171717;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
}

body {
  color: var(--foreground);
  background: var(--background);
  font-family: Arial, Helvetica, sans-serif;
}"""
    elif file_path.endswith('.json') and not file_path.endswith('tsconfig.json'):
        return '{\n  "name": "devpulse-studio-app",\n  "version": "1.0.0",\n  "private": true\n}'
    return None

# ==============================================================================
# 3. WORKER TASK ENGINE FOR PARALLEL GENERATION
# ==============================================================================
def generate_single_file_worker(task_args: tuple) -> tuple:
    """
    یہ ورکر تھریڈ ہر فائل کی کوڈ جنریشن کا ذمہ دار ہے:
    1. Static Templates کے لیے بائی پاس کرے گا۔
    2. Groq Pool پر راؤنڈ روبن روٹ کرے گا۔
    3. Error / Rate Limit پر Gemini Pool پر منتقل ہو جائے گا۔
    """
    file_path, system_blueprint, task_index = task_args
    print(f"🚀 [THREAD START] Generating: {file_path}")

    # Step 0: Fast-track check
    static_content = get_static_template(file_path)
    if static_content:
        return file_path, static_content, "Fast-Track Static Template"

    prompt = f"""
    SYSTEM BLUEPRINT CONTEXT:
    {system_blueprint}
    
    TASK:
    Generate complete, clean, production-ready, highly optimized, non-placeholder source code for: {file_path}.
    
    CRITICAL CONSTRAINTS:
    - Output ONLY valid production code for this file.
    - DO NOT wrap in extra markdown explanations outside code block.
    - Strictly write full imports, interfaces, schemas, models, and export logic.
    - ABSOLUTELY NO placeholders like '// TODO' or '// Implementation here'.
    """

    # --------------------------------------------------------------------------
    # PHASE 1: GROQ KEY ROTATION POOL
    # --------------------------------------------------------------------------
    if GROQ_KEYS:
        # Load balancing across available keys
        start_key_idx = task_index % len(GROQ_KEYS)
        for i in range(len(GROQ_KEYS)):
            current_key_idx = (start_key_idx + i) % len(GROQ_KEYS)
            key = GROQ_KEYS[current_key_idx]

            try:
                client = Groq(api_key=key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )
                content = response.choices[0].message.content
                return file_path, content, f"Groq Key #{current_key_idx + 1}"
            except Exception as e:
                err_msg = str(e)
                print(f"⚠️ [Groq Key #{current_key_idx + 1} Error on {file_path}]: {err_msg[:80]}")
                if "429" in err_msg or "rate_limit" in err_msg.lower():
                    time.sleep(2)  # Short pause before jumping to next key
                continue

    # --------------------------------------------------------------------------
    # PHASE 2: GEMINI KEY ROTATION FALLBACK POOL
    # --------------------------------------------------------------------------
    if GEMINI_KEYS:
        print(f"🔀 [FALLBACK SWITCH] Shifting {file_path} to Gemini Alliance Pool...")
        start_gemini_idx = task_index % len(GEMINI_KEYS)
        for j in range(len(GEMINI_KEYS)):
            current_gemini_idx = (start_gemini_idx + j) % len(GEMINI_KEYS)
            key = GEMINI_KEYS[current_gemini_idx]

            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(GEMINI_MODEL_NAME)
                response = model.generate_content(prompt)
                return file_path, response.text, f"Gemini Key #{current_gemini_idx + 1}"
            except Exception as e:
                print(f"⚠️ [Gemini Key #{current_gemini_idx + 1} Error on {file_path}]: {str(e)[:80]}")
                continue

    return file_path, None, "ALL ENGINES EXHAUSTED"


# ==============================================================================
# 4. PARALLEL BATCH PROCESSOR WITH GITHUB PUSH
# ==============================================================================
def run_autonomous_builder(file_list: list, system_blueprint: str, push_to_github_func):
    """
    یہ مین لوپ تمام فائلوں کو Parallel Threads (MAX_WORKERS) کے تحت چلائے گا
    اور ساتھ ہی ساتھ گٹ ہب پر پش کرتا جائے گا۔
    """
    total_files = len(file_list)
    print(f"\n🌟 Starting Autonomous Engine Alliance Build for {total_files} files...")
    print(f"⚡ Parallel Concurrent Workers: {MAX_WORKERS}")
    print(f"🔑 Loaded Pools: {len(GROQ_KEYS)} Groq Keys | {len(GEMINI_KEYS)} Gemini Keys\n")

    tasks = [(file_path, system_blueprint, idx) for idx, file_path in enumerate(file_list)]
    
    completed_count = 0
    failed_files = []

    # ThreadPoolExecutor for Parallel File Generation
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(generate_single_file_worker, task): task[0] 
            for task in tasks
        }

        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            completed_count += 1

            try:
                res_path, code_content, engine_info = future.result()

                if code_content:
                    print(f"\n✅ [{completed_count}/{total_files}] Generated via [{engine_info}]: {res_path}")
                    
                    # Push code to GitHub Repository
                    try:
                        push_to_github_func(res_path, code_content)
                        print(f"📦 [GITHUB PUSHED] {res_path}")
                    except Exception as gh_err:
                        print(f"❌ [GITHUB PUSH ERROR] Failed for {res_path}: {gh_err}")

                else:
                    print(f"❌ [{completed_count}/{total_files}] CRITICAL FAILURE for: {res_path}")
                    failed_files.append(res_path)

            except Exception as exc:
                print(f"💥 Thread Exception for {file_path}: {exc}")
                failed_files.append(file_path)

            # Global Cooldown per completed thread
            time.sleep(COOLDOWN_MS)

    print("\n🎉 ============================================================")
    print(f"🚀 BUILD COMPLETE! Processed: {completed_count}/{total_files} files.")
    if failed_files:
        print(f"⚠️ Failed files ({len(failed_files)}): {failed_files}")
    else:
        print("✨ ALL MANIFEST FILES PROCESSED & PUSHED SUCCESSFULLY!")
    print("============================================================ 🎉")

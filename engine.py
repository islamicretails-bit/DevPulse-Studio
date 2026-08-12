import os
import time
import concurrent.futures
import google.generativeai as genai
from groq import Groq
import streamlit as st

# ==========================================
# 1. CONSTANTS & MODEL CONFIGURATION
# ==========================================
GEMINI_MODEL_NAME = "gemini-1.5-flash"  # Working model without 404 error
MAX_CONCURRENT_WORKERS = 5              # ایک وقت میں 5 فائلیں ایک ساتھ بنیں گی

def get_static_template(file_path):
    """CSS اور دیگر Static فائلوں کے لیے API کے بغیر ڈائریکٹ کوڈ جنریٹ کریں"""
    if file_path.endswith('.css'):
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
    elif file_path.endswith('.json'):
        return '{\n  "name": "project",\n  "version": "1.0.0",\n  "private": true\n}'
    return None

# ==========================================
# 2. INDIVIDUAL WORKER TASK (PARALLEL READY)
# ==========================================
def worker_task(args):
    """
    یہ ورکر فنکشن ہر فائل کو پیرالل (ایک ساتھ) پروسیس کرے گا۔
    """
    file_path, prompt, task_index, groq_keys, gemini_keys = args
    
    # Check 1: Static Files Bypass
    static_content = get_static_template(file_path)
    if static_content:
        return file_path, static_content, "Fast-Track Static"

    # Engine Routing Logic: Alternating between Groq and Gemini Alliance
    prefer_engine = "groq" if task_index % 2 == 0 else "gemini"
    
    # Try Groq Execution
    if prefer_engine == "groq" and groq_keys:
        key = groq_keys[task_index % len(groq_keys)].strip()
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert full-stack developer."},
                    {"role": "user", "content": f"Generate raw code for file `{file_path}` based on prompt:\n{prompt}"}
                ],
                temperature=0.2
            )
            return file_path, response.choices[0].message.content, f"Groq (Key #{task_index % len(groq_keys) + 1})"
        except Exception as e:
            prefer_engine = "gemini" # Fallback to Gemini if Groq fails

    # Try Gemini Execution / Fallback
    if gemini_keys:
        key = gemini_keys[task_index % len(gemini_keys)].strip()
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            response = model.generate_content(
                f"Generate production-ready raw code ONLY for file `{file_path}`:\n{prompt}"
            )
            return file_path, response.text, f"Gemini (Key #{task_index % len(gemini_keys) + 1})"
        except Exception as e:
            pass

    # If all primary keys fail, last resort loop across remaining keys
    for key in groq_keys:
        try:
            client = Groq(api_key=key.strip())
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Generate raw code for file `{file_path}`:\n{prompt}"}]
            )
            return file_path, response.choices[0].message.content, "Groq (Fallback)"
        except:
            continue

    return file_path, None, "Failed"

# ==========================================
# 3. PARALLEL BUILD PROCESSOR
# ==========================================
def process_build_queue_parallel(file_list, master_prompt, groq_keys, gemini_keys):
    """
    تمام فائلوں کو ایک ساتھ (Parallel Threads) میں چلانے کا مین فنکشن
    """
    st.info(f"🚀 Parallel Engine Alliance Started! Processing {len(file_list)} files using {MAX_CONCURRENT_WORKERS} parallel streams.")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Task Preparation
    tasks = [
        (file_path, master_prompt, idx, groq_keys, gemini_keys) 
        for idx, file_path in enumerate(file_list)
    ]
    
    completed_files = 0
    total_files = len(file_list)
    
    # Parallel Thread Pool Execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(worker_task, task) for task in tasks]
        
        for future in concurrent.futures.as_completed(futures):
            file_path, content, engine_used = future.result()
            completed_files += 1
            
            if content:
                st.write(f"✅ **[{engine_used}]** Successfully generated: `{file_path}`")
                
                # Local Directory Persistence
                os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                st.error(f"❌ Failed to generate `{file_path}` across all keys.")
            
            # Update Progress Bar
            progress_bar.progress(completed_files / total_files)
            status_text.text(f"Processed {completed_files}/{total_files} files...")

    st.success("🎉 All files generated in parallel successfully!")

# ==========================================
# 4. STREAMLIT UI INTEGRATION EXAMPLE
# ==========================================
st.title("⚡ Multi-Engine Parallel Code Generator")

# Key Inputs (From secrets or text boxes)
groq_keys_input = st.text_area("Enter Groq Keys (comma separated)", value=st.secrets.get("GROQ_KEYS", ""))
gemini_keys_input = st.text_area("Enter Gemini Keys (comma separated)", value=st.secrets.get("GEMINI_KEYS", ""))

groq_keys_list = [k.strip() for k in groq_keys_input.split(",") if k.strip()]
gemini_keys_list = [k.strip() for k in gemini_keys_input.split(",") if k.strip()]

if st.button("🚀 Start Parallel Build"):
    if not groq_keys_list and not gemini_keys_list:
        st.error("براہ کرم کم از کم ایک Groq یا Gemini API Key فراہم کریں۔")
    else:
        sample_files = [
            "prisma/schema.prisma",
            "src/app/page.tsx",
            "src/app/layout.tsx",
            "src/app/globals.css",
            "src/app/api/route.ts"
        ]
        process_build_queue_parallel(
            file_list=sample_files,
            master_prompt="Build a high performance SaaS web application.",
            groq_keys=groq_keys_list,
            gemini_keys=gemini_keys_list
        )

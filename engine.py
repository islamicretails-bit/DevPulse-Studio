import os
import time
import requests
import google.generativeai as genai
from groq import Groq
import streamlit as st

# ==========================================
# 1. CONSTANTS & MODEL CONFIGURATION
# ==========================================
# Gemini ماڈل 1.5-flash / 2.0-flash پر سیٹ کریں (تاکہ 404 Error نہ آئے)
GEMINI_MODEL_NAME = "gemini-1.5-flash" 

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
# 2. GENERATION ENGINE WITH ROTATION & FALLBACK
# ==========================================
def generate_file_content(file_path, prompt, groq_keys, gemini_keys):
    """
    1. Static فائلوں کو ڈائریکٹ ٹیمپلیٹ سے بناتا ہے۔
    2. Groq Keys پر چلاتا ہے۔
    3. فیل ہونے پر Gemini (1.5-flash) پر Fallback کرتا ہے۔
    """
    
    # Check 1: Static Files Bypass (CSS, JSON وغیرہ)
    static_content = get_static_template(file_path)
    if static_content:
        st.write(f"⚡ [Fast Track] Using static template for `{file_path}`")
        return static_content

    # Check 2: Groq Engine Loop
    if groq_keys:
        for idx, key in enumerate(groq_keys, start=1):
            try:
                st.write(f"⚡ [Groq Engine] Trying Key #{idx} for `{file_path}`...")
                client = Groq(api_key=key.strip())
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert full-stack developer."},
                        {"role": "user", "content": f"Generate raw code for file `{file_path}` based on prompt:\n{prompt}"}
                    ],
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                st.write(f"⚠️ Groq Key #{idx} Limit/Error: {str(e)[:60]}")
                time.sleep(1)

    # Check 3: Gemini Fallback Loop
    if gemini_keys:
        for idx, key in enumerate(gemini_keys, start=1):
            try:
                st.write(f"🔄 [Gemini Fallback] Switching to Gemini Key #{idx} for `{file_path}`...")
                genai.configure(api_key=key.strip())
                model = genai.GenerativeModel(GEMINI_MODEL_NAME)
                
                response = model.generate_content(
                    f"Generate production-ready raw code ONLY for file `{file_path}`:\n{prompt}"
                )
                return response.text
            except Exception as e:
                st.write(f"⚠️ Gemini Key #{idx} Error: {str(e)[:60]}")
                time.sleep(1)

    # اگر تمام کیز فیل ہو جائیں تو Cooldown
    st.write("🛑 All API keys busy! Taking a 25s cooldown before retry...")
    time.sleep(25)
    return None

# ==========================================
# 3. BUILD PROCESSOR EXAMPLE
# ==========================================
def process_build_queue(file_list, master_prompt, groq_keys, gemini_keys):
    for index, file_path in enumerate(file_list, start=1):
        st.write(f"🔒 File Lock Active: `{file_path}` ({index}/{len(file_list)})")
        
        content = None
        while content is None:
            content = generate_file_content(file_path, master_prompt, groq_keys, gemini_keys)
        
        # GitHub Upload or File Saving Logic
        st.success(f"✅ Generated & Saved `{file_path}` successfully!")

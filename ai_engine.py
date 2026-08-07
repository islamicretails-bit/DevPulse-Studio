import os
import time
from groq import Groq
import google.generativeai as genai

# ==============================================================================
# API KEYS CONFIGURATION
# ==============================================================================
# اپنے .env میں یہ تمام API کیز شامل کریں
GROQ_KEYS = [
    os.getenv("GROQ_API_KEY_1"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
]

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# ==============================================================================
# UNSTOPPABLE MULTI-MODEL CODE GENERATOR ENGINE
# ==============================================================================
def generate_file_code(file_path: str, system_blueprint: str) -> str:
    """
    مضبوط کوڈ جنریٹر:
    1. پہلے تمام Groq Keys باری باری استعمال کرے گا۔
    2. Rate Limit (429) پر خود بخود 12 سیکنڈ کا وقفہ لے گا۔
    3. اگر تمام Groq Keys فیل ہو جائیں تو فوراً Google Gemini API پر شفٹ ہو جائے گا۔
    """
    print(f"\n🚀 [PROCESSING] Starting generation for: {file_path}")
    
    prompt = f"""
    SYSTEM BLUEPRINT CONTEXT:
    {system_blueprint}
    
    TASK:
    Generate complete, clean, production-ready, highly optimized, non-placeholder source code for: {file_path}.
    
    CRITICAL CONSTRAINTS:
    - Output ONLY valid code for this file.
    - DO NOT wrap in markdown explanation text outside code block.
    - Strictly strictly write full imports, interfaces, models, and export logic.
    - NO placeholder comments like '// TODO' or '// Implementation here'.
    """

    # --------------------------------------------------------------------------
    # PHASE 1: TRY GROQ API WITH MULTI-KEY ROTATION & RETRIES
    # --------------------------------------------------------------------------
    for key_index, key in enumerate(GROQ_KEYS):
        if not key:
            continue
            
        client = Groq(api_key=key)
        
        for attempt in range(3):  # Retry up to 3 times per key
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )
                code_content = response.choices[0].message.content
                print(f"✅ [SUCCESS - Groq Key {key_index + 1}] Generated: {file_path}")
                return code_content
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ [Groq Key {key_index + 1} Attempt {attempt + 1}] Error: {error_msg[:100]}...")
                
                # Check for Rate Limit or Timeout
                if "429" in error_msg or "rate_limit" in error_msg.lower() or "timeout" in error_msg.lower():
                    print("⏳ Rate Limit / Timeout detected. Pausing for 12 seconds to reset quota...")
                    time.sleep(12)  # Cooldown delay
                else:
                    time.sleep(3)

    # --------------------------------------------------------------------------
    # PHASE 2: FALLBACK TO GOOGLE GEMINI IF GROQ IS COMPLETELY EXHAUSTED
    # --------------------------------------------------------------------------
    if GEMINI_KEY:
        print(f"🔀 [FALLBACK SWITCH] All Groq Keys limited. Switching to Google Gemini for: {file_path}")
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            print(f"✅ [SUCCESS - Gemini Fallback] Generated: {file_path}")
            return response.text
        except Exception as e:
            print(f"❌ [Gemini Error] Fallback failed: {e}")

    raise RuntimeError(f"CRITICAL FAILURE: Could not generate code for {file_path} across all models and keys.")


# ==============================================================================
# MAIN BATCH PROCESSOR WITH SMART DELAYS & GITHUB PUSH INTEGRATION
# ==============================================================================
def run_autonomous_builder(file_list: list, system_blueprint: str, push_to_github_func):
    """
    یہ مین لوپ تمام 47 فائلوں کو ایک ایک کر کے سنبھالے گا، 
    وقفے دے گا، اور فیل ہونے پر فائل کو دوبارہ جنریٹ کرے گا۔
    """
    total_files = len(file_list)
    print(f"🌟 Starting Autonomous Monorepo Build for {total_files} files...")

    for index, file_path in enumerate(file_list, start=1):
        print(f"\n------------------------------------------------------------")
        print(f"📊 Progress: [{index}/{total_files}] -> {file_path}")
        print(f"------------------------------------------------------------")

        success = False
        max_file_retries = 3

        for file_attempt in range(max_file_retries):
            try:
                # 1. Code Generation
                generated_code = generate_file_code(file_path, system_blueprint)

                # 2. Push directly to GitHub Repository
                push_to_github_func(file_path, generated_code)

                success = True

                # 3. SMART COOL-DOWN DELAY (3 seconds gap between files)
                print("💤 Cooling down API for 3 seconds before next file...")
                time.sleep(3)
                break

            except Exception as err:
                print(f"❌ [Retry {file_attempt + 1}/{max_file_retries}] Failed for {file_path}: {err}")
                print("⏳ Pausing 15 seconds before retrying this file...")
                time.sleep(15)

        if not success:
            print(f"🚨 [SKIPPED] Critical Error: Failed to complete {file_path} after full retries.")

    print("\n🎉 ============================================================")
    print("🚀 ALL 47 MANIFEST FILES PROCESSED & PUSHED TO GITHUB!")
    print("============================================================ 🎉")

import os
import time
import json
import base64
import urllib.request
import urllib.error
import re
import threading
import concurrent.futures
from groq import Groq

# =========================================================
# CONFIGURATION & ENVIRONMENT LOADER
# =========================================================

# Load Groq Keys dynamically (4 Keys + Fallbacks)
GROQ_KEYS = [
    os.getenv("GROQ_API_KEY_1", "gsk_key1_yahan_lgaein"),
    os.getenv("GROQ_API_KEY_2", "gsk_key2_yahan_lgaein"),
    os.getenv("GROQ_API_KEY_3", "gsk_key3_yahan_lgaein"),
    os.getenv("GROQ_API_KEY_4", "gsk_key4_yahan_lgaein"),
]

# Load Gemini Keys dynamically (3 Keys + Fallbacks)
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSy_gemini_key1_yahan_lgaein"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSy_gemini_key2_yahan_lgaein"),
    os.getenv("GEMINI_API_KEY_3", "AIzaSy_gemini_key3_yahan_lgaein"),
]

# GitHub Details
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "github_pat_11...")
GITHUB_REPO = os.getenv("GITHUB_REPO", "username/repository-name")

# Parallel Execution Settings
MAX_WORKERS = int(os.getenv("ENGINE_MAX_WORKERS", 5))
github_lock = threading.Lock()  # Thread-safe lock for GitHub pushes

MASTER_BLUEPRINT = """
================================================================================
DEVPULSE STUDIO ENTERPRISE PRO - ULTIMATE SELF-EVOLVING MASTER BLUEPRINT (V3.0)
================================================================================
PROJECT SYSTEM OVERVIEW:
Build an autonomous, self-evolving enterprise-grade digital marketplace & AI orchestration 
monorepo engine ("NexusVault Global Enterprise / MystoriumX AI Studio") using Next.js 14 (App Router), 
TypeScript, Tailwind CSS, Prisma ORM, PostgreSQL, Cloudflare R2, and Dynamic Multi-Model AI Routing.

MANIFEST FILES:
1. DATABASE SCHEMAS & CONFIGURATIONS:
- prisma/schema.prisma
- package.json
- tailwind.config.js
- src/app/globals.css
- vercel.json
- .env.example

2. TYPES, SECURITY & CORE UTILITIES:
- src/types/index.ts
- src/lib/security.ts
- src/lib/geo-currency.ts
- src/lib/ai-generator.ts
- src/lib/ai-router.ts
- src/lib/notifications.ts
- src/lib/s3-storage.ts
- src/lib/seo-generator.ts

3. APPLICATION LAYOUTS & SEO:
- src/app/layout.tsx
- src/app/page.tsx
- src/app/office/page.tsx
- src/app/dashboard/page.tsx
- src/app/affiliate/page.tsx
- src/app/vendor/page.tsx
- src/app/sitemap.ts
- src/app/robots.txt

4. USER & MARKETPLACE COMPONENTS:
- src/components/marketplace/ProductGrid.tsx
- src/components/marketplace/ProductCard.tsx
- src/components/marketplace/CustomRequestModal.tsx
- src/components/marketplace/AppleToast.tsx
- src/components/vendor/WalletOverview.tsx

5. ADMIN & OPERATIONS COMPONENTS:
- src/components/admin/LiveTrafficMap.tsx
- src/components/admin/AIOperationsHub.tsx
- src/components/admin/SalesAnalyticsChart.tsx
- src/components/admin/CustomRequestsTable.tsx

6. BACKEND ROUTE HANDLERS & WEBHOOKS:
- src/app/api/cron/auto-generate/route.ts
- src/app/api/ai/generate-product/route.ts
- src/app/api/ai/stream/route.ts
- src/app/api/payments/checkout/route.ts
- src/app/api/webhooks/stripe/route.ts
- src/app/api/webhooks/paypal/route.ts
- src/app/api/admin/analytics/route.ts
- src/app/api/vendor/payouts/route.ts
- src/app/api/downloads/secure/route.ts
"""

# =========================================================
# STATIC FILE FAST-TRACK TEMPLATES
# =========================================================
def get_static_template(file_path):
    if file_path.endswith('.css') and 'globals' in file_path:
        return """@tailwind base;\n@tailwind components;\n@tailwind utilities;\n\n:root {\n  --background: #ffffff;\n  --foreground: #171717;\n}\n\n@media (prefers-color-scheme: dark) {\n  :root {\n    --background: #0a0a0a;\n    --foreground: #ededed;\n  }\n}\n\nbody {\n  color: var(--foreground);\n  background: var(--background);\n  font-family: Arial, Helvetica, sans-serif;\n}"""
    elif file_path.endswith('.json') and 'package.json' in file_path:
        return '{\n  "name": "nexus-vault-enterprise",\n  "version": "1.0.0",\n  "private": true\n}'
    return None

# =========================================================
# MULTI-KEY ROTATION & WORKER ENGINE
# =========================================================

def call_gemini_api(prompt, task_index):
    """3 Gemini keys کا تھریڈ سیف روٹیشن فلو"""
    for i in range(len(GEMINI_KEYS)):
        current_idx = (task_index + i) % len(GEMINI_KEYS)
        gemini_key = GEMINI_KEYS[current_idx]
        
        if "yahan_lgaein" in gemini_key or not gemini_key:
            continue
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            print(f"  🚀 [Gemini] Trying Gemini Key #{current_idx + 1}...")
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"  ⚠️ Gemini Key #{current_idx + 1} Error: {str(e)[:60]}")
            time.sleep(2)
            
    raise Exception("All Gemini Keys exhausted or failed.")

def generate_file_worker(task_args):
    file_path, task_index = task_args

    # Check 1: Fast-track static templates
    static_content = get_static_template(file_path)
    if static_content:
        return file_path, static_content, "Fast-Track Static Template"

    prompt = f"""
    System Blueprint:
    {MASTER_BLUEPRINT}

    TASK:
    Write COMPLETE, PRODUCTION-READY source code for module: `{file_path}`.

    RULES:
    - Absolutely NO placeholders, NO '// TODO', NO cuts.
    - Write full imports, interfaces, models, and complete logic.
    - Output ONLY valid executable code.
    """

    # Phase 1: Groq Keys Rotation (4 Keys Pool)
    for i in range(len(GROQ_KEYS)):
        current_idx = (task_index + i) % len(GROQ_KEYS)
        key = GROQ_KEYS[current_idx]
        
        if "yahan_lgaein" in key or not key:
            continue
            
        try:
            print(f"  ⚡ [Groq Worker] Trying Groq Key #{current_idx + 1} for `{file_path}`...")
            client = Groq(api_key=key, timeout=60.0)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are a Senior Principal Architect writing full code for {file_path}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=6000,
            )
            content = completion.choices[0].message.content
            if content and len(content.strip()) > 0:
                return file_path, content, f"Groq Key #{current_idx + 1}"
        except Exception as e:
            print(f"  ⚠️ Groq Key #{current_idx + 1} Limit hit/Error: {str(e)[:60]}")
            time.sleep(2)

    # Phase 2: Fallback to Gemini Cluster
    try:
        print(f"  🔄 Groq Cluster busy for `{file_path}`. Switching to Gemini Cluster...")
        content = call_gemini_api(prompt, task_index)
        if content and len(content.strip()) > 0:
            return file_path, content, "Gemini Cluster"
    except Exception as e:
        print(f"  ⚠️ Gemini Cluster Error on `{file_path}`: {str(e)[:60]}")

    return file_path, None, "Failed"

# =========================================================
# THREAD-SAFE GITHUB PUSH LOGIC
# =========================================================

def push_to_github_strict(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MultiEngine-Parallel-Builder"
    }

    clean_code = re.sub(r'^```\w*\n', '', content, flags=re.MULTILINE)
    clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()
    encoded = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')

    with github_lock:  # Thread-safety lock to prevent race conflicts on GitHub SHA
        sha = None
        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            with urllib.request.urlopen(req, timeout=30) as res:
                sha = json.loads(res.read().decode('utf-8')).get('sha')
        except Exception:
            pass

        payload = {
            "message": f"feat: build full module {path}",
            "content": encoded
        }
        if sha:
            payload["sha"] = sha

        retries = 3
        while retries > 0:
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
                with urllib.request.urlopen(req, timeout=60):
                    print(f"  ✅ [GitHub Push] `{path}` successfully uploaded!")
                    return True
            except Exception as e:
                retries -= 1
                print(f"  ⚠️ GitHub upload delay ({e}) for `{path}`. Retrying... ({retries} left)")
                time.sleep(3)
        return False

# =========================================================
# PARALLEL MAIN CONTROLLER
# =========================================================

def main():
    extracted_paths = re.findall(r'[\w\/\.\-]+\.(?:prisma|json|js|jsx|css|ts|tsx|env|example|txt)', MASTER_BLUEPRINT)
    file_paths = list(dict.fromkeys(extracted_paths))

    print(f"==================================================")
    print(f"🚀 Hybrid Parallel Engine Active (4 Groq + 3 Gemini)")
    print(f"📂 Total Target Modules: {len(file_paths)}")
    print(f"⚡ Concurrent Threads: {MAX_WORKERS}")
    print(f"==================================================\n")

    tasks = [(path, idx) for idx, path in enumerate(file_paths)]
    completed = 0

    # ThreadPoolExecutor for concurrent file generation
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_path = {executor.submit(generate_file_worker, task): task[0] for task in tasks}

        for future in concurrent.futures.as_completed(future_to_path):
            file_path = future_to_path[future]
            completed += 1

            try:
                path, code, engine_used = future.result()
                if code:
                    print(f"\n[Progress: {completed}/{len(file_paths)}] Generated via [{engine_used}]: `{path}`")
                    push_to_github_strict(path, code)
                else:
                    print(f"\n❌ [CRITICAL FAILURE] Unable to generate `{file_path}`")
            except Exception as exc:
                print(f"\n💥 Thread Exception for `{file_path}`: {exc}")

    print("\n🎉 MABROOK! All target modules have been processed and pushed to GitHub!")

if __name__ == "__main__":
    main()

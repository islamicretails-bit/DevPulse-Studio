import os
import time
import json
import base64
import urllib.request
import urllib.error
import re
from groq import Groq

# =========================================================
# CONFIGURATION - اپنی تمام 7 کیز اور GitHub تفصیلات یہاں درج کریں
# =========================================================

# 1. Groq API Keys (4 Keys)
GROQ_KEYS = [
    "gsk_key1_yahan_lgaein",
    "gsk_key2_yahan_lgaein",
    "gsk_key3_yahan_lgaein",
    "gsk_key4_yahan_lgaein"
]

# 2. Gemini API Keys (3 Keys)
GEMINI_KEYS = [
    "AIzaSy_gemini_key1_yahan_lgaein",
    "AIzaSy_gemini_key2_yahan_lgaein",
    "AIzaSy_gemini_key3_yahan_lgaein"
]

# 3. GitHub Setup
GITHUB_TOKEN = "github_pat_11..."        # اپنا Personal Access Token
GITHUB_REPO = "username/repository-name" # اپنی Repo کا نام (مثلاً: username/nexusvault)

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
# MULTI-KEY ROTATION LOGIC
# =========================================================
current_groq_idx = 0
current_gemini_idx = 0

def call_gemini_api(prompt):
    """3 Gemini keys کا روٹیشن فلو"""
    global current_gemini_idx
    
    for _ in range(len(GEMINI_KEYS)):
        gemini_key = GEMINI_KEYS[current_gemini_idx]
        key_num = current_gemini_idx + 1
        current_gemini_idx = (current_gemini_idx + 1) % len(GEMINI_KEYS)
        
        if "yahan_lgaein" in gemini_key:
            continue
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            print(f"  🚀 [Gemini] Trying Gemini Key #{key_num}...")
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"  ⚠️ Gemini Key #{key_num} Error: {str(e)[:60]}")
            
    raise Exception("All Gemini Keys exhausted or failed.")

def generate_file_code(file_path):
    global current_groq_idx
    prompt = f"""
    System Blueprint:
    {MASTER_BLUEPRINT}

    TASK:
    Write COMPLETE, PRODUCTION-READY source code for module: `{file_path}`.

    RULES:
    - Absolutely NO placeholders, NO '// TODO', NO cuts.
    - Write full imports, interfaces, models, and complete logic.
    - Output ONLY valid executable code inside markdown blocks.
    """

    # 1. Try Groq Keys Rotation (4 Keys)
    for _ in range(len(GROQ_KEYS)):
        key = GROQ_KEYS[current_groq_idx]
        key_num = current_groq_idx + 1
        current_groq_idx = (current_groq_idx + 1) % len(GROQ_KEYS)
        
        if "yahan_lgaein" in key:
            continue
            
        try:
            print(f"  ⚡ [Groq] Trying Groq Key #{key_num} for `{file_path}`...")
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
                return content
        except Exception as e:
            print(f"  ⚠️ Groq Key #{key_num} Limit hit/Error: {str(e)[:60]}")

    # 2. Fallback to Gemini Keys Rotation (3 Keys)
    try:
        print(f"  🔄 Groq Keys busy. Switching to Gemini Cluster...")
        content = call_gemini_api(prompt)
        if content and len(content.strip()) > 0:
            return content
    except Exception as e:
        print(f"  ⚠️ Gemini Cluster Error: {str(e)[:60]}")

    # 3. Complete Standby Pause if all 7 keys hit rate limits at the same time
    print("  💤 All 7 API keys hit rate limits. Pause for 20 seconds...")
    time.sleep(20)
    return generate_file_code(file_path)

def push_to_github_strict(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MultiEngine-Builder"
    }

    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req, timeout=30) as res:
            sha = json.loads(res.read().decode('utf-8')).get('sha')
    except Exception:
        pass

    clean_code = re.sub(r'^```\w*\n', '', content, flags=re.MULTILINE)
    clean_code = re.sub(r'\n```$', '', clean_code, flags=re.MULTILINE).strip()
    
    encoded = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')
    payload = {
        "message": f"feat: build full module {path}",
        "content": encoded
    }
    if sha:
        payload["sha"] = sha

    while True:
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=60):
                print(f"  ✅ [GitHub Push] `{path}` successfully uploaded!")
                return True
        except Exception as e:
            print(f"  ⚠️ GitHub upload delay ({e}). Retrying in 5s...")
            time.sleep(5)

def main():
    extracted_paths = re.findall(r'[\w\/\.\-]+\.(?:prisma|json|js|jsx|css|ts|tsx|env|example|txt)', MASTER_BLUEPRINT)
    file_paths = list(dict.fromkeys(extracted_paths))

    print(f"==================================================")
    print(f"🚀 Hybrid Build Engine Active (4 Groq + 3 Gemini)")
    print(f"📂 Total Target Modules: {len(file_paths)}")
    print(f"==================================================\n")

    for idx, path in enumerate(file_paths):
        print(f"[{idx+1}/{len(file_paths)}] Building Module: {path}")
        code = generate_file_code(path)
        push_to_github_strict(path, code)
        print("  ⏱️ Quick pause (5s)...\n")
        time.sleep(5)

    print("\n🎉 MABROOK! All 38 modules have been successfully generated and pushed to GitHub!")

if __name__ == "__main__":
    main()

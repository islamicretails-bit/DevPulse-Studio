# ⚡ DevPulse Studio Pro

**DevPulse Studio Pro** ایک انتہائی خودکار، ملٹی ایجنٹ (Autonomous Multi-Agent) AI کوڈ جنریشن انجن اور لائیو ڈیش بورڈ ہے۔ یہ سسٹم پیچیدہ سافٹ ویئر پرامپٹس کو سمجھ کر خودکار طریقے سے پروجیکٹ کا آرکیٹیکچر ڈیزائن کرتا ہے، پروڈکشن گریڈ سورس کوڈ لکھتا ہے، یونٹ ٹیسٹس (Unit Tests) جنریٹ کرتا ہے، اور فائلیں براہِ راست آپ کی **GitHub Repository** میں کمیٹ (Commit) اور پش (Push) کرتا ہے۔

---

## 🌟 بنیادی فیچرز (Key Features)

- 🤖 **Autonomous Multi-Agent Architecture:**
  - **ArchitectAgent:** پروجیکٹ کی ضروریات کا تجزیہ کرتا ہے اور فائل اسٹرکچر/بلیو پرنٹ تیار کرتا ہے۔
  - **CoderAgent:** پروڈکشن گریڈ سورس کوڈ تیار کرتا ہے۔
  - **TesterAgent:** جنریٹ شدہ کوڈ کے لیے خودکار Jest/Vitest یونٹ ٹیسٹس لکھتا ہے۔
  - **GitHubAgent:** جنریٹ شدہ پروجیکٹ فائلوں کو خود بخود GitHub پر پش اور اپ لوڈ کرتا ہے۔
- 🐙 **Direct GitHub Integration:**
  - GitHub Personal Access Token (PAT) کے ذریعے رپوزٹری میں آٹومیٹک یا مینوئل کمیٹ۔
- 🔑 **Multi-Key Rotation & Failover Engine:**
  - Multiple API Keys (Groq / OpenAI) کا پول تاکہ Rate Limits اور Quota Errors کا سامنا نہ کرنا پڑے۔
  - خودکار Failover اور Retry میکانزم۔
- ⏸️ **Interactive Control Pipeline:**
  - لائیو ایگزیکیوشن لاگز اور ریئل ٹائم پروگریس مانیٹرنگ۔
  - ایگزیکیوشن پاز (Pause)، ریزیوم (Resume) اور کینسل کرنے کے کنٹرولز۔
- 📦 **One-Click Export & Zip:**
  - جنریٹ شدہ پروجیکٹ فائلز کو دیکھنا (File Viewer) اور ایک کلک پر `.zip` فارمیٹ میں ڈاؤن لوڈ کرنا۔
- ☁️ **Streamlit Cloud Ready:**
  - Streamlit Cloud Secrets اور local `.env` دونوں کے ساتھ مکمل مطابقت۔

---

## 📁 پروجیکٹ کا اسٹرکچر (Repository Architecture)

```text
devpulse-studio-pro/
├── packages/
│   └── engine/                   # Core Engine (TypeScript)
│       ├── src/
│       │   ├── agents/           # ArchitectAgent, CoderAgent, TesterAgent
│       │   ├── services/         # ApiKeyRotator, RateLimitHandler
│       │   └── types/            # Engine Data Interfaces & Types
│       └── index.ts              # Core Exports
├── app.py                        # Streamlit Interactive Web Application
├── requirements.txt              # Python Dependencies for Streamlit
├── package.json                  # Node.js Monorepo Workspace Configuration
├── .env.example                  # Environment Variables Template
└── README.md                     # Project Documentation

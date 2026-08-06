"""
DevPulse Studio - AI Code Reviewer & Auditor Agent
Performs comprehensive post-generation quality audits, security scans, and structural reviews.
"""

import google.generativeai as genai
from typing import Dict, Any, List
from config import logger, config


class AIReviewer:
    """
    Enterprise Security & Code Auditor Agent powered by Gemini 1.5 Flash.
    Provides automated quality analysis, security vulnerability audits, and optimization guidelines.
    """

    def __init__(self, api_key: str):
        """
        AI Reviewer کو Gemini API Key کے ساتھ انیشلائز کریں۔
        """
        if not api_key or not api_key.strip():
            raise ValueError("AI Reviewer ایجنٹ کو فعال کرنے کے لیے Gemini API Key لازمی ہے۔")
        
        self.api_key = api_key.strip()
        genai.configure(api_key=self.api_key)
        
        # High-speed model for code review and auditing
        self.model = genai.GenerativeModel(
            model_name=config.gemini.reviewer_model,
            generation_config=config.gemini.get_generation_config()
        )
        logger.info("AI Reviewer Agent (Security & QA Engine) کامیابی سے انیشلائز ہو گیا۔")

    def audit_project(
        self, 
        project_name: str, 
        requirements: str, 
        project_plan: Dict[str, Any],
        repo_url: str
    ) -> str:
        """
        پروجیکٹ کے اسٹرکچر اور ریکوائرمنٹس کا تجزیہ کر کے سیکیورٹی اور کوالٹی آڈٹ رپورٹ تیار کرتا ہے۔
        """
        logger.info(f"پروجیکٹ '{project_name}' کے لیے سیکیورٹی اور کوالٹی ریویو کیا جا رہا ہے...")

        files_summary = "\n".join([f"- {f.get('path')}: {f.get('purpose')}" for f in project_plan.get("files", [])])
        
        system_prompt = f"""
You are an Enterprise Lead Security Auditor & QA Engineer.
Review the newly built automated repository and provide an executive evaluation report.

PROJECT NAME: "{project_name}"
ORIGINAL REQUIREMENTS: "{requirements}"
REPOSITORY URL: {repo_url}
GENERATED ARCHITECTURE FILES:
{files_summary}

YOUR TASK:
Generate a clean, structured, and professional Markdown Audit Report.

Include the following sections in your report:
1. 🛡️ Executive Security Summary (OWASP standards, credential handling, API isolation check)
2. ⚡ Performance & Scalability Score (Architecture rating out of 10)
3. 🛠️ Code Maintainability & Modularity (Clean Code principles assessment)
4. 🚀 Next Steps & Hosting Recommendations (How to deploy to Render, Vercel, Streamlit, or Cloud providers)

Do NOT return JSON. Return markdown text directly with appropriate headers and clear bullet points.
"""

        try:
            response = self.model.generate_content(system_prompt)
            review_report = response.text.strip()
            logger.info("سیکیورٹی اور کوالٹی ریویو پورٹ کامیابی سے تیار ہو گئی۔")
            return review_report

        except Exception as e:
            logger.error(f"AI Reviewer Audit Failure: {str(e)}")
            return f"### ⚠️ Review Audit Unavailable\n\nریویو رپورٹ تیار کرتے وقت درج ذیل مسئلہ پیش آیا: {str(e)}"

"""
DevPulse Studio - AI System Architect Agent
Analyzes natural language requests and engineers complete project blueprints, schemas, and directory structures.
"""

import json
import google.generativeai as genai
from typing import Dict, Any, List
from config import logger, config


class AIArchitect:
    """
    Enterprise Software Architect Agent powered by Gemini 1.5 Pro.
    Generates scalable project file trees, component splits, and structural specs.
    """

    def __init__(self, api_key: str):
        """
        AI Architect کو Gemini API Key کے ساتھ انیشلائز کریں۔
        """
        if not api_key or not api_key.strip():
            raise ValueError("AI Architect ایجنٹ کو فعال کرنے کے لیے Gemini API Key لازمی ہے۔")
        
        self.api_key = api_key.strip()
        genai.configure(api_key=self.api_key)
        
        # High-reasoning model for system planning
        self.model = genai.GenerativeModel(
            model_name=config.gemini.architect_model,
            generation_config=config.gemini.get_generation_config()
        )
        logger.info("AI Architect Agent کامیابی سے انیشلائز ہو گیا۔")

    def plan_project(self, project_name: str, requirements: str) -> Dict[str, Any]:
        """
        پروجیکٹ کی ضرورت کا مکمل جائزہ لے کر اسٹرکچرڈ JSON پروجیکٹ میپ جنریٹ کرتا ہے۔
        """
        logger.info(f"پروجیکٹ '{project_name}' کے لیے آرکیٹیکچر کا منصوبہ بنایا جا رہا ہے...")
        
        system_prompt = f"""
You are a World-Class Senior Principal Software Architect.
Your mission is to design a production-grade, enterprise-ready repository blueprint for the project requested by the user.

PROJECT NAME: "{project_name}"
PROJECT REQUIREMENTS:
"{requirements}"

INSTRUCTIONS:
1. Analyze the full scope. Whether it's a massive platform (like YouTube, Netflix, SaaS, CRM) or a complex tool, design all required layers:
   - Configuration & Environment
   - Data Models & Database Schemas
   - Core Business Logic & Controllers
   - API Routes / Backend Services
   - Frontend Interfaces / UI Components
   - Authentication, Security, Middleware & Utility Helpers
   - Testing & Deployment Scripts (Docker, CI/CD, README)

2. Divide the system into clean, logical file paths with absolute precision.

3. You MUST respond STRICTLY with valid JSON. Do not include markdown backticks like ```json or ```. Return pure JSON only.

JSON STRUCTURE REQUIREMENTS:
{{
    "project_name": "{project_name}",
    "architecture_style": "Clean Architecture / Microservices / Full-Stack Enterprise",
    "summary": "High-level functional breakdown of the engineered architecture.",
    "files": [
        {{
            "path": "relative/path/to/file.ext",
            "purpose": "Precise description of what this specific file will implement."
        }}
    ]
}}
"""

        try:
            response = self.model.generate_content(system_prompt)
            raw_text = response.text.strip()
            
            # Clean possible Markdown formatting if model emits it
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
            
            project_plan = json.loads(raw_text)
            
            # Validation check
            if "files" not in project_plan or not isinstance(project_plan["files"], list):
                raise ValueError("AI Architect کا جواب JSON اسٹرکچر کے معیار پر پورا نہیں اترا۔")

            logger.info(f"آرکیٹیکچر مکمل تیار ہو گیا۔ کل فائلز کی تعداد: {len(project_plan['files'])}")
            return project_plan

        except json.JSONDecodeError as jde:
            logger.error(f"JSON Parsing Error in Architect Response: {str(jde)}")
            raise Exception("AI Architect کا جواب درست JSON فارمیٹ میں نہیں مل سکا، دوبارہ کوشش کریں۔")
        except Exception as e:
            logger.error(f"AI Architect Failure: {str(e)}")
            raise Exception(f"پروجیکٹ آرکیٹیکچر پلان بنانے میں مسئلہ پیش آیا: {str(e)}")

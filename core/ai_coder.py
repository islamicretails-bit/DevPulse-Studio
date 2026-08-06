"""
DevPulse Studio - AI Deep Coder Agent
Generates zero-placeholder, production-grade, fully functional code implementation for every targeted architecture file.
"""

import google.generativeai as genai
from config import logger, config


class AICoder:
    """
    Principal Software Engineer Agent powered by Gemini 1.5 Pro.
    Generates strict, fully realized enterprise-level codebase implementation.
    """

    def __init__(self, api_key: str):
        """
        AI Coder ایجنٹ کو Gemini API Key کے ساتھ انیشلائز کریں۔
        """
        if not api_key or not api_key.strip():
            raise ValueError("AI Coder ایجنٹ کو فعال کرنے کے لیے Gemini API Key لازمی ہے۔")
        
        self.api_key = api_key.strip()
        genai.configure(api_key=self.api_key)
        
        # Pro model for deep logic generation
        self.model = genai.GenerativeModel(
            model_name=config.gemini.coder_model,
            generation_config=config.gemini.get_generation_config()
        )
        logger.info("AI Coder Agent (Zero-Placeholder Engine) کامیابی سے انیشلائز ہو گیا۔")

    def generate_file_code(
        self, 
        project_name: str, 
        file_path: str, 
        purpose: str, 
        architecture_summary: str,
        all_files_list: list
    ) -> str:
        """
        کسی بھی فائل کا مکمل، تفصیلی اور سیکیور کوڈ تیار کرتا ہے۔
        """
        logger.info(f"فائل '{file_path}' کا ڈیپ کوڈ لکھا جا رہا ہے...")
        
        system_prompt = f"""
You are a Principal Software Engineer writing code for enterprise-grade applications.
Your job is to generate the COMPLETE, fully realized source code for the specified file.

PROJECT: "{project_name}"
ARCHITECTURE OVERVIEW: {architecture_summary}
TARGET FILE PATH: "{file_path}"
FILE INTENDED PURPOSE: {purpose}
COMPLETE REPOSITORY FILE MAP: {all_files_list}

NON-NEGOTIABLE STRICT CODING RULES:
1. Write 100% COMPLETE, fully operational code.
2. ABSOLUTELY ZERO shortcuts, ZERO placeholders, ZERO 'TODO' comments, ZERO 'insert implementation here', and ZERO truncated arrays/logic.
3. Write clean, robust, enterprise-grade code with error handling, logging, docstrings, type hints, and full business logic.
4. Ensure imports align seamlessly with the provided repository file map so files interconnect cleanly.
5. Return ONLY the raw file source code. Do NOT wrap it in markdown code fences (do NOT use ```python or ```). Do NOT include conversational preambles or postscripts.
"""

        try:
            response = self.model.generate_content(system_prompt)
            raw_code = response.text.strip()
            
            # Clean markdown code block boundaries if emitted by model
            if raw_code.startswith("```"):
                lines = raw_code.splitlines()
                # Remove top line like ```python
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove bottom closing line ```
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_code = "\n".join(lines).strip()

            logger.info(f"فائل '{file_path}' کا کوڈ کامیابی سے تیار ہو گیا۔ (طوالت: {len(raw_code)} حروف)")
            return raw_code

        except Exception as e:
            logger.error(f"فائل '{file_path}' کا کوڈ بنانے میں ناکامی: {str(e)}")
            raise Exception(f"AI Coder Engine ایرر ({file_path}): {str(e)}")

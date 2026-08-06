"""
DevPulse Studio - Global Configuration Engine
Enterprise-Grade Settings, System Limits & Environment Management
"""

import os
import logging
from typing import Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Environment Variables لوڈ کریں
load_dotenv()


def setup_logger(name: str = "DevPulseLogger") -> logging.Logger:
    """
    پورے DevPulse Studio کے لیے لائیو لاگنگ اسٹرکچر قائم کرتا ہے۔
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger


# Global System Logger
logger = setup_logger()


@dataclass
class GeminiModelConfig:
    """
    Gemini AI Models کی مکمل پیرامیٹر ترتیب
    """
    architect_model: str = "gemini-1.5-pro"
    coder_model: str = "gemini-1.5-pro"
    reviewer_model: str = "gemini-1.5-flash"
    
    # Advanced AI Generation Parameters
    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        AI جنریشن کی سیٹنگز فراہم کرتا ہے۔
        """
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
        }


@dataclass
class GitHubConfig:
    """
    GitHub API اور Repository کی سیٹنگز
    """
    default_branch: str = "main"
    max_retries: int = 3
    retry_delay_seconds: int = 2
    commit_author_name: str = "DevPulse Studio Bot"
    commit_author_email: str = "bot@devpulse.studio"


@dataclass
class DevPulseConfig:
    """
    DevPulse Studio کا مرکزی کنفیگریشن ڈیٹا اسٹرکچر
    """
    app_name: str = "DevPulse Studio"
    version: str = "1.0.0 Enterprise"
    author: str = "Enterprise AI Developer"
    
    # Model & GitHub Settings
    gemini: GeminiModelConfig = field(default_factory=GeminiModelConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    
    # Security Credentials Container
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))

    def validate_keys(self, custom_gemini_key: str = "", custom_github_token: str = "") -> bool:
        """
        چیک کرتا ہے کہ آیا سیشن یا انوائرنمنٹ میں API کیز موجود ہیں یا نہیں۔
        """
        active_gemini = custom_gemini_key or self.gemini_api_key
        active_github = custom_github_token or self.github_token
        
        if not active_gemini or not active_github:
            logger.warning("سیکیورٹی الرٹ: Gemini API Key یا GitHub Token غائب ہے۔")
            return False
        return True


# Global Singleton Instance
config = DevPulseConfig()

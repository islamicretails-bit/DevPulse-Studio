"""
DevPulse Studio - GitHub Integration Engine
Handles automated repository creation, branch initialization, file commits, and tree management.
"""

import time
import base64
from typing import Optional, Dict, Any
from github import Github, GithubException, UnknownObjectException
from config import logger, GitHubConfig, config


class GitHubManager:
    """
    Enterprise-grade GitHub API Automation Interface.
    Manages direct interactions with GitHub repositories.
    """

    def __init__(self, access_token: str):
        """
        GitHub Client کو فراہم کردہ Access Token کے ساتھ انیشلائز کریں۔
        """
        if not access_token or not access_token.strip():
            raise ValueError("ایک درست GitHub Access Token فراہم کرنا لازمی ہے۔")
        
        self.access_token = access_token.strip()
        self.github_client = Github(self.access_token)
        self.gh_config = config.github
        
        try:
            self.user = self.github_client.get_user()
            logger.info(f"GitHub Auth کامیابی سے قائم ہو گئی۔ صارف: {self.user.login}")
        except GithubException as e:
            logger.error(f"GitHub Authenticate کرنے میں ناکامی: {str(e)}")
            raise Exception(f"GitHub Token کی تصدیق ناکام ہو گئی: {str(e)}")

    def create_repository(self, repo_name: str, description: str = "", private: bool = False) -> Any:
        """
        صارف کے گٹ ہب اکاؤنٹ پر نئی ریپوزیٹری بناتا ہے یا موجودہ کو حاصل کرتا ہے۔
        """
        clean_repo_name = repo_name.strip().replace(" ", "-").lower()
        
        try:
            logger.info(f"GitHub پر نئی ریپوزیٹری بنائی جا رہی ہے: '{clean_repo_name}'")
            repo = self.user.create_repo(
                name=clean_repo_name,
                description=description or "DevPulse Studio AI کے ذریعے تیار کردہ خودکار پروجیکٹ",
                private=private,
                auto_init=True  # README.md کے ساتھ انیشلائز کرتا ہے تاکہ main branch قائم ہو جائے
            )
            time.sleep(2)  # API Sync delay
            logger.info(f"ریپوزیٹری کامیابی سے بن گئی: {repo.html_url}")
            return repo
        except GithubException as e:
            if e.status == 422:  # Repo already exists
                logger.warning(f"ریپوزیٹری '{clean_repo_name}' پہلے سے موجود ہے۔ موجودہ Repo حاصل کی جا رہی ہے۔")
                try:
                    return self.user.get_repo(clean_repo_name)
                except Exception as fetch_err:
                    raise Exception(f"موجودہ ریپوزیٹری حاصل نہیں کی جا سکی: {str(fetch_err)}")
            else:
                logger.error(f"GitHub Repo بنانے کے دوران غلطی: {str(e)}")
                raise Exception(f"GitHub Repository بنانے میں ناکامی: {str(e)}")

    def push_file_to_repo(
        self, 
        repo_name: str, 
        file_path: str, 
        content: str, 
        commit_message: Optional[str] = None
    ) -> bool:
        """
        کسی بھی ٹیکسٹ يا کوڈ فائل کو ڈائریکٹ GitHub Repository میں Commit / Update کرتا ہے۔
        """
        clean_repo_name = repo_name.strip().replace(" ", "-").lower()
        clean_file_path = file_path.strip().lstrip("/")
        
        if not commit_message:
            commit_message = f"DevPulse AI: '{clean_file_path}' کی فائل تیار کر کے کمٹ کر دی گئی"

        retry_count = 0
        max_retries = self.gh_config.max_retries

        while retry_count < max_retries:
            try:
                repo = self.user.get_repo(clean_repo_name)
                
                # چیک کریں کہ کیا فائل پہلے سے موجود ہے
                try:
                    existing_file = repo.get_contents(clean_file_path, ref=self.gh_config.default_branch)
                    # اگر فائل موجود ہے تو اپڈیٹ کریں
                    logger.info(f"فائل '{clean_file_path}' کو اپڈیٹ کیا جا رہا ہے...")
                    repo.update_file(
                        path=clean_file_path,
                        message=commit_message,
                        content=content,
                        sha=existing_file.sha,
                        branch=self.gh_config.default_branch
                    )
                except UnknownObjectException:
                    # اگر فائل موجود نہیں ہے تو نئی بنائیں
                    logger.info(f"نئی فائل '{clean_file_path}' جنریٹ کر کے Push کی جا رہی ہے...")
                    repo.create_file(
                        path=clean_file_path,
                        message=commit_message,
                        content=content,
                        branch=self.gh_config.default_branch
                    )
                
                logger.info(f"فائل '{clean_file_path}' کامیابی سے Commit ہو گئی۔")
                return True

            except GithubException as ge:
                retry_count += 1
                logger.warning(f"GitHub Push کی کوشش ناکام ہو گئی ({retry_count}/{max_retries}): {str(ge)}")
                if retry_count >= max_retries:
                    logger.error(f"فائل '{clean_file_path}' Push کرنے کی تمام کوششیں ناکام ہو گئیں۔")
                    raise Exception(f"GitHub Push Error ({clean_file_path}): {str(ge)}")
                time.sleep(self.gh_config.retry_delay_seconds)
            except Exception as e:
                logger.error(f"غیر متوقع خرابی: {str(e)}")
                raise Exception(f"فائل Processing میں ایرر: {str(e)}")

        return False

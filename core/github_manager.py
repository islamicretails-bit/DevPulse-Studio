"""
DevPulse Studio - Enterprise GitHub Manager Module
Handles automatic repository creation, file updates, commit control, and empty repo handling.
"""

import logging
from github import Github, GithubException

# App-wide Logger Setup
logger = logging.getLogger("DevPulseStudio")

class GitHubManager:
    """
    Manages all interactions with the GitHub REST API using PyGithub.
    """
    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("GitHub Access Token is required.")
        
        self.access_token = access_token.strip()
        self.github = Github(self.access_token)
        self.user = self.github.get_user()

    def create_repository(self, repo_name: str, description: str = "", private: bool = False):
        """
        Creates a new GitHub repository or fetches an existing one.
        Uses `auto_init=True` to prevent '404 Repository is empty' errors.
        """
        try:
            logger.info(f"Creating repository: {repo_name}")
            
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=True  # 👈 ریپازیٹری میں خود بخود README.md فائل بنا کر اسے انیشلائز کرتا ہے
            )
            return repo

        except GithubException as e:
            # اگر ریپازیٹری پہلے سے موجود ہو (HTTP 422)
            if e.status == 422:
                logger.warning(f"Repository '{repo_name}' already exists. Fetching existing repository.")
                return self.user.get_repo(repo_name)
            
            logger.error(f"Failed to create repository '{repo_name}': {str(e)}")
            raise e

    def push_file_to_repo(self, repo_name: str, file_path: str, content: str, commit_message: str):
        """
        Safely creates a new file or updates an existing file in the GitHub repository.
        """
        try:
            repo = self.user.get_repo(repo_name)
            
            # پہلے چیک کریں کہ کیا یہ فائل ریپازیٹری میں موجود ہے
            try:
                contents = repo.get_contents(file_path)
                # اگر فائل موجود ہے تو اسے اپ ڈیٹ کریں
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=contents.sha
                )
                logger.info(f"Updated existing file: {file_path}")

            except GithubException as e:
                # اگر فائل نئی ہے (404) یا خالی ریپازیٹری کا ایشو ہے (422)
                if e.status in [404, 422]:
                    repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content
                    )
                    logger.info(f"Created new file: {file_path}")
                else:
                    raise e

        except GithubException as e:
            logger.error(f"Failed to push file '{file_path}' to repository '{repo_name}': {str(e)}")
            raise e

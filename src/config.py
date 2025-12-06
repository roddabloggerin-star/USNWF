import os
from dataclasses import dataclass

@dataclass
class Config:
    # API Keys and Secrets (stored in GitHub Secrets)
    NWS_API_KEY: str = os.environ.get("NWS_API_KEY", "")
    NWS_USER_AGENT: str = os.environ.get("NWS_USER_AGENT", "")
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    BLOGGER_API_KEY: str = os.environ.get("BLOGGER_API_KEY", "")
    BLOGGER_BLOG_ID: str = os.environ.get("BLOGGER_BLOG_ID", "")
    
    # Application Settings
    PUBLISH_TO_BLOGGER: bool = os.environ.get("PUBLISH_TO_BLOGGER", "false").lower() == "true"
    TEST_MODE: bool = not PUBLISH_TO_BLOGGER
    
    # Content Settings
    MIN_WORD_COUNT: int = 1000
    MAX_IMAGE_SIZE_MB: int = 5
    
    # SEO Settings
    META_DESCRIPTION_LENGTH: int = 160
    CANONICAL_URL: str = os.environ.get("CANONICAL_URL", "https://yourblog.blogspot.com")
    
    # Scheduling
    SCHEDULE_INTERVAL_HOURS: int = 2
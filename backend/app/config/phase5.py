"""
Phase 5 Configuration
Advanced features configuration including API keys for new workers and integrations
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Phase5Config(BaseSettings):
    """Configuration for Phase 5 features"""

    # ==================== Academic Research ====================
    SERPAPI_KEY: str = ""  # For Google Scholar ($50/month for 5,000 searches)

    # ==================== Community Intelligence ====================
    REDDIT_CLIENT_ID: str = ""  # Free with Reddit app registration
    REDDIT_CLIENT_SECRET: str = ""  # Free with Reddit app registration

    YOUTUBE_API_KEY: str = ""  # Free 10,000 quota/day from Google Cloud

    USPTO_API_KEY: str = ""  # Optional, free tier available

    # ==================== Integrations ====================
    # Slack
    SLACK_BOT_TOKEN: str = ""  # Optional
    SLACK_WEBHOOK_URL: str = ""  # Optional

    # Email
    SENDGRID_API_KEY: str = ""  # Optional, $15/month for 40k emails
    EMAIL_FROM: str = "research@agent.com"

    # Notion
    NOTION_API_KEY: str = ""  # Optional, free for personal use
    NOTION_DATABASE_ID: str = ""  # Database to save research to

    # ==================== Feature Flags ====================
    # Enable/disable Phase 5B enterprise features
    ENABLE_AUTHENTICATION: bool = False
    ENABLE_RATE_LIMITING: bool = False
    ENABLE_ANALYTICS: bool = True  # Always track for personal use
    ENABLE_MULTI_TENANT: bool = False

    # Phase 5A personal features
    ENABLE_ACADEMIC_WORKER: bool = True
    ENABLE_REDDIT_WORKER: bool = True
    ENABLE_YOUTUBE_WORKER: bool = True
    ENABLE_PATENT_WORKER: bool = True
    ENABLE_FOLLOWUP_CHAT: bool = True
    ENABLE_VISUALIZATIONS: bool = True
    ENABLE_PDF_EXPORT: bool = True
    ENABLE_PERSONALIZATION: bool = True

    # ==================== Personalization ====================
    DEFAULT_DEPTH: str = "standard"  # quick, standard, or deep
    DEFAULT_MAX_SOURCES: int = 30
    DEFAULT_DOMAIN: str = "tech"  # tech, investing, or academic

    # ==================== Cost Tracking ====================
    TRACK_API_COSTS: bool = True
    COST_ALERT_THRESHOLD: float = 100.0  # Alert if monthly cost exceeds this

    # ==================== Advanced Settings ====================
    # Worker timeouts (seconds)
    WORKER_TIMEOUT: int = 30
    MAX_CONCURRENT_WORKERS: int = 10

    # Follow-up chat settings
    MAX_FOLLOWUP_TURNS: int = 5
    FOLLOWUP_CONTEXT_WINDOW: int = 3  # Number of previous Q&A pairs to include

    # Visualization settings
    MAX_CHART_DATA_POINTS: int = 50
    CHART_THEME: str = "light"  # light or dark

    # PDF export settings
    PDF_PAGE_SIZE: str = "A4"  # A4 or Letter
    PDF_FONT_SIZE: int = 11
    INCLUDE_CHARTS_IN_PDF: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
_config: Optional[Phase5Config] = None


def get_phase5_config() -> Phase5Config:
    """Get Phase 5 configuration singleton"""
    global _config
    if _config is None:
        _config = Phase5Config()
    return _config


# Helper functions for feature flags
def is_academic_worker_enabled() -> bool:
    return get_phase5_config().ENABLE_ACADEMIC_WORKER


def is_reddit_worker_enabled() -> bool:
    return get_phase5_config().ENABLE_REDDIT_WORKER


def is_youtube_worker_enabled() -> bool:
    return get_phase5_config().ENABLE_YOUTUBE_WORKER


def is_patent_worker_enabled() -> bool:
    return get_phase5_config().ENABLE_PATENT_WORKER


def is_followup_enabled() -> bool:
    return get_phase5_config().ENABLE_FOLLOWUP_CHAT


def is_visualizations_enabled() -> bool:
    return get_phase5_config().ENABLE_VISUALIZATIONS


def is_pdf_export_enabled() -> bool:
    return get_phase5_config().ENABLE_PDF_EXPORT


def is_personalization_enabled() -> bool:
    return get_phase5_config().ENABLE_PERSONALIZATION


# API key validation
def validate_api_keys() -> dict:
    """
    Validate which API keys are configured
    Returns dict of {service: is_configured}
    """
    config = get_phase5_config()

    return {
        "serpapi": bool(config.SERPAPI_KEY),
        "reddit": bool(config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET),
        "youtube": bool(config.YOUTUBE_API_KEY),
        "uspto": bool(config.USPTO_API_KEY),
        "slack": bool(config.SLACK_BOT_TOKEN or config.SLACK_WEBHOOK_URL),
        "sendgrid": bool(config.SENDGRID_API_KEY),
        "notion": bool(config.NOTION_API_KEY),
    }


def get_missing_api_keys() -> list:
    """Get list of services with missing API keys"""
    validation = validate_api_keys()
    return [service for service, configured in validation.items() if not configured]

"""Configuration module for ChatQuestBot."""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Bot configuration class."""

    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    CHAT_ID: int = int(os.getenv("CHAT_ID", "0"))

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")

    # Operator Configuration
    OPERATOR_IDS: List[int] = [
        int(uid.strip())
        for uid in os.getenv("OPERATOR_IDS", "").split(",")
        if uid.strip()
    ]

    # Scheduler Configuration
    TASK_SCHEDULE_TIMES: List[str] = [
        time.strip()
        for time in os.getenv("TASK_SCHEDULE_TIMES", "10:00,18:00").split(",")
    ]

    # Forum Topic Configuration (Flood)
    FLOOD_THREAD_ID: int = int(os.getenv("FLOOD_THREAD_ID", "0"))

    # Points Configuration
    MAX_DAILY_ACTIVITY_POINTS: int = int(os.getenv("MAX_DAILY_ACTIVITY_POINTS", "200"))
    MIN_MESSAGE_LENGTH: int = int(os.getenv("MIN_MESSAGE_LENGTH", "10"))
    POINTS_PER_WORD: int = int(os.getenv("POINTS_PER_WORD", "1"))

    # Task Points
    TEXT_TASK_POINTS: int = 100
    PHOTO_TASK_POINTS: int = 200
    VIDEO_TASK_POINTS: int = 300

    # Week End Configuration
    WEEK_END_DAY: int = int(os.getenv("WEEK_END_DAY", "6"))  # Sunday
    WEEK_END_TIME: str = os.getenv("WEEK_END_TIME", "20:00")

    # Warnings
    MAX_WARNINGS: int = 3

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not cls.CHAT_ID:
            raise ValueError("CHAT_ID is required")
        if not cls.OPERATOR_IDS:
            raise ValueError("At least one OPERATOR_ID is required")
        return True


# Validate configuration on import
Config.validate()

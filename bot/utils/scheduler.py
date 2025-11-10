"""Scheduler module for automated task sending."""

import logging
import random
import json
from datetime import datetime
from typing import List, Dict
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Database
from config import Config

logger = logging.getLogger(__name__)

db = Database()


def load_tasks() -> List[Dict]:
    """Load tasks from tasks.json file."""
    try:
        with open("data/tasks.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("tasks.json not found!")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing tasks.json: {e}")
        return []


def initialize_tasks():
    """Load tasks from file into database if not already loaded."""
    tasks_data = load_tasks()

    if not tasks_data:
        logger.warning("No tasks loaded from file")
        return

    # Check if tasks are already in database
    existing_tasks = db.get_active_tasks()

    if not existing_tasks:
        logger.info("Initializing tasks in database...")
        for task_data in tasks_data:
            db.add_task(
                text=task_data["text"],
                content_type=task_data["content_type"],
                points=task_data["points"]
            )
        logger.info(f"Loaded {len(tasks_data)} tasks into database")
    else:
        logger.info(f"Database already contains {len(existing_tasks)} tasks")


async def send_random_task(bot: Bot):
    """Send a random task to the chat."""
    tasks = db.get_active_tasks()

    if not tasks:
        logger.error("No active tasks available")
        return

    # Select random task
    task = random.choice(tasks)

    # Get current week info
    now = datetime.now()
    week_number = now.isocalendar()[1]
    year = now.year

    # Record daily task
    daily_task_id = db.add_daily_task(
        task_id=task["task_id"],
        week_number=week_number,
        year=year
    )

    # Prepare task message
    content_type_emoji = {
        "text": "📝",
        "photo": "📷",
        "video": "🎥",
        "mixed": "🎯"
    }

    emoji = content_type_emoji.get(task["content_type"], "🎯")

    message_text = (
        f"{emoji} НОВОЕ ЗАДАНИЕ!\n\n"
        f"{task['text']}\n\n"
        f"💰 Награда: {task['points']} баллов\n"
        f"📊 Тип: {task['content_type']}\n\n"
        f"Ответьте на это сообщение, чтобы выполнить задание!"
    )

    try:
        await bot.send_message(
            chat_id=Config.CHAT_ID,
            text=message_text
        )
        logger.info(f"Task {task['task_id']} sent successfully (daily_task_id: {daily_task_id})")
    except Exception as e:
        logger.error(f"Failed to send task: {e}")


async def send_week_results(bot: Bot):
    """Send week results and determine winners."""
    leaderboard = db.get_leaderboard(limit=10)

    if not leaderboard:
        message = "🏆 Итоги недели\n\nВ эту неделю не было активных участников."
    else:
        message = "🏆 Итоги недели!\n\nТоп участников:\n\n"

        medals = ["🥇", "🥈", "🥉"]
        prizes = [
            "Место в первом ряду 🎟️",
            "Приоритет в питчинге 🗣️",
            "VIP-зона с пуфиками 😎"
        ]

        for idx, user in enumerate(leaderboard, 1):
            medal = medals[idx - 1] if idx <= 3 else f"{idx}️⃣"
            username = user["username"] or user["first_name"]
            points = user["total_points"]

            user_line = f"{medal} @{username} — {points} баллов"

            if idx <= 3:
                user_line += f"\n   🎁 {prizes[idx - 1]}"

            message += user_line + "\n\n"

        message += "\n🎉 Поздравляем победителей!\n\nСпасибо всем за участие!"

    try:
        await bot.send_message(
            chat_id=Config.CHAT_ID,
            text=message
        )
        logger.info("Week results sent successfully")
    except Exception as e:
        logger.error(f"Failed to send week results: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Setup and configure the scheduler."""
    scheduler = AsyncIOScheduler()

    # Schedule tasks sending
    for time_str in Config.TASK_SCHEDULE_TIMES:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            send_random_task,
            CronTrigger(hour=hour, minute=minute),
            args=[bot],
            id=f"task_{time_str}",
            replace_existing=True
        )
        logger.info(f"Scheduled task sending at {time_str}")

    # Schedule week end results
    week_end_hour, week_end_minute = map(int, Config.WEEK_END_TIME.split(":"))
    scheduler.add_job(
        send_week_results,
        CronTrigger(day_of_week=Config.WEEK_END_DAY, hour=week_end_hour, minute=week_end_minute),
        args=[bot],
        id="week_end",
        replace_existing=True
    )
    logger.info(f"Scheduled week end results on day {Config.WEEK_END_DAY} at {Config.WEEK_END_TIME}")

    return scheduler


async def start_scheduler(bot: Bot):
    """Initialize tasks and start scheduler."""
    # Initialize tasks from file
    initialize_tasks()

    # Setup and start scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started successfully")

    return scheduler
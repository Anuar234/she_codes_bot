"""Database module for ChatQuestBot."""

import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database manager for the bot."""

    def __init__(self, db_path: str = "data/bot.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_operator BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    warnings_count INTEGER DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Daily tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    week_number INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)

            # Answers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    daily_task_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    content TEXT,
                    status TEXT DEFAULT 'pending',
                    reviewed_by INTEGER,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (daily_task_id) REFERENCES daily_tasks(id),
                    FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
                )
            """)

            # Points table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS points (
                    point_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    points INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    reference_id INTEGER,
                    week_number INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Chat activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_activity (
                    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    messages_count INTEGER DEFAULT 0,
                    words_count INTEGER DEFAULT 0,
                    points_earned INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, date)
                )
            """)

            # Warnings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    warning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    issued_by INTEGER NOT NULL,
                    reason TEXT,
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (issued_by) REFERENCES users(user_id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_answers_user_status
                ON answers(user_id, status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_points_user_week
                ON points(user_id, week_number, year)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_activity_user_date
                ON chat_activity(user_id, date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_tasks_week
                ON daily_tasks(week_number, year)
            """)

            logger.info("Database initialized successfully")

    # User methods
    def add_user(self, user_id: int, username: str = None, first_name: str = None,
                 last_name: str = None, is_operator: bool = False) -> None:
        """Add or update user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users
                (user_id, username, first_name, last_name, is_operator)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, is_operator))

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        user = self.get_user(user_id)
        return user["is_banned"] if user else False

    # Task methods
    def add_task(self, text: str, content_type: str, points: int) -> int:
        """Add new task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (text, content_type, points)
                VALUES (?, ?, ?)
            """, (text, content_type, points))
            return cursor.lastrowid

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def add_daily_task(self, task_id: int, week_number: int, year: int) -> int:
        """Record a sent daily task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_tasks (task_id, week_number, year)
                VALUES (?, ?, ?)
            """, (task_id, week_number, year))
            return cursor.lastrowid

    def get_current_daily_task(self) -> Optional[Dict[str, Any]]:
        """Get the most recent daily task."""
        now = datetime.now()
        week_number = now.isocalendar()[1]
        year = now.year

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dt.*, t.text, t.content_type, t.points
                FROM daily_tasks dt
                JOIN tasks t ON dt.task_id = t.task_id
                WHERE dt.week_number = ? AND dt.year = ?
                ORDER BY dt.sent_at DESC
                LIMIT 1
            """, (week_number, year))
            row = cursor.fetchone()
            return dict(row) if row else None

    # Answer methods
    def add_answer(self, user_id: int, daily_task_id: int, message_id: int,
                   content_type: str, content: str = None) -> int:
        """Add user answer to a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO answers
                (user_id, daily_task_id, message_id, content_type, content)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, daily_task_id, message_id, content_type, content))
            return cursor.lastrowid

    def update_answer_status(self, answer_id: int, status: str,
                            reviewed_by: int) -> None:
        """Update answer status (approved/rejected)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE answers
                SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE answer_id = ?
            """, (status, reviewed_by, answer_id))

    def get_answer(self, answer_id: int) -> Optional[Dict[str, Any]]:
        """Get answer by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM answers WHERE answer_id = ?", (answer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # Points methods
    def add_points(self, user_id: int, points: int, reason: str,
                   reference_id: int = None) -> None:
        """Add points to user."""
        now = datetime.now()
        week_number = now.isocalendar()[1]
        year = now.year

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO points
                (user_id, points, reason, reference_id, week_number, year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, points, reason, reference_id, week_number, year))

    def get_user_points(self, user_id: int, week_number: int = None,
                       year: int = None) -> int:
        """Get total points for user in a week."""
        if week_number is None or year is None:
            now = datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(points), 0) as total
                FROM points
                WHERE user_id = ? AND week_number = ? AND year = ?
            """, (user_id, week_number, year))
            return cursor.fetchone()["total"]

    def get_leaderboard(self, week_number: int = None, year: int = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by points."""
        if week_number is None or year is None:
            now = datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    u.user_id,
                    u.username,
                    u.first_name,
                    COALESCE(SUM(p.points), 0) as total_points
                FROM users u
                LEFT JOIN points p ON u.user_id = p.user_id
                    AND p.week_number = ? AND p.year = ?
                WHERE u.is_banned = 0
                GROUP BY u.user_id
                HAVING total_points > 0
                ORDER BY total_points DESC
                LIMIT ?
            """, (week_number, year, limit))
            return [dict(row) for row in cursor.fetchall()]

    # Chat activity methods
    def update_chat_activity(self, user_id: int, words_count: int,
                            points: int) -> None:
        """Update daily chat activity for user."""
        today = date.today()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_activity
                (user_id, date, messages_count, words_count, points_earned)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    messages_count = messages_count + 1,
                    words_count = words_count + ?,
                    points_earned = points_earned + ?
            """, (user_id, today, words_count, points, words_count, points))

    def get_daily_activity_points(self, user_id: int) -> int:
        """Get points earned today from chat activity."""
        today = date.today()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(points_earned, 0) as points
                FROM chat_activity
                WHERE user_id = ? AND date = ?
            """, (user_id, today))
            row = cursor.fetchone()
            return row["points"] if row else 0

    # Warning methods
    def add_warning(self, user_id: int, issued_by: int, reason: str = None) -> None:
        """Add warning to user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO warnings (user_id, issued_by, reason)
                VALUES (?, ?, ?)
            """, (user_id, issued_by, reason))

            # Update user warnings count
            cursor.execute("""
                UPDATE users
                SET warnings_count = warnings_count + 1
                WHERE user_id = ?
            """, (user_id,))

            # Check if user should be banned
            cursor.execute("""
                SELECT warnings_count FROM users WHERE user_id = ?
            """, (user_id,))
            warnings = cursor.fetchone()["warnings_count"]

            if warnings >= 3:
                cursor.execute("""
                    UPDATE users SET is_banned = 1 WHERE user_id = ?
                """, (user_id,))

    def get_user_warnings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all warnings for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM warnings
                WHERE user_id = ?
                ORDER BY issued_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    # Statistics methods
    def get_all_users_stats(self, week_number: int = None,
                           year: int = None) -> List[Dict[str, Any]]:
        """Get statistics for all users."""
        if week_number is None or year is None:
            now = datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.is_banned,
                    u.warnings_count,
                    COALESCE(SUM(p.points), 0) as total_points
                FROM users u
                LEFT JOIN points p ON u.user_id = p.user_id
                    AND p.week_number = ? AND p.year = ?
                GROUP BY u.user_id
                ORDER BY total_points DESC
            """, (week_number, year))
            return [dict(row) for row in cursor.fetchall()]
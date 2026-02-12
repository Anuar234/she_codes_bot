"""User handlers for ChatQuestBot."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.enums import ContentType

from database import Database
from config import Config

logger = logging.getLogger(__name__)

router = Router()
db = Database()


def is_private_chat(message: Message) -> bool:
    """Check if message is from private chat."""
    return message.chat.type == "private"


def create_reply_menu_keyboard(is_operator: bool) -> ReplyKeyboardMarkup:
    """Create reply keyboard for main menu."""
    buttons = [
        [KeyboardButton(text="💰 Мои баллы")],
        [KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="📖 Помощь")],
    ]

    if is_operator:
        buttons.append([KeyboardButton(text="🛡 Модерация")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def is_flood_thread(message: Message) -> bool:
    """Check if message is in the Flood forum topic."""
    if message.chat.type not in ("group", "supergroup"):
        return False
    if Config.FLOOD_THREAD_ID <= 0:
        return False
    return message.message_thread_id == Config.FLOOD_THREAD_ID


def is_allowed_group_message(message: Message) -> bool:
    """Allow only Flood topic messages in groups if configured."""
    if message.chat.type in ("group", "supergroup"):
        if Config.FLOOD_THREAD_ID > 0:
            return is_flood_thread(message)
        return True
    return True


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    if not is_private_chat(message):
        return

    user = message.from_user

    # Add user to database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_operator=user.id in Config.OPERATOR_IDS
    )

    await message.answer(
        "🎮 Добро пожаловать в ChatQuestBot!\n\n"
        "Выполняй ежедневные задания, участвуй в обсуждениях и зарабатывай баллы!\n\n"
        "Доступные команды:\n"
        "/my_points - мои баллы\n"
        "/top - топ участников\n"
        "/help - помощь"
    )

    await message.answer(
        "Меню функций:",
        reply_markup=create_reply_menu_keyboard(user.id in Config.OPERATOR_IDS)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    if not is_private_chat(message):
        return

    help_text = (
        "📖 Как работает бот:\n\n"
        "1️⃣ Бот отправляет ежедневные задания\n"
        "2️⃣ Выполняй задания и получай баллы\n"
        "3️⃣ Участвуй в обсуждениях (1 балл за слово)\n"
        "4️⃣ В конце недели определяются победители\n\n"
        "💰 Баллы за задания:\n"
        "• Текст (≥10 символов) - 100 баллов\n"
        "• Фото - 200 баллов\n"
        "• Видео - 300 баллов\n\n"
        "⚡ За активность в чате:\n"
        "• 1 балл за каждое слово\n"
        "• Минимум 10 символов в сообщении\n"
        f"• Максимум {Config.MAX_DAILY_ACTIVITY_POINTS} баллов в день\n\n"
        "⚠️ Правила:\n"
        "• Не спамь короткими сообщениями\n"
        "• 3 предупреждения = исключение\n\n"
        "Команды:\n"
        "/my_points - мои баллы\n"
        "/top - топ-10 участников"
    )

    await message.answer(help_text)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main reply menu."""
    if not is_private_chat(message):
        return
    await message.answer(
        "Меню функций:",
        reply_markup=create_reply_menu_keyboard(message.from_user.id in Config.OPERATOR_IDS)
    )


@router.message(Command("whoami"))
async def cmd_whoami(message: Message):
    """Debug: show current user id and operator status."""
    if not is_private_chat(message):
        return
    user_id = message.from_user.id
    is_op = user_id in Config.OPERATOR_IDS
    await message.answer(
        f"Ваш ID: {user_id}\n"
        f"Оператор: {is_op}\n"
        f"OPERATOR_IDS: {', '.join(str(x) for x in Config.OPERATOR_IDS)}"
    )


@router.message(Command("thread_id"))
async def cmd_thread_id(message: Message):
    """Debug: show current thread id (topic)."""
    thread_id = message.message_thread_id
    chat_type = message.chat.type
    await message.answer(
        f"Chat type: {chat_type}\n"
        f"Thread ID: {thread_id}"
    )


async def send_my_points(message: Message, user):
    """Send user points info (supports callback context)."""
    if not is_private_chat(message):
        return

    user_id = user.id

    # Check if user is banned
    if db.is_user_banned(user_id):
        await message.answer(
            "❌ Вы исключены из геймификации на эту неделю."
        )
        return

    # Ensure user exists in database
    if not db.get_user(user_id):
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_operator=user.id in Config.OPERATOR_IDS
        )

    # Get user points
    points = db.get_user_points(user_id)
    db_user = db.get_user(user_id)

    text = (
        f"💰 Твои баллы: {points}\n"
        f"⚠️ Предупреждения: {db_user['warnings_count']}/{Config.MAX_WARNINGS}\n\n"
    )

    # Get daily activity points
    daily_points = db.get_daily_activity_points(user_id)
    remaining = Config.MAX_DAILY_ACTIVITY_POINTS - daily_points

    text += (
        f"📊 Сегодня за активность: {daily_points}/{Config.MAX_DAILY_ACTIVITY_POINTS} баллов\n"
    )

    if remaining > 0:
        text += f"Можно заработать еще {remaining} баллов!"
    else:
        text += "Дневной лимит достигнут!"

    await message.answer(text)


@router.message(Command("my_points"))
async def cmd_my_points(message: Message):
    """Show user's current points."""
    if not is_private_chat(message):
        return
    await send_my_points(message, message.from_user)


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Show top users leaderboard."""
    if not is_allowed_group_message(message):
        return
    is_flood = is_flood_thread(message)
    leaderboard = db.get_leaderboard(limit=3 if is_flood else 10)

    if not leaderboard:
        await message.answer("🏆 Пока нет участников с баллами!")
        return

    text = (
        "🏆 Подиум недели (Топ-3):\n\n"
        if is_flood
        else "🏆 Топ-10 участников недели:\n\n"
    )

    medals = ["🥇", "🥈", "🥉"]

    for idx, user in enumerate(leaderboard, 1):
        medal = medals[idx - 1] if idx <= 3 else f"{idx}️⃣"
        username = user["username"] or user["first_name"]
        points = user["total_points"]

        text += f"{medal} @{username} — {points} баллов\n"

    await message.answer(text)


@router.message(F.text == "💰 Мои баллы")
async def menu_my_points(message: Message):
    if not is_private_chat(message):
        return
    await send_my_points(message, message.from_user)


@router.message(F.text == "🏆 Топ")
async def menu_top(message: Message):
    if not is_private_chat(message):
        return
    await cmd_top(message)


@router.message(F.text == "📖 Помощь")
async def menu_help(message: Message):
    if not is_private_chat(message):
        return
    await cmd_help(message)


@router.message(F.text == "🛡 Модерация")
async def menu_moderation(message: Message):
    if not is_private_chat(message):
        return
    if message.from_user.id not in Config.OPERATOR_IDS:
        await message.answer("❌ Эта команда доступна только операторам")
        return
    from bot.handlers.operator import create_moderation_keyboard
    await message.answer(
        "Модерация:",
        reply_markup=create_moderation_keyboard()
    )


@router.message(F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO]))
async def handle_chat_activity(message: Message):
    """Handle chat messages for activity tracking and task answers."""
    user_id = message.from_user.id

    # In groups/supergroups process only configured Flood topic.
    if message.chat.type in ("group", "supergroup") and not is_allowed_group_message(message):
        return

    # In private chat keep command-based flow; ignore free text/media.
    if is_private_chat(message):
        return

    # Skip if user is banned
    if db.is_user_banned(user_id):
        return

    # Ensure user exists in database
    user = message.from_user
    if not db.get_user(user_id):
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_operator=user.id in Config.OPERATOR_IDS
        )

    # Check if this is a reply to a task
    current_task = db.get_current_daily_task()
    is_task_answer = False

    if message.reply_to_message and current_task:
        # Check if replying to bot's task message
        if message.reply_to_message.from_user.id == message.bot.id:
            is_task_answer = True
            await handle_task_answer(message, current_task)

    # In Flood topic only task answers are processed.


async def handle_task_answer(message: Message, task: dict):
    """Handle user's answer to a daily task."""
    user_id = message.from_user.id

    # Determine content type and content
    content_type = message.content_type.value
    content = None

    if content_type == "text":
        content = message.text
        # Check minimum length
        if len(content) < Config.MIN_MESSAGE_LENGTH:
            await message.reply(
                f"❌ Минимальная длина ответа: {Config.MIN_MESSAGE_LENGTH} символов"
            )
            return
    elif content_type == "photo":
        content = message.photo[-1].file_id
    elif content_type == "video":
        content = message.video.file_id

    # Add answer to database
    answer_id = db.add_answer(
        user_id=user_id,
        daily_task_id=task["id"],
        message_id=message.message_id,
        content_type=content_type,
        content=content
    )

    await message.reply(
        "✅ Ответ отправлен на проверку!\n"
        "Ожидайте одобрения оператора."
    )

    # Forward to operators
    await forward_to_operators(message, answer_id, task)


async def forward_to_operators(message: Message, answer_id: int, task: dict):
    """Forward answer to operators for review."""
    from bot.handlers.operator import create_review_keyboard

    user = message.from_user
    username = user.username or user.first_name

    caption = (
        f"📌 Новый ответ на задание:\n"
        f"👤 От: @{username}\n"
        f"🎯 Задание: {task['text']}\n"
        f"💰 Баллы: {task['points']}\n"
        f"🆔 Answer ID: {answer_id}"
    )

    keyboard = create_review_keyboard(answer_id)

    for operator_id in Config.OPERATOR_IDS:
        try:
            if message.content_type == ContentType.TEXT:
                await message.bot.send_message(
                    chat_id=operator_id,
                    text=f"{caption}\n\n📄 Текст:\n{message.text}",
                    reply_markup=keyboard
                )
            elif message.content_type == ContentType.PHOTO:
                await message.bot.send_photo(
                    chat_id=operator_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    reply_markup=keyboard
                )
            elif message.content_type == ContentType.VIDEO:
                await message.bot.send_video(
                    chat_id=operator_id,
                    video=message.video.file_id,
                    caption=caption,
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Failed to forward to operator {operator_id}: {e}")


async def track_activity(message: Message):
    """Track user's chat activity and award points."""
    user_id = message.from_user.id
    text = message.text

    # Check minimum length
    if len(text) < Config.MIN_MESSAGE_LENGTH:
        return

    # Check daily limit
    daily_points = db.get_daily_activity_points(user_id)
    if daily_points >= Config.MAX_DAILY_ACTIVITY_POINTS:
        return

    # Count words
    words = len(text.split())
    points = min(words * Config.POINTS_PER_WORD,
                 Config.MAX_DAILY_ACTIVITY_POINTS - daily_points)

    if points > 0:
        # Update activity
        db.update_chat_activity(user_id, words, points)

        # Add points
        db.add_points(
            user_id=user_id,
            points=points,
            reason="chat_activity"
        )

        logger.info(f"User {user_id} earned {points} points for activity")

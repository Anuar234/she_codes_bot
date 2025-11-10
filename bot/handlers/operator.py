"""Operator handlers for ChatQuestBot."""

import logging
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter

from database import Database
from config import Config

logger = logging.getLogger(__name__)

router = Router()
db = Database()


def is_operator(user_id: int) -> bool:
    """Check if user is an operator."""
    return user_id in Config.OPERATOR_IDS


def create_review_keyboard(answer_id: int) -> InlineKeyboardMarkup:
    """Create inline keyboard for answer review."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{answer_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{answer_id}")
        ]
    ])


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show all users statistics (operators only)."""
    if not is_operator(message.from_user.id):
        await message.answer("❌ Эта команда доступна только операторам")
        return

    stats = db.get_all_users_stats()

    if not stats:
        await message.answer("📊 Нет данных по пользователям")
        return

    text = "📊 Статистика всех участников:\n\n"

    for idx, user in enumerate(stats, 1):
        username = user["username"] or user["first_name"]
        points = user["total_points"]
        warnings = user["warnings_count"]
        banned = "🚫" if user["is_banned"] else ""

        text += f"{idx}. @{username} — {points} б. | ⚠️ {warnings} {banned}\n"

    await message.answer(text)


@router.message(Command("warn"))
async def cmd_warn(message: Message):
    """Issue a warning to a user (operators only)."""
    if not is_operator(message.from_user.id):
        await message.answer("❌ Эта команда доступна только операторам")
        return

    # Parse command: /warn @username [reason]
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "❌ Использование: /warn @username [причина]\n"
            "Пример: /warn @user спам короткими сообщениями"
        )
        return

    # Extract username or user_id
    target = parts[1]
    reason = parts[2] if len(parts) > 2 else "Нарушение правил"

    # Try to extract user_id from username or mention
    user_id = None

    # Check if it's a mention or username
    if target.startswith("@"):
        username = target[1:]
        # Try to find user in database by username
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                user_id = row["user_id"]
    elif target.isdigit():
        user_id = int(target)

    if not user_id:
        await message.answer(
            "❌ Пользователь не найден. Убедитесь, что пользователь "
            "взаимодействовал с ботом хотя бы раз."
        )
        return

    # Issue warning
    db.add_warning(
        user_id=user_id,
        issued_by=message.from_user.id,
        reason=reason
    )

    # Get updated user info
    user = db.get_user(user_id)
    warnings_count = user["warnings_count"]
    is_banned = user["is_banned"]

    response = (
        f"⚠️ Предупреждение выдано!\n"
        f"Пользователь: {target}\n"
        f"Причина: {reason}\n"
        f"Всего предупреждений: {warnings_count}/{Config.MAX_WARNINGS}\n"
    )

    if is_banned:
        response += "\n🚫 Пользователь исключен из геймификации!"

    await message.answer(response)

    # Notify user
    try:
        user_message = (
            f"⚠️ Вы получили предупреждение!\n"
            f"Причина: {reason}\n"
            f"Предупреждений: {warnings_count}/{Config.MAX_WARNINGS}\n"
        )

        if is_banned:
            user_message += "\n🚫 Вы исключены из геймификации на текущую неделю!"
        else:
            user_message += f"\nОсталось до исключения: {Config.MAX_WARNINGS - warnings_count}"

        await message.bot.send_message(user_id, user_message)
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")


@router.callback_query(F.data.startswith("approve_"))
async def callback_approve(callback: CallbackQuery):
    """Handle approve button callback."""
    if not is_operator(callback.from_user.id):
        await callback.answer("❌ Только операторы могут одобрять ответы", show_alert=True)
        return

    answer_id = int(callback.data.split("_")[1])
    answer = db.get_answer(answer_id)

    if not answer:
        await callback.answer("❌ Ответ не найден", show_alert=True)
        return

    if answer["status"] != "pending":
        await callback.answer("❌ Этот ответ уже проверен", show_alert=True)
        return

    # Update answer status
    db.update_answer_status(
        answer_id=answer_id,
        status="approved",
        reviewed_by=callback.from_user.id
    )

    # Get task points
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dt.*, t.points
            FROM answers a
            JOIN daily_tasks dt ON a.daily_task_id = dt.id
            JOIN tasks t ON dt.task_id = t.task_id
            WHERE a.answer_id = ?
        """, (answer_id,))
        task_info = cursor.fetchone()

    if task_info:
        points = task_info["points"]

        # Add points
        db.add_points(
            user_id=answer["user_id"],
            points=points,
            reason="task_answer",
            reference_id=answer_id
        )

        # Update message
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n✅ ОДОБРЕНО ({points} баллов)",
            reply_markup=None
        )

        # Notify user
        try:
            await callback.bot.send_message(
                answer["user_id"],
                f"✅ Ваш ответ одобрен! Начислено {points} баллов."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {answer['user_id']}: {e}")

        await callback.answer(f"✅ Ответ одобрен! Начислено {points} баллов")
    else:
        await callback.answer("❌ Ошибка при получении информации о задании", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def callback_reject(callback: CallbackQuery):
    """Handle reject button callback."""
    if not is_operator(callback.from_user.id):
        await callback.answer("❌ Только операторы могут отклонять ответы", show_alert=True)
        return

    answer_id = int(callback.data.split("_")[1])
    answer = db.get_answer(answer_id)

    if not answer:
        await callback.answer("❌ Ответ не найден", show_alert=True)
        return

    if answer["status"] != "pending":
        await callback.answer("❌ Этот ответ уже проверен", show_alert=True)
        return

    # Update answer status
    db.update_answer_status(
        answer_id=answer_id,
        status="rejected",
        reviewed_by=callback.from_user.id
    )

    # Update message
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ ОТКЛОНЕНО",
        reply_markup=None
    )

    # Notify user
    try:
        await callback.bot.send_message(
            answer["user_id"],
            "❌ Ваш ответ отклонен. Попробуйте еще раз!"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {answer['user_id']}: {e}")

    await callback.answer("❌ Ответ отклонен")


@router.message(Command("send_task"))
async def cmd_send_task(message: Message):
    """Manually send a task (operators only)."""
    if not is_operator(message.from_user.id):
        await message.answer("❌ Эта команда доступна только операторам")
        return

    from bot.utils.scheduler import send_random_task

    try:
        await send_random_task(message.bot)
        await message.answer("✅ Задание отправлено!")
    except Exception as e:
        logger.error(f"Failed to send task: {e}")
        await message.answer(f"❌ Ошибка при отправке задания: {e}")


@router.message(Command("week_end"))
async def cmd_week_end(message: Message):
    """Manually trigger week end results (operators only)."""
    if not is_operator(message.from_user.id):
        await message.answer("❌ Эта команда доступна только операторам")
        return

    from bot.utils.scheduler import send_week_results

    try:
        await send_week_results(message.bot)
        await message.answer("✅ Итоги недели отправлены!")
    except Exception as e:
        logger.error(f"Failed to send week results: {e}")
        await message.answer(f"❌ Ошибка: {e}")
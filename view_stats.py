"""Script to view bot statistics from the command line."""

from datetime import datetime
from database import Database
from config import Config


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def view_leaderboard():
    """Show current week leaderboard."""
    db = Database()
    leaderboard = db.get_leaderboard(limit=20)

    print_header("🏆 РЕЙТИНГ УЧАСТНИКОВ")

    if not leaderboard:
        print("Пока нет участников с баллами")
        return

    now = datetime.now()
    week_number = now.isocalendar()[1]
    print(f"Неделя {week_number}, {now.year}\n")

    medals = ["🥇", "🥈", "🥉"]

    for idx, user in enumerate(leaderboard, 1):
        medal = medals[idx - 1] if idx <= 3 else f"{idx:2d}."
        username = user["username"] or user["first_name"]
        points = user["total_points"]

        print(f"{medal} @{username:<20} {points:>6} баллов")


def view_all_users():
    """Show all users statistics."""
    db = Database()
    stats = db.get_all_users_stats()

    print_header("📊 СТАТИСТИКА ВСЕХ УЧАСТНИКОВ")

    if not stats:
        print("Нет зарегистрированных пользователей")
        return

    print(f"{'№':<4} {'Username':<20} {'Баллы':<8} {'Пред.':<6} {'Статус'}")
    print("-" * 60)

    for idx, user in enumerate(stats, 1):
        username = user["username"] or user["first_name"]
        points = user["total_points"]
        warnings = user["warnings_count"]
        status = "🚫 Бан" if user["is_banned"] else "✅ Активен"

        print(f"{idx:<4} @{username:<19} {points:<8} {warnings}/3    {status}")


def view_tasks():
    """Show all tasks."""
    db = Database()
    tasks = db.get_active_tasks()

    print_header("🎯 СПИСОК ЗАДАНИЙ")

    if not tasks:
        print("Нет активных заданий")
        return

    print(f"Всего заданий: {len(tasks)}\n")

    for task in tasks:
        print(f"[{task['task_id']}] {task['content_type'].upper()} - {task['points']} баллов")
        print(f"    {task['text'][:70]}{'...' if len(task['text']) > 70 else ''}")
        print()


def view_pending_answers():
    """Show pending answers waiting for review."""
    db = Database()

    print_header("⏳ ОТВЕТЫ В ОЖИДАНИИ ПРОВЕРКИ")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                a.answer_id,
                a.user_id,
                u.username,
                u.first_name,
                a.content_type,
                a.answered_at,
                t.text as task_text,
                t.points
            FROM answers a
            JOIN users u ON a.user_id = u.user_id
            JOIN daily_tasks dt ON a.daily_task_id = dt.id
            JOIN tasks t ON dt.task_id = t.task_id
            WHERE a.status = 'pending'
            ORDER BY a.answered_at ASC
        """)

        pending = [dict(row) for row in cursor.fetchall()]

    if not pending:
        print("Все ответы проверены! 🎉")
        return

    print(f"Ожидают проверки: {len(pending)}\n")

    for answer in pending:
        username = answer["username"] or answer["first_name"]
        answered_at = datetime.fromisoformat(answer["answered_at"]).strftime("%d.%m %H:%M")

        print(f"[{answer['answer_id']}] @{username} - {answer['content_type']}")
        print(f"    Задание: {answer['task_text'][:60]}{'...' if len(answer['task_text']) > 60 else ''}")
        print(f"    Время: {answered_at} | Баллы: {answer['points']}")
        print()


def view_recent_activity():
    """Show recent point activity."""
    db = Database()

    print_header("📈 ПОСЛЕДНЯЯ АКТИВНОСТЬ")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.point_id,
                p.user_id,
                u.username,
                u.first_name,
                p.points,
                p.reason,
                p.created_at
            FROM points p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC
            LIMIT 20
        """)

        activity = [dict(row) for row in cursor.fetchall()]

    if not activity:
        print("Пока нет активности")
        return

    for point in activity:
        username = point["username"] or point["first_name"]
        created_at = datetime.fromisoformat(point["created_at"]).strftime("%d.%m %H:%M")
        reason = "💬 Активность" if point["reason"] == "chat_activity" else "✅ Задание"

        print(f"{created_at} | @{username:<15} +{point['points']:>3} баллов | {reason}")


def main():
    """Main function."""
    print("\n🤖 ChatQuestBot - Статистика")

    while True:
        print("\n" + "-"*60)
        print("Выберите действие:")
        print("1. 🏆 Показать рейтинг")
        print("2. 📊 Статистика всех участников")
        print("3. 🎯 Список заданий")
        print("4. ⏳ Ответы в ожидании")
        print("5. 📈 Последняя активность")
        print("0. Выход")

        choice = input("\n> ").strip()

        if choice == "1":
            view_leaderboard()
        elif choice == "2":
            view_all_users()
        elif choice == "3":
            view_tasks()
        elif choice == "4":
            view_pending_answers()
        elif choice == "5":
            view_recent_activity()
        elif choice == "0":
            print("\n👋 До встречи!")
            break
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 До встречи!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
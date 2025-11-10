"""Script to reset the database (WARNING: This will delete all data!)."""

import sys
from pathlib import Path
from database import Database


def reset_database():
    """Reset the database by deleting and recreating it."""
    db_path = Path("data/bot.db")

    if not db_path.exists():
        print("ℹ️  База данных не существует, создаю новую...")
        db = Database()
        print("✅ База данных создана!")
        return

    print("⚠️  ВНИМАНИЕ: Это действие удалит ВСЕ данные!")
    print(f"   База данных: {db_path}")
    print("\n   Будут удалены:")
    print("   - Все пользователи и их баллы")
    print("   - Все ответы на задания")
    print("   - Вся история активности")
    print("   - Все предупреждения")
    print("\n   Задания из tasks.json НЕ будут удалены")
    print("   (они будут загружены заново при следующем запуске)\n")

    confirm = input("Вы уверены? Введите 'YES' для подтверждения: ").strip()

    if confirm != "YES":
        print("❌ Отменено")
        return

    # Backup old database
    backup_path = db_path.with_suffix(".db.backup")
    if backup_path.exists():
        print(f"\n⚠️  Найдена старая резервная копия: {backup_path}")
        overwrite = input("Перезаписать её? (y/n): ").strip().lower()
        if overwrite == "y":
            backup_path.unlink()
        else:
            print("❌ Отменено")
            return

    print(f"\n📦 Создаю резервную копию: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    print("✅ Резервная копия создана")

    # Delete database
    print(f"\n🗑️  Удаляю базу данных...")
    db_path.unlink()

    # Delete journal if exists
    journal_path = db_path.with_suffix(".db-journal")
    if journal_path.exists():
        journal_path.unlink()

    print("✅ База данных удалена")

    # Create new database
    print("\n📊 Создаю новую базу данных...")
    db = Database()
    print("✅ База данных создана и инициализирована")

    print("\n🎉 Готово!")
    print(f"💾 Резервная копия: {backup_path}")
    print("\nТеперь можно запустить бота: python main.py")


def restore_from_backup():
    """Restore database from backup."""
    db_path = Path("data/bot.db")
    backup_path = db_path.with_suffix(".db.backup")

    if not backup_path.exists():
        print("❌ Резервная копия не найдена!")
        return

    if db_path.exists():
        print("⚠️  Текущая база данных будет перезаписана")
        confirm = input("Продолжить? (y/n): ").strip().lower()
        if confirm != "y":
            print("❌ Отменено")
            return
        db_path.unlink()

    import shutil
    shutil.copy2(backup_path, db_path)
    print("✅ База данных восстановлена из резервной копии")


def view_database_info():
    """Show database information."""
    db_path = Path("data/bot.db")

    if not db_path.exists():
        print("❌ База данных не существует")
        return

    db = Database()

    print("📊 Информация о базе данных\n")

    # Get counts
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM tasks")
        tasks_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM answers")
        answers_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM answers WHERE status = 'pending'")
        pending_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM points")
        points_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COALESCE(SUM(points), 0) as total FROM points")
        total_points = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as count FROM warnings")
        warnings_count = cursor.fetchone()["count"]

    print(f"👥 Пользователей: {users_count}")
    print(f"🎯 Заданий: {tasks_count}")
    print(f"📝 Ответов: {answers_count} (ожидают: {pending_count})")
    print(f"💰 Записей о баллах: {points_count} (всего начислено: {total_points})")
    print(f"⚠️  Предупреждений: {warnings_count}")

    # Database file size
    size_mb = db_path.stat().st_size / 1024 / 1024
    print(f"\n💾 Размер файла: {size_mb:.2f} MB")
    print(f"📁 Путь: {db_path.absolute()}")


def main():
    """Main function."""
    print("\n🗄️  Управление базой данных ChatQuestBot\n")

    print("Выберите действие:")
    print("1. Сбросить базу данных (создать новую)")
    print("2. Восстановить из резервной копии")
    print("3. Показать информацию о базе данных")
    print("0. Выход")

    choice = input("\n> ").strip()

    if choice == "1":
        reset_database()
    elif choice == "2":
        restore_from_backup()
    elif choice == "3":
        view_database_info()
    elif choice == "0":
        print("👋 До встречи!")
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Отменено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
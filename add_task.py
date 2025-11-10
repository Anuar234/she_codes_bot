"""Interactive script to add new tasks to the database."""

import json
from pathlib import Path
from database import Database


def add_task_interactive():
    """Interactive CLI to add a new task."""
    print("🎯 Добавление нового задания\n")

    # Get task text
    print("Введите текст задания:")
    text = input("> ").strip()

    if not text:
        print("❌ Текст не может быть пустым!")
        return

    # Get content type
    print("\nВыберите тип контента:")
    print("1. text - Текстовый ответ")
    print("2. photo - Фото")
    print("3. video - Видео")
    print("4. mixed - Смешанный (текст, фото или видео)")

    content_types = {
        "1": "text",
        "2": "photo",
        "3": "video",
        "4": "mixed"
    }

    choice = input("> ").strip()
    content_type = content_types.get(choice)

    if not content_type:
        print("❌ Неверный выбор!")
        return

    # Get points
    default_points = {"text": 100, "photo": 200, "video": 300, "mixed": 150}
    suggested_points = default_points[content_type]

    print(f"\nБаллы за выполнение (по умолчанию {suggested_points}):")
    points_input = input("> ").strip()

    if points_input:
        try:
            points = int(points_input)
        except ValueError:
            print("❌ Баллы должны быть числом!")
            return
    else:
        points = suggested_points

    # Confirm
    print("\n" + "="*50)
    print("📝 Задание:")
    print(f"   {text}")
    print(f"📊 Тип: {content_type}")
    print(f"💰 Баллы: {points}")
    print("="*50)

    confirm = input("\nДобавить это задание? (y/n): ").strip().lower()

    if confirm != "y":
        print("❌ Отменено")
        return

    # Add to database
    db = Database()
    task_id = db.add_task(text=text, content_type=content_type, points=points)

    print(f"✅ Задание добавлено в базу данных (ID: {task_id})!")

    # Ask if want to add to tasks.json
    save_to_json = input("\nСохранить также в tasks.json? (y/n): ").strip().lower()

    if save_to_json == "y":
        tasks_file = Path("data/tasks.json")

        if tasks_file.exists():
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        else:
            tasks = []

        tasks.append({
            "text": text,
            "content_type": content_type,
            "points": points
        })

        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        print(f"✅ Задание сохранено в {tasks_file}")

    print("\n🎉 Готово!")


def main():
    """Main function."""
    try:
        add_task_interactive()
    except KeyboardInterrupt:
        print("\n\n❌ Отменено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
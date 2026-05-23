import json
import os

TASKS_FILE = "tasks.json"


def load_tasks():
    """tasks.json faylidan vazifalarni yuklaydi"""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Tasks yuklash xatosi: {e}")
    return []


def save_tasks(tasks_database):
    """tasks.json faylga vazifalarni saqlaydi"""
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks_database, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Tasks saqlash xatosi: {e}")


def update_task_status(task_id: int, status: str, completed_by: str = None):
    """Vazifa statusini yangilash"""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = status
            if status == "completed":
                from datetime import datetime, timedelta, timezone
                tashkent_tz = timezone(timedelta(hours=5))
                task["completed_at"] = datetime.now(tashkent_tz).isoformat()
                task["completed_by"] = completed_by
            save_tasks(tasks)
            return True
    return False

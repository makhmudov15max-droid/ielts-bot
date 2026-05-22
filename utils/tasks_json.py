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

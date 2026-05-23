import json
import os

USERS_FILE = "users.json"


def load_users(admin_id: int):
    """users.json faylidan ma'lumotlarni yuklaydi"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if str(admin_id) not in data:
                    data[str(admin_id)] = {
                        "role": "Owner",
                        "name": "Baxtiyorjon",
                        "active_task": None,
                        "is_waiting_for_proof": False
                    }
                    save_users(data)
                else:
                    # Eski foydalanuvchilarga yangi fieldlarni qo'shish
                    for u_id, u_info in data.items():
                        if "active_task" not in u_info:
                            u_info["active_task"] = None
                        if "is_waiting_for_proof" not in u_info:
                            u_info["is_waiting_for_proof"] = False
                    save_users(data)
                return data
    except Exception as e:
        print(f"Users yuklash xatosi: {e}")

    return {
        str(admin_id): {
            "role": "Owner",
            "name": "Baxtiyorjon",
            "active_task": None,
            "is_waiting_for_proof": False
        }
    }


def save_users(data=None):
    """users.json faylga ma'lumotlarni saqlaydi"""
    try:
        if data is None:
            global USERS_ROLES
            data = USERS_ROLES
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Users saqlash xatosi: {e}")


def set_user_busy(user_id: str, task_id: int):
    """Foydalanuvchini band holatiga o'tkazish (isbot kutilmoqda)"""
    users = load_users(6500594896)
    if user_id in users:
        users[user_id]["active_task"] = task_id
        users[user_id]["is_waiting_for_proof"] = True
        save_users(users)
        return True
    return False


def set_user_free(user_id: str):
    """Foydalanuvchini band holatidan chiqarish"""
    users = load_users(6500594896)
    if user_id in users:
        users[user_id]["active_task"] = None
        users[user_id]["is_waiting_for_proof"] = False
        save_users(users)
        return True
    return False


def is_user_busy(user_id: str) -> bool:
    """Foydalanuvchi band holatida ekanligini tekshirish"""
    users = load_users(6500594896)
    if user_id in users:
        return users[user_id].get("is_waiting_for_proof", False)
    return False


def get_user_active_task(user_id: str) -> int:
    """Foydalanuvchining active task ID sini olish"""
    users = load_users(6500594896)
    if user_id in users:
        return users[user_id].get("active_task")
    return None

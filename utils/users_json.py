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
                        "name": "Baxtiyorjon"
                    }
                    save_users(data)
                return data
    except Exception as e:
        print(f"Users yuklash xatosi: {e}")

    return {
        str(admin_id): {
            "role": "Owner",
            "name": "Baxtiyorjon"
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

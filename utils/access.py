import json
import os


def check_user_access(users_roles, user_id: int) -> bool:
    """Foydalanuvchi botdan foydalanish huquqiga egami"""
    # Agar users_roles None bo'lsa, False qaytar
    if users_roles is None:
        print("DEBUG: check_user_access - users_roles is None!")
        return False
    
    user_info = users_roles.get(str(user_id))
    if not user_info:
        print(f"DEBUG: check_user_access - user {user_id} not found")
        return False
    if not isinstance(user_info, dict):
        print(f"DEBUG: check_user_access - user_info not dict")
        return False
    if user_info.get("role") in [None, "rejected"]:
        print(f"DEBUG: check_user_access - role rejected or None")
        return False
    
    return True


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi Admin, Owner yoki Manager rolida ekanligini tekshiradi"""
    USERS_FILE = "users.json"
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
                user_info = users.get(str(user_id))
                if user_info:
                    role = user_info.get("role")
                    return role in ["Admin", "Owner", "Manager"]
    except Exception as e:
        print(f"is_admin() xatosi: {e}")
    return False

import logging
from utils.database import get_pool


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


async def is_admin(user_id: int) -> bool:
    """Foydalanuvchi Admin, Owner yoki Manager rolida ekanligini tekshiradi (PostgreSQL orqali)"""
    pool = get_pool()
    if not pool:
        logging.error("Database pool mavjud emas!")
        return False
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT role FROM users WHERE user_id = $1",
                str(user_id)
            )
            if row:
                role = row["role"]
                return role in ["Admin", "Owner", "Manager"]
    except Exception as e:
        logging.error(f"is_admin() xatosi: {e}")
    return False

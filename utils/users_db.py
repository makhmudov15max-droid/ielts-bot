import logging
from utils.database import get_pool

async def load_users(admin_id: int):
    """PostgreSQL dan foydalanuvchilarni yuklaydi"""
    pool = get_pool()
    if not pool:
        logging.error("Database pool mavjud emas!")
        return {}
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, role, name, active_task, is_waiting_for_proof FROM users")
            
            users = {}
            for row in rows:
                users[row["user_id"]] = {
                    "role": row["role"],
                    "name": row["name"],
                    "active_task": row["active_task"],
                    "is_waiting_for_proof": row["is_waiting_for_proof"]
                }
            return users
    except Exception as e:
        logging.error(f"Users yuklash xatosi: {e}")
        return {}

async def save_users(data):
    """PostgreSQL ga foydalanuvchilarni saqlaydi"""
    pool = get_pool()
    if not pool:
        logging.error("Database pool mavjud emas!")
        return
    
    try:
        async with pool.acquire() as conn:
            for user_id, user_info in data.items():
                await conn.execute("""
                    INSERT INTO users (user_id, role, name, active_task, is_waiting_for_proof, updated_at)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        role = EXCLUDED.role,
                        name = EXCLUDED.name,
                        active_task = EXCLUDED.active_task,
                        is_waiting_for_proof = EXCLUDED.is_waiting_for_proof,
                        updated_at = CURRENT_TIMESTAMP
                """, user_id, user_info.get("role"), user_info.get("name"),
                   user_info.get("active_task"), user_info.get("is_waiting_for_proof", False))
    except Exception as e:
        logging.error(f"Users saqlash xatosi: {e}")

async def set_user_busy(user_id: str, task_id: int):
    """Foydalanuvchini band holatiga o'tkazish"""
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET active_task = $1, is_waiting_for_proof = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
            """, task_id, user_id)
        return True
    except Exception as e:
        logging.error(f"set_user_busy xatosi: {e}")
        return False

async def set_user_free(user_id: str):
    """Foydalanuvchini band holatidan chiqarish"""
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET active_task = NULL, is_waiting_for_proof = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id)
        return True
    except Exception as e:
        logging.error(f"set_user_free xatosi: {e}")
        return False

async def is_user_busy(user_id: str) -> bool:
    """Foydalanuvchi band holatida ekanligini tekshirish"""
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT is_waiting_for_proof FROM users WHERE user_id = $1", user_id)
            return row["is_waiting_for_proof"] if row else False
    except Exception as e:
        logging.error(f"is_user_busy xatosi: {e}")
        return False

async def get_user_active_task(user_id: str) -> int:
    """Foydalanuvchining active task ID sini olish"""
    pool = get_pool()
    if not pool:
        return None
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT active_task FROM users WHERE user_id = $1", user_id)
            return row["active_task"] if row else None
    except Exception as e:
        logging.error(f"get_user_active_task xatosi: {e}")
        return None

async def get_user_role(user_id: str) -> str:
    """Foydalanuvchining rolini qaytaradi"""
    pool = get_pool()
    if not pool:
        return None
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT role FROM users WHERE user_id = $1", user_id)
            return row["role"] if row else None
    except Exception as e:
        logging.error(f"get_user_role xatosi: {e}")
        return None

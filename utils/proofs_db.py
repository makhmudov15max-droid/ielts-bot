import logging
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

async def load_proofs():
    """PostgreSQL dan barcha isbotlarni yuklaydi"""
    pool = get_pool()
    if not pool:
        return []
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM proofs ORDER BY id")
            
            proofs = []
            for row in rows:
                proofs.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "task_id": row["task_id"],
                    "task_name": row["task_name"],
                    "task_description": row["task_description"],
                    "proof_type": row["proof_type"],
                    "file_id": row["file_id"],
                    "text_content": row["text_content"],
                    "group_chat_id": row["group_chat_id"],
                    "timestamp": row["timestamp"].isoformat(),
                    "date": row["date"],
                    "time": row["time"]
                })
            return proofs
    except Exception as e:
        logging.error(f"Proofs yuklash xatosi: {e}")
        return []

async def add_proof(user_id, user_name, task_id, task_name, task_description, 
                    proof_type, file_id, group_chat_id, text_content=None):
    """Yangi isbot qo'shish va 60 kundan eskilarni o'chirish"""
    pool = get_pool()
    if not pool:
        return None
    
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    
    try:
        async with pool.acquire() as conn:
            # Yangi isbot qo'shish
            row = await conn.fetchrow("""
                INSERT INTO proofs (user_id, user_name, task_id, task_name, task_description,
                                    proof_type, file_id, text_content, group_chat_id,
                                    timestamp, date, time)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, str(user_id), user_name, task_id, task_name, task_description,
               proof_type, file_id or "", text_content or "", group_chat_id,
               now, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
            
            new_id = row["id"]
            
            # 60 kundan eski isbotlarni o'chirish
            cutoff = now - timedelta(days=60)
            await conn.execute("DELETE FROM proofs WHERE timestamp < $1", cutoff)
            
            return {
                "id": new_id,
                "user_id": str(user_id),
                "user_name": user_name,
                "task_id": task_id,
                "task_name": task_name,
                "task_description": task_description,
                "proof_type": proof_type,
                "file_id": file_id,
                "text_content": text_content,
                "group_chat_id": group_chat_id,
                "timestamp": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S")
            }
    except Exception as e:
        logging.error(f"add_proof xatosi: {e}")
        return None

async def get_proofs_by_user(user_id, start_date=None, end_date=None):
    """Foydalanuvchi bo'yicha isbotlarni olish"""
    pool = get_pool()
    if not pool:
        return []
    
    try:
        async with pool.acquire() as conn:
            if start_date and end_date:
                rows = await conn.fetch("""
                    SELECT * FROM proofs WHERE user_id = $1 AND date BETWEEN $2 AND $3 ORDER BY timestamp DESC
                """, str(user_id), start_date, end_date)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM proofs WHERE user_id = $1 ORDER BY timestamp DESC
                """, str(user_id))
            
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"get_proofs_by_user xatosi: {e}")
        return []

async def get_proofs_by_role(role_name, start_date=None, end_date=None):
    """Role bo'yicha isbotlarni olish"""
    pool = get_pool()
    if not pool:
        return []
    
    try:
        async with pool.acquire() as conn:
            if start_date and end_date:
                rows = await conn.fetch("""
                    SELECT p.* FROM proofs p
                    JOIN users u ON p.user_id = u.user_id
                    WHERE u.role = $1 AND p.date BETWEEN $2 AND $3
                    ORDER BY p.timestamp DESC
                """, role_name, start_date, end_date)
            else:
                rows = await conn.fetch("""
                    SELECT p.* FROM proofs p
                    JOIN users u ON p.user_id = u.user_id
                    WHERE u.role = $1
                    ORDER BY p.timestamp DESC
                """, role_name)
            
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"get_proofs_by_role xatosi: {e}")
        return []

async def get_proofs_by_date_range(start_date, end_date):
    """Sana oralig'i bo'yicha isbotlarni olish"""
    pool = get_pool()
    if not pool:
        return []
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM proofs WHERE date BETWEEN $1 AND $2 ORDER BY timestamp DESC
            """, start_date, end_date)
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"get_proofs_by_date_range xatosi: {e}")
        return []

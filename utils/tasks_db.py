import logging
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

async def load_tasks():
    """PostgreSQL dan vazifalarni yuklaydi"""
    pool = get_pool()
    if not pool:
        return []
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, task_type, task_name, task_description, task_days, 
                       task_frequency, task_times, proof_type, assigned_to_id,
                       assigned_to_name, sent_today_times, status, completed_at, 
                       completed_by, created_at
                FROM tasks ORDER BY id
            """)
            
            tasks = []
            for row in rows:
                tasks.append({
                    "id": row["id"],
                    "task_type": row["task_type"],
                    "task_name": row["task_name"],
                    "task_description": row["task_description"] or "Mavjud emas",
                    "task_days": row["task_days"] or "Kunlik vazifa",
                    "task_frequency": row["task_frequency"] or "Bir martalik",
                    "task_times": row["task_times"] or [],
                    "proof_type": row["proof_type"],
                    "assigned_to_id": int(row["assigned_to_id"]),
                    "assigned_to_name": row["assigned_to_name"] or "Noma'lum",
                    "sent_today_times": row["sent_today_times"] or [],
                    "status": row["status"],
                    "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                    "completed_by": row["completed_by"],
                    "created_at": row["created_at"].isoformat()
                })
            return tasks
    except Exception as e:
        logging.error(f"Tasks yuklash xatosi: {e}")
        return []

async def save_tasks(tasks_database):
    """PostgreSQL ga vazifalarni saqlaydi (to'liq qayta yozadi)"""
    pool = get_pool()
    if not pool:
        return
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE tasks RESTART IDENTITY")
            
            for task in tasks_database:
                await conn.execute("""
                    INSERT INTO tasks (id, task_type, task_name, task_description, task_days,
                                       task_frequency, task_times, proof_type, assigned_to_id,
                                       assigned_to_name, sent_today_times, status, completed_at,
                                       completed_by, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """, task["id"], task["task_type"], task["task_name"], task.get("task_description"),
                   task.get("task_days"), task.get("task_frequency"), task.get("task_times", []),
                   task["proof_type"], task["assigned_to_id"], task["assigned_to_name"],
                   task.get("sent_today_times", []), task["status"], task.get("completed_at"),
                   task.get("completed_by"), task.get("created_at"))
    except Exception as e:
        logging.error(f"Tasks saqlash xatosi: {e}")

async def update_task_status(task_id: int, status: str, completed_by: str = None):
    """Vazifa statusini yangilash"""
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            if status == "completed":
                tashkent_tz = timezone(timedelta(hours=5))
                completed_at = datetime.now(tashkent_tz).isoformat()
                await conn.execute("""
                    UPDATE tasks SET status = $1, completed_at = $2, completed_by = $3
                    WHERE id = $4
                """, status, completed_at, completed_by, task_id)
            else:
                await conn.execute("""
                    UPDATE tasks SET status = $1 WHERE id = $2
                """, status, task_id)
        return True
    except Exception as e:
        logging.error(f"update_task_status xatosi: {e}")
        return False

async def get_task_by_id(task_id: int):
    """ID bo'yicha vazifani olish"""
    tasks = await load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None

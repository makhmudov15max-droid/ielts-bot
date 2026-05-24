import logging
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

async def load_tasks():
    """PostgreSQL dan vazifalarni yuklaydi"""
    pool = get_pool()
    if not pool:
        logging.error("load_tasks: pool mavjud emas")
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
            
            logging.info(f"load_tasks: {len(rows)} ta vazifa topildi")
            
            tasks = []
            for row in rows:
                created_at_value = row["created_at"]
                if created_at_value:
                    if isinstance(created_at_value, datetime):
                        created_at_str = created_at_value.isoformat()
                    else:
                        created_at_str = str(created_at_value)
                else:
                    created_at_str = None
                    
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
                    "completed_at": row["completed_at"].isoformat() if row["completed_at"] and isinstance(row["completed_at"], datetime) else row["completed_at"],
                    "completed_by": row["completed_by"],
                    "created_at": created_at_str
                })
            return tasks
    except Exception as e:
        logging.error(f"load_tasks xatosi: {e}")
        import traceback
        traceback.print_exc()
        return []

async def save_tasks(tasks_database):
    """PostgreSQL ga vazifalarni saqlaydi"""
    pool = get_pool()
    if not pool:
        logging.error("save_tasks: pool mavjud emas")
        return
    
    logging.info(f"save_tasks: {len(tasks_database)} ta vazifa saqlanmoqda")
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE tasks RESTART IDENTITY")
            
            for idx, task in enumerate(tasks_database):
                try:
                    assigned_to_id = str(task.get("assigned_to_id"))
                    created_at = task.get("created_at")
                    
                    if created_at and isinstance(created_at, str):
                        try:
                            created_at = created_at.replace('T', ' ').replace('Z', '')[:19]
                        except:
                            created_at = datetime.now().isoformat()
                    
                    await conn.execute("""
                        INSERT INTO tasks (id, task_type, task_name, task_description, task_days,
                                           task_frequency, task_times, proof_type, assigned_to_id,
                                           assigned_to_name, sent_today_times, status, completed_at,
                                           completed_by, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    """, 
                        task["id"], 
                        task["task_type"], 
                        task["task_name"], 
                        task.get("task_description"),
                        task.get("task_days"), 
                        task.get("task_frequency"), 
                        task.get("task_times", []),
                        task["proof_type"], 
                        assigned_to_id,
                        task.get("assigned_to_name"),
                        task.get("sent_today_times", []), 
                        task["status"], 
                        task.get("completed_at"),
                        task.get("completed_by"), 
                        created_at
                    )
                    logging.info(f"save_tasks: Task {task['id']} saqlandi")
                except Exception as inner_e:
                    logging.error(f"save_tasks: Task {task.get('id')} saqlashda xatolik: {inner_e}")
                    logging.error(f"Task malumotlari: {task}")
                    
    except Exception as e:
        logging.error(f"save_tasks xatosi: {e}")
        import traceback
        traceback.print_exc()

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

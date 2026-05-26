import logging
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

TASHKENT_TZ = timezone(timedelta(hours=5))


async def init_attendance_table():
    """attendance jadvalini yaratish"""
    pool = get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    role TEXT,
                    date TEXT NOT NULL,
                    arrived_at TEXT,
                    late_minutes INTEGER DEFAULT 0,
                    reason TEXT,
                    proof_file_id TEXT,
                    proof_type TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status)")
            logging.info("✅ attendance jadvali tayyor")
    except Exception as e:
        logging.error(f"init_attendance_table xatosi: {e}", exc_info=True)


async def add_attendance(user_id: str, user_name: str, role: str,
                         date: str, arrived_at: str, late_minutes: int,
                         reason: str, proof_file_id: str = None, 
                         proof_type: str = None, status: str = "checked_in"):
    """Kech qolish ma'lumotini saqlash (status bilan)"""
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO attendance (user_id, user_name, role, date, arrived_at,
                                        late_minutes, reason, proof_file_id, proof_type, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, user_id, user_name, role, date, arrived_at,
                late_minutes, reason, proof_file_id, proof_type, status)
            return row["id"]
    except Exception as e:
        logging.error(f"add_attendance xatosi: {e}", exc_info=True)
        return None


async def get_attendance_by_user_and_month(user_id: str, year: int, month: int):
    """Bitta xodimning oylik ma'lumotlari (barcha statuslar)"""
    pool = get_pool()
    if not pool:
        return []
    try:
        month_str = f"{year}-{month:02d}"
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM attendance
                WHERE user_id = $1 AND date LIKE $2
                ORDER BY date ASC
            """, user_id, f"{month_str}%")
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"get_attendance_by_user_and_month xatosi: {e}", exc_info=True)
        return []


async def get_attendance_by_user_today(user_id: str):
    """Xodimning bugungi ma'lumotlari"""
    today = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d")
    return await get_attendance_by_user_and_date(user_id, today)


async def get_attendance_by_user_and_date(user_id: str, date: str):
    """Bitta xodimning berilgan sanadagi yozuvlari"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM attendance WHERE user_id = $1 AND date = $2
                ORDER BY created_at ASC
            """, user_id, date)
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"get_attendance_by_user_and_date xatosi: {e}", exc_info=True)
        return []


async def get_attendance_by_dates(user_id: str, dates: list):
    """Bir nechta sana uchun xodim yozuvlari"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM attendance
                WHERE user_id = $1 AND date = ANY($2::text[])
                ORDER BY date ASC
            """, user_id, dates)
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"get_attendance_by_dates xatosi: {e}", exc_info=True)
        return []


async def has_checkin_today(user_id: str) -> bool:
    """Xodim bugun ishga kelganini tasdiqlaganmi?"""
    today = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d")
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id FROM attendance 
                WHERE user_id = $1 AND date = $2 AND status = 'checked_in'
            """, user_id, today)
            return row is not None
    except Exception as e:
        logging.error(f"has_checkin_today xatosi: {e}", exc_info=True)
        return False


async def mark_missed_for_date(user_id: str, date: str):
    """Berilgan sana uchun xodimni 'missed' deb belgilash"""
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            # Agar shu sana uchun hech qanday yozuv bo'lmasa
            existing = await conn.fetchrow("""
                SELECT id FROM attendance WHERE user_id = $1 AND date = $2
            """, user_id, date)
            
            if not existing:
                # Yangi 'missed' yozuv qo'shish
                await conn.execute("""
                    INSERT INTO attendance (user_id, user_name, role, date, arrived_at, status)
                    SELECT $1, name, role, $2, NULL, 'missed'
                    FROM users WHERE user_id = $1
                """, user_id, date)
            else:
                # Mavjud yozuvni 'missed' ga o'zgartirish (agar checked_in bo'lmasa)
                await conn.execute("""
                    UPDATE attendance SET status = 'missed' 
                    WHERE user_id = $1 AND date = $2 AND status != 'checked_in'
                """, user_id, date)
        return True
    except Exception as e:
        logging.error(f"mark_missed_for_date xatosi: {e}", exc_info=True)
        return False


async def get_missed_days(user_id: str, year: int, month: int) -> list:
    """Xodimning kelmagan kunlari ro'yxati"""
    pool = get_pool()
    if not pool:
        return []
    try:
        month_str = f"{year}-{month:02d}"
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT date FROM attendance
                WHERE user_id = $1 AND date LIKE $2 AND status = 'missed'
                ORDER BY date ASC
            """, user_id, f"{month_str}%")
            return [row["date"] for row in rows]
    except Exception as e:
        logging.error(f"get_missed_days xatosi: {e}", exc_info=True)
        return []

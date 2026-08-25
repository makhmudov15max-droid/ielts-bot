import asyncpg
import os
import logging

DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None


async def init_db():
    """Database pool ni yaratish va jadvallarni yaratish"""
    global db_pool
    try:
        if not DATABASE_URL:
            logging.error("❌ DATABASE_URL environment variable topilmadi!")
            raise Exception("DATABASE_URL not set")
        
        logging.info("🔗 PostgreSQL ga ulanish...")
        
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
            timeout=60
        )
        
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        
        logging.info("✅ PostgreSQL ulandi!")
        
        async with db_pool.acquire() as conn:
            # ================= USERS TABLE =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    name TEXT,
                    active_task INTEGER,
                    is_waiting_for_proof BOOLEAN DEFAULT FALSE,
                    work_start TEXT DEFAULT '09:00',
                    work_end TEXT DEFAULT '18:00',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ================= TASKS TABLE =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    task_description TEXT,
                    task_days TEXT,
                    task_frequency TEXT,
                    task_times TEXT[],
                    proof_type TEXT,
                    assigned_to_id TEXT NOT NULL,
                    assigned_to_name TEXT,
                    sent_today_times TEXT[],
                    status TEXT DEFAULT 'pending',
                    completed_at TIMESTAMP,
                    completed_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ================= PROOFS TABLE =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS proofs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    task_id INTEGER,
                    task_name TEXT,
                    task_description TEXT,
                    proof_type TEXT,
                    file_id TEXT,
                    text_content TEXT,
                    group_chat_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date TEXT,
                    time TEXT
                )
            """)
            
            # ================= ATTENDANCE TABLE =================
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
            
            # ================= HOLIDAYS TABLE (is_repeat bilan) =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS holidays (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    role TEXT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    is_repeat BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ================= MIGRATION: Ustunlar qo'shish =================
            # is_repeat ustuni eski bazalarda bo'lmasligi mumkin
            await conn.execute("""
                ALTER TABLE holidays ADD COLUMN IF NOT EXISTS is_repeat BOOLEAN DEFAULT FALSE
            """)
            await conn.execute("""
                ALTER TABLE holidays ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            # ================= INDEXES =================
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_proofs_user ON proofs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_proofs_date ON proofs(date)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_holidays_user ON holidays(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(date)")
            
            # ================= GROUP COMMENTS TABLE =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS group_comments (
                    id SERIAL PRIMARY KEY,
                    group_name TEXT UNIQUE NOT NULL,
                    comment TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_group_comments_name ON group_comments(group_name)")

            # ================= FINES_TARIFFS TABLE =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fines_tariffs (
                    id SERIAL PRIMARY KEY,
                    role TEXT NOT NULL,
                    min_minutes INTEGER NOT NULL,
                    max_minutes INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_tariffs_role ON fines_tariffs(role)")

            # ================= FINES TABLE =================
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fines (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    role TEXT,
                    date TEXT NOT NULL,
                    late_minutes INTEGER DEFAULT 0,
                    amount INTEGER DEFAULT 0,
                    reason TEXT DEFAULT 'late',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_user ON fines(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_date ON fines(date)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_status ON fines(status)")
            logging.info("✅ fines_tariffs va fines jadvallar tayyor")

            # ================= MIGRATION: motivation_index ustuni =================
            await conn.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS motivation_index INTEGER DEFAULT 0
            """)
            
            # ================= OWNER QO'SHISH =================
            await conn.execute("""
                INSERT INTO users (user_id, role, name, work_start, work_end)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO NOTHING
            """, "6500594896", "Owner", "Baxtiyorjon", "09:00", "18:00")
            
            # ================= MIGRATION: Eski ta'tillarni global qilish =================
            # Eski foydalanuvchi-ID bilan saqlangan ta'tillarni global formatga o'tkazish
            try:
                old_holidays = await conn.fetch("""
                    SELECT DISTINCT ON (name, date) name, date, is_repeat
                    FROM holidays
                    WHERE user_id != 'global'
                    ORDER BY name, date
                """)
                for h in old_holidays:
                    existing = await conn.fetchrow(
                        "SELECT id FROM holidays WHERE user_id = 'global' AND name = $1 AND date = $2",
                        h["name"], h["date"]
                    )
                    if not existing:
                        await conn.execute("""
                            INSERT INTO holidays (user_id, user_name, role, name, date, is_repeat)
                            VALUES ('global', 'Global', 'all', $1, $2, $3)
                        """, h["name"], h["date"], h["is_repeat"])
                if old_holidays:
                    await conn.execute("DELETE FROM holidays WHERE user_id != 'global'")
                    logging.info(f"✅ Migration: {len(old_holidays)} ta ta'til global formatga o'tkazildi")
            except Exception as mig_err:
                logging.warning(f"Migration xatosi (muhim emas): {mig_err}")
            
        logging.info("✅ Barcha jadvallar tayyor!")
        
    except Exception as e:
        logging.error(f"❌ Database xatosi: {e}")
        raise


async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
        logging.info("🔒 Database ulanishi yopildi")


def get_pool():
    return db_pool

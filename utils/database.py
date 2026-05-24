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
        
        # Ulanishni tekshirish
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        
        logging.info("✅ PostgreSQL ulandi!")
        
        # Jadvallarni yaratish
        async with db_pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    name TEXT,
                    active_task INTEGER,
                    is_waiting_for_proof BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tasks table
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
            
            # Proofs table
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
            
            # Indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_proofs_user ON proofs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_proofs_date ON proofs(date)")
            
            # Owner (admin) ni qo'shish
            await conn.execute("""
                INSERT INTO users (user_id, role, name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            """, "6500594896", "Owner", "Baxtiyorjon")
            
        logging.info("✅ Barcha jadvallar tayyor va Owner qo'shildi!")
    except Exception as e:
        logging.error(f"❌ Database xatosi: {e}")
        raise

async def close_db():
    """Database pool ni yopish"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logging.info("🔒 Database ulanishi yopildi")

def get_pool():
    return db_pool

"""
Guruh izohlari bilan ishlash uchun modul.
group_comments jadvalidan izohlarni o'qish, yozish, o'chirish.
"""
import logging
from utils.database import get_pool

logger = logging.getLogger(__name__)


async def get_comment(group_name: str) -> str | None:
    """Guruh uchun izohni qaytaradi. Agar izoh bo'lmasa None."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT comment FROM group_comments WHERE group_name = $1",
            group_name
        )
        return row["comment"] if row else None


async def set_comment(group_name: str, comment: str, user_id: str) -> None:
    """Guruhga izoh qo'shadi yoki yangilaydi."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO group_comments (group_name, comment, created_by, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (group_name) DO UPDATE SET
                comment = $2,
                updated_at = NOW()
        """, group_name, comment, user_id)
        logger.info(f"Izoh saqlandi: {group_name[:30]}...")


async def delete_comment(group_name: str) -> bool:
    """Guruh izohini o'chiradi. O'chirilgan bo'lsa True qaytaradi."""
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM group_comments WHERE group_name = $1",
            group_name
        )
        deleted = result == "DELETE 1"
        if deleted:
            logger.info(f"Izoh o'chirildi: {group_name[:30]}...")
        return deleted


async def get_all_comments() -> dict[str, str]:
    """Barcha guruh izohlarini {group_name: comment} lug'atida qaytaradi."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT group_name, comment FROM group_comments")
        return {row["group_name"]: row["comment"] for row in rows}

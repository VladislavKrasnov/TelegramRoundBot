import aiosqlite
from data.settings import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY, "
            "video_note_count INTEGER DEFAULT 0)"
        )
        await db.commit()

async def register_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        if not await cursor.fetchone():
            await db.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            await db.commit()

async def increment_video_note(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET video_note_count = video_note_count + 1 "
            "WHERE id = ?", (user_id,)
        )
        await db.commit()

async def get_profile(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT video_note_count FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
    return {"id": user_id, "video_note_count": row[0] if row else 0}

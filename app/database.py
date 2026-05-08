import aiosqlite
import os
from datetime import datetime
from typing import Optional, List

DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/digitalhuman.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    image_url TEXT,
    video_url TEXT,
    status TEXT DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


async def init_db():
    """Initialize the database and create tables if not exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def create_task(task_id: str, prompt: str, image_url: Optional[str] = None) -> int:
    """Create a new task record, return the row id."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (task_id, prompt, image_url, status) VALUES (?, ?, ?, 'queued')",
            (task_id, prompt, image_url),
        )
        await db.commit()
        return cursor.lastrowid


async def update_task_status(task_id: str, status: str, video_url: Optional[str] = None):
    """Update task status and optionally video_url."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if video_url:
            await db.execute(
                "UPDATE tasks SET status = ?, video_url = ?, updated_at = ? WHERE task_id = ?",
                (status, video_url, datetime.now().isoformat(), task_id),
            )
        else:
            await db.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                (status, datetime.now().isoformat(), task_id),
            )
        await db.commit()


async def get_task(task_id: str) -> Optional[dict]:
    """Get a task by task_id."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_tasks(limit: int = 20) -> List[dict]:
    """Get recent tasks ordered by created_at desc."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

import sqlite3
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_FILE = "tasks.db"

app = FastAPI(title="Task CRUD API")


# ---------- DB helpers ----------

@contextmanager
def get_connection():
    """Every request opens a fresh SQLite connection and closes it afterwards."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the tasks table if missing, and seed it if empty."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    ("Buy groceries", 0),
                    ("Finish FastAPI assignment", 0),
                    ("Read a book", 1),
                ],
            )


@app.on_event("startup")
def on_startup():
    init_db()


# ---------- Schemas ----------

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    done: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    done: Optional[bool] = None


class Task(BaseModel):
    id: int
    title: str
    done: bool


def row_to_task(row: sqlite3.Row) -> Task:
    return Task(id=row["id"], title=row["title"], done=bool(row["done"]))


# ---------- Endpoints ----------

@app.get("/tasks", response_model=list[Task])
def list_tasks():
    with get_connection() as conn:
        rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
        return [row_to_task(r) for r in rows]


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return row_to_task(row)


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (task.title, int(task.done)),
        )
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (new_id,)
        ).fetchone()
        return row_to_task(row)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")

        new_title = existing["title"] if task.title is None else task.title
        new_done = existing["done"] if task.done is None else int(task.done)

        if task.title is not None and not task.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, task_id),
        )
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return None

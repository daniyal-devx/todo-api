import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

DB_PATH = "tasks.db"

app = FastAPI()


# ---------- DB helpers ----------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()

        cursor = conn.execute("SELECT COUNT(*) AS count FROM tasks")
        count = cursor.fetchone()["count"]

        if count == 0:
            seed_tasks = [
                ("Buy groceries", 0),
                ("Write report", 0),
                ("Walk the dog", 1),
            ]
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", seed_tasks
            )
            conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------- Models ----------

class TaskCreate(BaseModel):
    title: str
    done: bool = False


class TaskPut(BaseModel):
    title: str
    done: bool


class TaskCreatePartial(BaseModel):
    # Used only to allow partial JSON bodies for manual validation on PUT
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------- Error handling ----------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        payload = detail
    else:
        payload = {"error": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"detail": payload})


def error(status_code: int, message: str):
    raise HTTPException(status_code=status_code, detail={"error": message})


# ---------- Helpers ----------

def row_to_task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


# ---------- Endpoints ----------

@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
        return [row_to_task(r) for r in rows]
    finally:
        conn.close()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            error(404, f"Task with id {task_id} not found")
        return row_to_task(row)
    finally:
        conn.close()


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (task.title, int(task.done)),
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (new_id,)
        ).fetchone()
        return row_to_task(row)
    finally:
        conn.close()


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    body = await request.json()

    if not isinstance(body, dict) or "title" not in body or "done" not in body:
        error(400, "Both 'title' and 'done' are required for a full update")

    title = body.get("title")
    done = body.get("done")

    if not isinstance(title, str):
        error(400, "'title' must be a string")
    if not isinstance(done, bool):
        error(400, "'done' must be a boolean")

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            error(404, f"Task with id {task_id} not found")

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, int(done), task_id),
        )
        conn.commit()

        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return row_to_task(row)
    finally:
        conn.close()


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            error(404, f"Task with id {task_id} not found")

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return None
    finally:
        conn.close()

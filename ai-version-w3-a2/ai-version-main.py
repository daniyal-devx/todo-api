from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Task API")


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)


@app.on_event("startup")
def startup():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()["count"]
    if count == 0:
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Sample task 1", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Sample task 2", True))
        conn.commit()
    conn.close()


class Task(BaseModel):
    title: str
    done: bool = False


@app.get("/")
def root():
    return {"message": "Task API running"}


@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return rows


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    if not task.title:
        raise HTTPException(status_code=400, detail="Title is required")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (task.title, task.done)
    )
    new_task = cur.fetchone()
    conn.commit()
    conn.close()
    return new_task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
        (task.title, task.done, task_id)
    )
    updated = cur.fetchone()
    conn.commit()
    conn.close()
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Task not found")

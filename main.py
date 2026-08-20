from fastapi import FastAPI,Response, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import psycopg
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app = FastAPI(
    title="To-do API",
    description="A simple CRUD API for managing tasks — built for FlyRank's Backend Track Week 2 assignment.",
    version="1.0.0"
)
@app.get("/", summary="API info", description="Returns basic info about this API: its name, version, and available endpoints.")
def read_root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }
@app.get("/health", summary="Health check", description="Returns a simple status check to confirm the server and database are running.")
def health_check():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "ok", "db": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "error", "db": "unreachable"})
@app.get("/tasks", summary="List all tasks", description="Returns the full list of tasks currently stored in memory.")
def get_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows=cursor.fetchall()
    tasks=[{"id":row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]
    conn.close()
    return tasks
@app.get("/tasks/{id}", summary="Get a single task", description="Returns the task matching the given id. Returns 404 if no task with that id exists.")
def get_task(id:int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    row=cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail={"error":f"Task {id} not found"})
    return {"id":row["id"], "title": row["title"], "done": bool(row["done"])}
class TaskCreate(BaseModel):
    title:str | None=None
@app.post("/tasks", status_code=201, summary="Create a task", description="Creates a new task with the given title. Returns 400 if the title is missing or empty.")
def create_task(task:TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error":"Task title is required"})
    conn = get_connection()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)  RETURNING * ", (task.title, False))
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {"id":new_id, "title":task.title, "done":False}
    
class TaskUpdate(BaseModel):
    title:str 
    done:bool 
@app.put("/tasks/{id}", summary="Update a task", description="Replaces a task's title and done status. Returns 404 if the id doesn't exist, or 400 if the title is missing or empty.")
def update_task(id: int, task: TaskUpdate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Task title is required"})

    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s", (task.title, task.done, id))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    row = cursor.fetchone()
    conn.close()
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
@app.delete("/tasks/{id}", summary="Delete a task", description="Deletes the task matching the given id. Returns 404 if no task with that id exists.")
def delete_task(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})

    return Response(status_code=204)

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)
@app.on_event("startup")
def startup():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()["count"]
    if count == 0:
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", [
            ("something", False),
            ("something else", True),
            ("creating header", False)
        ])
        conn.commit()

    conn.close()
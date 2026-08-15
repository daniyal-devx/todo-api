from fastapi import FastAPI,Response, HTTPException
from pydantic import BaseModel
import sqlite3
app = FastAPI(
    title="To-do API",
    description="A simple CRUD API for managing tasks — built for FlyRank's Backend Track Week 2 assignment.",
    version="1.0.0"
)
tasks = [
    {"id": 1, "title": "something", "done": False},
    {'id': 2, "title": "something else", "done": True},
    {"id": 3, "title": "creating header", "done": False}
]
@app.get("/", summary="API info", description="Returns basic info about this API: its name, version, and available endpoints.")
def read_root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }
@app.get("/health", summary="Health check", description="Returns a simple status check to confirm the server is running.")
def health_check():
    return {"status":"ok"}
@app.get("/tasks", summary="List all tasks", description="Returns the full list of tasks currently stored in memory.")
def get_tasks():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows=cursor.fetchall()
    tasks=[{"id":row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]
    conn.close()
    return tasks
@app.get("/tasks/{id}", summary="Get a single task", description="Returns the task matching the given id. Returns 404 if no task with that id exists.")
def get_task(id:int):
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
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
    conn = sqlite3.connect("tasks.db")
    cursor=conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, 0))
    conn.commit()
    new_id=cursor.lastrowid
    conn.close()
    return {"id":new_id, "title":task.title, "done":False}
    
class TaskUpdate(BaseModel):
    title:str 
    done:bool 
@app.put("/tasks/{id}", summary="Update a task", description="Replaces a task's title and done status. Returns 404 if the id doesn't exist, or 400 if the title is missing or empty.")
def update_task(id: int, task: TaskUpdate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Task title is required"})

    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (task.title, int(task.done), id))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
@app.delete("/tasks/{id}", summary="Delete a task", description="Deletes the task matching the given id. Returns 404 if no task with that id exists.")
def delete_task(id: int):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})

    return Response(status_code=204)
@app.on_event("startup")
def startup():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL
        )
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", [
            ("something", 0),
            ("something else", 1),
            ("creating header", 0)
        ])
        conn.commit()

    conn.close()
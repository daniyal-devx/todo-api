from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Todo API")

# In-memory storage
tasks = [
    {"id": 1, "title": "Sample task 1", "done": False},
    {"id": 2, "title": "Sample task 2", "done": True},
]


class Task(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.get("/")
def read_root():
    return {"message": "Welcome to the Todo API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    return tasks


@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    if not task.title:
        raise HTTPException(status_code=400, detail="Title is required")
    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{id}")
def update_task(id: int, task: TaskUpdate):
    for t in tasks:
        if t["id"] == id:
            if task.title is not None:
                t["title"] = task.title
            if task.done is not None:
                t["done"] = task.done
            return t
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for t in tasks:
        if t["id"] == id:
            tasks.remove(t)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

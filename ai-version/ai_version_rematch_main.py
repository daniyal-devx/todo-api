from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Todo API",
    description="A CRUD API for managing a to-do list, built with FastAPI."
)

# In-memory storage
tasks = [
    {"id": 1, "title": "Sample task 1", "done": False},
    {"id": 2, "title": "Sample task 2", "done": True},
]


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


@app.get("/", summary="API info", description="Returns basic info about this API.")
def read_root():
    return {"name": "Todo API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check", description="Returns server status.")
def health_check():
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks", description="Returns the full list of tasks.")
def get_tasks():
    return tasks


@app.get("/tasks/{id}", summary="Get a single task", description="Returns one task by id. Returns 404 if not found.")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})


@app.post("/tasks", status_code=201, summary="Create a task",
           description="Creates a new task. Returns 400 if title is missing, empty, or whitespace-only.")
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title is required and cannot be empty"})
    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{id}", summary="Update a task",
         description="Replaces a task's title and done status. Both fields are required. "
                      "Returns 404 if id doesn't exist, 400 if title is missing/empty/whitespace-only.")
def update_task(id: int, task: TaskUpdate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title is required and cannot be empty"})
    for t in tasks:
        if t["id"] == id:
            t["title"] = task.title
            t["done"] = task.done
            return t
    raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})


@app.delete("/tasks/{id}", status_code=204, summary="Delete a task",
            description="Deletes a task by id. Returns 404 if not found.")
def delete_task(id: int):
    for t in tasks:
        if t["id"] == id:
            tasks.remove(t)
            return
    raise HTTPException(status_code=404, detail={"error": f"Task {id} not found"})

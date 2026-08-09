from fastapi import FastAPI,Response, HTTPException
from pydantic import BaseModel
app=FastAPI()
tasks = [
    {"id": 1, "title": "something", "done": False},
    {'id': 2, "title": "something else", "done": True},
    {"id": 3, "title": "creating header", "done": False}
]
@app.get("/")
def read_root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }
@app.get('/health')
def health_check():
    return {"status":"ok"}
@app.get("/tasks")
def get_tasks():
    return tasks
@app.get("/tasks/{id}")
def get_task(id:int):
    task = next((task for task in tasks if task["id"] == id), None)
    if task is None:
        raise HTTPException(status_code=404, detail={"error":f"Task {id} not found"})
    return task
class TaskCreate(BaseModel):
    title:str | None=None
@app.post("/tasks", status_code=201)
def create_task(task:TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error":"Task title is required"})
    new_task = {"id": max(t["id"] for t in tasks) +1 if tasks else 1, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task 
class TaskUpdate(BaseModel):
    title:str 
    done:bool 
@app.put("/tasks/{id}")
def update_task(id:int, task:TaskUpdate):
    existing_task=next((task for task in tasks if task["id"]==id), None)
    if existing_task is None:
        raise HTTPException(status_code=404, detail={"error":f"Task {id} not found"})
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail={"error":"Task title is required"})
    existing_task["title"]=task.title
    existing_task["done"]=task.done
    return existing_task
@app.delete("/tasks/{id}")
def delete_task(id:int):
    existing_task=next((task for task in tasks if task['id']==id),None)
    if existing_task is None:
        raise HTTPException(status_code=404, detail={"error":f"Task {id} not found"})
    tasks.remove(existing_task)
    return Response(status_code=204)
    

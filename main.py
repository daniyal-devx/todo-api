from fastapi import FastAPI,Response, HTTPException
from pydantic import BaseModel, ValidationError
import os
from dotenv import load_dotenv
import psycopg
from supabase import create_client, Client
from fastapi import Header
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.llm.schema import TriageInput, TriageOutput, Category, Urgency, extract_json
from openai import OpenAI
import json as jsonlib
from datetime import datetime, timezone
import time
import random
from openai import APITimeoutError, RateLimitError, APIStatusError
load_dotenv()
llm_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    timeout=30.0,
)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
DATABASE_URL = os.getenv("DATABASE_URL")
app = FastAPI(
    title="To-do API",
    description="A simple CRUD API for managing tasks — built for FlyRank's Backend Track Week 2 assignment.",
    version="1.0.0"
)
def load_prompt(filename: str) -> str:
    with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
        return f.read()

TRIAGE_PROMPT = load_prompt("triage-v1.md")

class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None

@app.post("/auth/signup", status_code=201, summary="Sign up a new user", description="Creates a new user account with the provided email and password.")
def sign_up_user(auth: AuthRequest):
    if not auth.email or not auth.email.strip() or not auth.password or not auth.password.strip():
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})
    
    try:
        result = supabase.auth.sign_up({"email": auth.email, "password": auth.password})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "Signup failed — email may already be registered"})
    
    return {"user": result.user}

@app.post("/auth/login", summary="Authenticate user", description="Authenticates a user with the provided email and password.")
def authenticate_user(auth: AuthRequest):
    if not auth.email or not auth.email.strip() or not auth.password or not auth.password.strip():
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})
    
    try:
        result = supabase.auth.sign_in_with_password({"email": auth.email, "password": auth.password})
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})
    
    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token
    }
@app.get("/public/info", summary="Public info", description="Returns a public message, no authentication required.")
def get_public_info():
    return {"message": "Welcome stranger! This info is public."}


bearer_scheme = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    if credentials is None or not credentials.credentials.strip():
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
    
    token = credentials.credentials
    
    try:
        user = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})
    
    return user.user


@app.get("/protected/profile", summary="Get profile (verified)", description="Returns profile data after verifying the bearer token with Supabase. Returns 401 if the token is missing, malformed, invalid, or expired.")
def get_profile(current_user = Depends(verify_token)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }
@app.get("/protected/dashboard", summary="Dashboard (verified)", description="Example second protected route, reusing the same auth guard as /protected/profile.")
def get_dashboard(current_user = Depends(verify_token)):
    return {"message": f"Welcome to your dashboard, {current_user.email}"}


@app.post("/auth/logout", status_code=204, summary="Log out", description="Ends the current user's session. Requires a valid bearer token.")
def logout_user(current_user = Depends(verify_token)):
    try:
        supabase.auth.sign_out()
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})
    
    return Response(status_code=204)
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

def log_quarantine(input_text: str, raw_output: str, error: str):
    os.makedirs("logs", exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
        "prompt_version": "triage-v1",
    }
    with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
        f.write(jsonlib.dumps(entry) + "\n")
def log_cost(prompt_version: str, model: str, input_tokens: int, output_tokens: int, duration_ms: int, repaired: bool):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "repaired": repaired,
    }
    print(jsonlib.dumps(entry))
@app.post("/triage", response_model=TriageOutput, summary="Triage a todo item", description="Classifies messy todo text into a category and urgency level.")
def triage_task(payload: TriageInput):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail={"error": "text is required"})
    if len(payload.text) > 500:
        raise HTTPException(status_code=400, detail={"error": "text must be 500 characters or fewer"})

    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        raise HTTPException(status_code=503, detail={"error": "Triage is temporarily disabled"})

    if os.getenv("LLM_STUB") == "1":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.normal,
            confidence=0.5,
            reason="Stub mode: no model was called."
        )
    try:
        result = call_and_validate(payload.text)
    except (APITimeoutError, RateLimitError, APIStatusError) as e:
        raise HTTPException(status_code=502, detail={"error": "LLM provider error", "detail": str(e)})

    if result is None:
        raise HTTPException(status_code=422, detail={"error": "Model could not produce a valid response after repair attempt"})
    return result
MAX_RETRIES = 2

def call_model_with_retry(messages: list) -> dict:
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            start = time.time()
            response = llm_client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                temperature=0.2,
                messages=messages,
            )
            duration_ms = int((time.time() - start) * 1000)
            return {
                "text": response.choices[0].message.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "duration_ms": duration_ms,
            }
        except (APITimeoutError, RateLimitError) as e:
            last_error = e
        except APIStatusError as e:
            if 500 <= e.status_code < 600:
                last_error = e
            else:
                raise

        if attempt < MAX_RETRIES:
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)

    raise last_error
MAX_REPAIR_ATTEMPTS = 1
def call_and_validate(user_text: str):
    messages = [
        {"role": "system", "content": TRIAGE_PROMPT},
        {"role": "user", "content": user_text},
    ]

    result = call_model_with_retry(messages)
    raw_text = result["text"]

    log_cost(
        prompt_version="triage-v1",
        model=os.environ["LLM_MODEL"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        duration_ms=result["duration_ms"],
        repaired=False,
    )

    try:
        parsed = extract_json(raw_text)
        return TriageOutput(**parsed)
    except (jsonlib.JSONDecodeError, ValidationError) as e:
        # Repair retry: send the broken answer + the error back to the model
        repair_messages = messages + [
            {"role": "assistant", "content": raw_text},
            {"role": "user", "content": f"Your previous answer was rejected for this reason: {e}. Return only corrected JSON matching the schema."}
        ]
        repair_result = call_model_with_retry(repair_messages)
        repair_text = repair_result["text"]

        log_cost(
            prompt_version="triage-v1",
            model=os.environ["LLM_MODEL"],
            input_tokens=repair_result["input_tokens"],
            output_tokens=repair_result["output_tokens"],
            duration_ms=repair_result["duration_ms"],
            repaired=True,
        )

        try:
            parsed = extract_json(repair_text)
            return TriageOutput(**parsed)
        except (jsonlib.JSONDecodeError, ValidationError) as e2:
            log_quarantine(user_text, repair_text, str(e2))
            return None

        
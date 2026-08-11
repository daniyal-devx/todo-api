# Todo API

A simple CRUD API for managing tasks, built with FastAPI. Built as part of FlyRank's Backend Engineering Track, Week 2 assignment.

## What this is

A backend REST API that lets you create, read, update, and delete tasks. Data is stored in memory (no database yet), so it resets when the server restarts.

## How to run it

1. Clone this repo and navigate into it:
   ```bash
   git clone https://github.com/daniyal-devx/todo-api.git
   cd todo-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

5. Open your browser to `http://localhost:8000/docs` to see the interactive Swagger UI.

## Endpoints

| Method | Path          | Description                             | Success | Errors    |
|--------|---------------|------------------------------------------|---------|-----------|
| GET    | `/`           | API info                                 | 200     | -         |
| GET    | `/health`     | Health check                             | 200     | -         |
| GET    | `/tasks`      | List all tasks                           | 200     | -         |
| POST   | `/tasks`      | Create a new task                        | 201     | 400       |
| GET    | `/tasks/{id}` | Get a single task by id                  | 200     | 404       |
| PUT    | `/tasks/{id}` | Replace a task's title and done status   | 200     | 404, 400  |
| DELETE | `/tasks/{id}` | Delete a task by id                      | 204     | 404       |

## Example request

```bash
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
```

```
HTTP/1.1 201 Created
content-type: application/json

{"id":5,"title":"Buy milk","done":false}
```

## Swagger UI

Full CRUD cycle tested via `/docs`.

![Swagger UI showing GET /tasks response](s1.png)

## Notes

- Data is stored in memory only — restarting the server clears all tasks.
- `title` is validated on both create and update: missing or empty (including whitespace-only) titles return a 400 with a clear error message, handled manually rather than relying on FastAPI's default 422 validation error.

## AI vs Me

### My original prompt

> You act as a professional backend ai engineer have to build a curd to-do api you have to use pydantic and fast api frameworks and build the api in python like fastapi swagger ui it should have 5 endpoints get / ,get /tasks , get /tasks {id}, post /tasks, put /tasks/{id}, delete /tasks/{id} and with some explicit status codes like if someone gives unknown id or task title empty during some post , put then some explicit status code with some detail it should use in memory storage.

### What the AI did better

Nothing meaningfully outperformed my own implementation — the AI's first attempt was functional but less strict than mine in the places that actually mattered for this assignment (validation, PUT semantics).

### What it got wrong or quietly ignored

1. **Whitespace-only titles were not rejected.** The AI checked `if not task.title:`, which only catches empty strings — a title of `"   "` passed validation and got saved as a task, unlike my own API which strips whitespace before checking.
2. **PUT behaved as a partial update (PATCH), not a full replacement.** My prompt never said whether `PUT` should require both `title` and `done` or allow either to be omitted. The AI defaulted to making both fields optional, silently preserving the old value for any field the client didn't send — a reasonable design choice, but not what REST convention (or my own hand-built version) intends for `PUT`.
3. **Swagger UI showed generic default labels** ("Read Root," "Get Tasks") instead of descriptive summaries, and error responses used a flat string (`"detail": "Title is required"`) instead of my nested `{"detail": {"error": "..."}}` format.

### What my prompt forgot to specify

I never stated the exact status codes to use, that whitespace-only titles count as empty, or whether `PUT` should require both fields. The AI made reasonable-but-different calls on each of these gaps — proof that a vague spec produces a working API, just not the *same* API.

### The rematch

I rewrote the prompt to explicitly require: rejecting whitespace-only titles (not just empty ones), requiring both `title` and `done` on every `PUT` request, and adding descriptive Swagger summaries to each endpoint. Regenerating from this tightened prompt fixed all three issues — the AI's output now matched my own API's behavior exactly.

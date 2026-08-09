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

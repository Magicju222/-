# AI Excel Cleaner Admin Backend

This is the FastAPI backend for the Admin Panel.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Make sure you have a `.env` file in the project root (or `backend/.env`) with the following keys:
    ```
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_key
    PROJECT_NAME="AI Excel Cleaner Admin API"
    ```

## Running the Server

Run the following command from the **project root** directory (one level up from `backend`):

### Windows (if `python` command fails)
```bash
py -m uvicorn backend.app.main:app --reload --port 8000
```

### Linux/Mac
```bash
uvicorn backend.app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
*   Swagger UI: http://localhost:8000/docs
*   ReDoc: http://localhost:8000/redoc

## Structure

*   `app/main.py`: Entry point.
*   `app/api/v1/endpoints/`: API route handlers (Users, Logs, Config).
*   `app/core/config.py`: Settings and Env Vars.
*   `app/services/`: Business logic and external services (Supabase).

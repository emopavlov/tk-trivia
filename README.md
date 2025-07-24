# tk-trivia

A simple FastAPI application with a `/ping` endpoint.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

3. Test the `/ping` endpoint:
   ```bash
   curl http://localhost:8000/ping
   ```

The server will be available at `http://localhost:8000` and the `/ping` endpoint will return an empty JSON response with status 200.
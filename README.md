# tk-trivia

A simple FastAPI application with a `/ping` endpoint.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. Test the `/ping` endpoint to validate the server is running:
   ```bash
   curl http://localhost:8000/ping
   ```

The server will be available at `http://localhost:8000` and the `/ping` endpoint will return an empty JSON response with status 200.
# tk-trivia

A simple FastAPI application with a `/ping` endpoint and a trivia question endpoint that reads from a CSV database.

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

4. Test the `/question/` endpoint to get a random trivia question:
   ```bash
   curl "http://localhost:8000/question/?round=Jeopardy!&value=\$200"
   ```

The server will be available at `http://localhost:8000`.

## Testing

Run the test suite to verify functionality:
```bash
python -m pytest test_main.py -v
```
## Continuous Integration

The project includes a GitHub Actions workflow that automatically runs tests on every commit to the main branch and on pull requests.

## Endpoints

- **GET `/ping`**: Health check endpoint that returns an empty JSON response with status 200
- **GET `/question/?round={round}&value={value}`**: Returns a random trivia question from the CSV database matching the specified round and value

## Example Response

```json
{
  "question_id": 4680,
  "round": "Jeopardy!",
  "category": "HISTORY",
  "value": "$200",
  "question": "For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory"
}
```

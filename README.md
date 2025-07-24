# tk-trivia

A simple FastAPI application for playing TK Trivia where your answers are judged by an AI bot.

## Prerequsites
1. To run the application you need to create a file called `open_ai_api_key.txt` and put in it your OpenAI api key. If you don't have access to OpenAI's API just leave the file empty and the application will fall back to matching your answers exactly to the expected anwers.

2. You need have `python` 3.9 or newer installed.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

5. Test the `/ping` endpoint to validate the server is running:
   ```bash
   curl http://localhost:8000/ping
   ```

The server will be available at `http://localhost:8000`. See the OpenAPI doc for further details.

## Testing

Run the test suite to verify functionality:
```bash
python -m pytest tests/ -v
```
## Continuous Integration

The project includes a GitHub Actions workflow that automatically runs tests on every commit to the main branch and on pull requests.

## Endpoints

- **GET `/ping`**: Health check endpoint that returns an empty JSON response with status 200

- **GET `/question/?round={round}&value={value}`**: Returns a random trivia question from our database matching the specified round and value
### Example Response

```json
{
   "question_id": 4680,
   "round": "Jeopardy!",
   "category": "HISTORY",
   "value": "$200",
   "question": "For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory"
}
```

- **POST `/verify-answer/`**: Validates the provided answer
#### Example body

```json
{
    "question_id": 4695,
    "user_answer": "Denmark"
}
```

#### Example response
```json
{
   "is_correct": true,
   "ai_response": "Yes, Copernicus proposed the heliocentric theory."
}
```
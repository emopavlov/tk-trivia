import random
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .data_store import trivia_store
from .openai_client import openai_client

logging.basicConfig(
    level=logging.INFO,

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI()


class VerifyAnswerRequest(BaseModel):
    question_id: int
    user_answer: str


class VerifyAnswerResponse(BaseModel):
    correct: bool
    ai_response: str


@app.get("/ping")
def ping():
    return {}


@app.get("/question/")
def get_question(round: str, value: str):
    """
    Get a random question from the CSV database based on round and value.
    
    Args:
        round: The round name (e.g., "Jeopardy!")
        value: The value (e.g., "$200")
    
    Returns:
        A random question matching the criteria
    """
    records = trivia_store.get_all_records()
    
    # Filter records by round and value
    matching_records = [
        record for record in records 
        if record.round == round and record.value == value
    ]
    
    if not matching_records:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for round='{round}' and value='{value}'"
        )
    
    # Select a random record
    selected_record = random.choice(matching_records)
    
    # Return the question data (without the answer)
    return {
        "question_id": selected_record.question_id,
        "round": selected_record.round,
        "category": selected_record.category,
        "value": selected_record.value,
        "question": selected_record.question
    }


@app.post("/verify-answer/", response_model=VerifyAnswerResponse)
async def verify_answer(request: VerifyAnswerRequest):
    """
    Verify a user's answer against the correct answer for a given question ID using AI.
    
    Args:
        request: Contains question_id and user_answer
    
    Returns:
        VerifyAnswerResponse with correct status, AI response, and explanation
    """
    record = trivia_store.get_record_by_question_id(request.question_id)
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Question with ID {request.question_id} not found"
        )
    
    try:
        # Use OpenAI to verify the answer
        ai_result = await openai_client.verify_trivia_answer(
            question=record.question,
            correct_answer=record.answer,
            user_answer=request.user_answer,
            category=record.category
        )
        
        return VerifyAnswerResponse(
            correct=ai_result["is_correct"],
            ai_response=ai_result["explanation"]
        )
    
    except Exception as e:
        # Fallback to simple string comparison if AI verification fails
        is_correct = request.user_answer == record.answer
        return VerifyAnswerResponse(
            correct=is_correct,
            ai_response=record.answer
        )

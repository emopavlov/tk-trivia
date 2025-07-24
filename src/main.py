import random
import logging

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .data_store import trivia_store
from .openai_client import openai_client

logging.basicConfig(
    level=logging.INFO,

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="TK Trivia API",
    description="A FastAPI application for playing TK Trivia where your answers are judged by an AI bot",
    version="0.0.1",
    contact={
        "name": "TK Trivia Support",
        "url": "https://github.com/emopavlov/tk-trivia",
    }
)


class VerifyAnswerRequest(BaseModel):
    """Request model for answer verification"""
    question_id: int = Field(..., description="The unique identifier of the trivia question.", example=4695)
    user_answer: str = Field(..., description="The user's answer to be verified.", example="Denmark")


class VerifyAnswerResponse(BaseModel):
    """Response model for answer verification"""
    correct: bool = Field(..., description="Whether the user's answer is correct", example=True)
    ai_response: str = Field(..., description="AI explanation or the correct answer", example="Yes, Copernicus proposed the heliocentric theory.")


@app.get("/ping", 
         summary="Health Check",
         description="Simple health check endpoint to verify the server is running",
         response_description="Empty JSON object indicating server is healthy",
         tags=["Health"])
def ping():
    return {}


@app.get("/question/",
         summary="Get Random Trivia Question",
         description="Retrieve a random trivia question from the database based on round and value criteria",
         response_description="A trivia question with metadata (without the answer)",
         responses={
             200: {
                 "description": "Successfully retrieved a random question",
                 "content": {
                     "application/json": {
                         "example": {
                             "question_id": 4680,
                             "round": "Jeopardy!",
                             "category": "HISTORY",
                             "value": "$200",
                             "question": "For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory"
                         }
                     }
                 }
             },
             404: {
                 "description": "No questions found matching the criteria",
                 "content": {
                     "application/json": {
                         "example": {
                             "detail": "No questions found for round='Jeopardy!' and value='$200'"
                         }
                     }
                 }
             }
         })
def get_question(
    round: str = Query(..., description="The round name", example="Jeopardy!"),
    value: str = Query(..., description="The point value", example="$200")
):
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


@app.post("/verify-answer/", 
          response_model=VerifyAnswerResponse,
          summary="Verify Trivia Answer",
          description="Verify a user's answer against the correct answer using AI-powered evaluation. Falls back to exact matching if AI is unavailable.",
          response_description="Verification result with AI explanation",
          responses={
              200: {
                  "description": "Successfully verified the answer",
                  "content": {
                      "application/json": {
                          "example": {
                              "correct": True,
                              "ai_response": "Yes, Copernicus proposed the heliocentric theory."
                          }
                      }
                  }
              },
              404: {
                  "description": "Question not found",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Question with ID 4695 not found"
                          }
                      }
                  }
              }
          })
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

import csv
import random
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException

app = FastAPI()


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
    csv_path = Path("resources/JEOPARDY_CSV.csv")
    
    if not csv_path.exists():
        raise HTTPException(status_code=500, detail="CSV database not found")
    
    matching_questions = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Strip whitespace from keys and values to handle CSV formatting
                row = {k.strip(): v.strip() for k, v in row.items()}
                if row['Round'] == round and row['Value'] == value:
                    matching_questions.append({
                        "question_id": int(row['Show Number']),
                        "round": row['Round'],
                        "category": row['Category'],
                        "value": row['Value'],
                        "question": row['Question']
                    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")
    
    if not matching_questions:
        raise HTTPException(
            status_code=404, 
            detail=f"No questions found for round='{round}' and value='{value}'"
        )
    
    # Return a random question from the matching ones
    return random.choice(matching_questions)

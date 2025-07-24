"""
Data access layer for trivia questions.

This module provides an abstraction layer for accessing trivia question data,
hiding the implementation details (CSV file) from the API layer.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel

# Set up logger for this module
logger = logging.getLogger(__name__)


class TriviaRecord(BaseModel):
    """Represents a raw trivia record from the data source"""
    question_id: int
    show_number: int
    air_date: str
    round: str
    category: str
    value: str
    question: str
    answer: str


class TriviaDataStore:
    """Data access layer for trivia questions"""
    
    def __init__(self, data_path: str = "resources/JEOPARDY_CSV.csv"):
        # Resolve path relative to project root (parent of src folder)
        if not Path(data_path).is_absolute():
            src_dir = Path(__file__).parent
            project_root = src_dir.parent
            self.data_path = project_root / data_path
        else:
            self.data_path = Path(data_path)
    
    def get_all_records(self) -> List[TriviaRecord]:
        """Load all records from the data source"""
        if not self.data_path.exists():
            raise HTTPException(status_code=500, detail="Data source not found")
        
        records = []
        try:
            with open(self.data_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for line_number, row in enumerate(reader, start=2):  # Start at 2 since line 1 is headers
                    # Strip whitespace from keys and values to handle CSV formatting
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    
                    record = TriviaRecord(
                        question_id=line_number,
                        show_number=int(row['Show Number']),
                        air_date=row['Air Date'],
                        round=row['Round'],
                        category=row['Category'],
                        value=row['Value'],
                        question=row['Question'],
                        answer=row['Answer']
                    )
                    records.append(record)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading data source: {str(e)}")
        
        logger.info(f"Loaded {len(records)}, last record_id: {records[-1].question_id if records else 'N/A'}")
        return records
    
    def get_record_by_question_id(self, question_id: int) -> Optional[TriviaRecord]:
        """Get a specific record by its question ID (line number in CSV)"""
        records = self.get_all_records()
        
        for record in records:
            if record.question_id == question_id:
                return record
        
        return None


# Global instance - could be configured differently for testing
trivia_store = TriviaDataStore()

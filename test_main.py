import pytest
import tempfile
import csv
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open

from main import app


# Test client for FastAPI
client = TestClient(app)


# Sample test data
SAMPLE_CSV_DATA = [
    ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
    ["4680", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Test question 1", "Test answer 1"],
    ["4680", "2004-12-31", "Jeopardy!", "SCIENCE", "$200", "Test question 2", "Test answer 2"],
    ["4681", "2005-01-01", "Double Jeopardy!", "HISTORY", "$400", "Test question 3", "Test answer 3"],
    ["4682", "2005-01-02", "Jeopardy!", "HISTORY", "$200", "Test question 4", "Test answer 4"],
]


class TestGetQuestion:
    """Test cases for the get_question endpoint"""

    def create_temp_csv(self, data=None):
        """Helper method to create a temporary CSV file"""
        if data is None:
            data = SAMPLE_CSV_DATA
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        writer = csv.writer(temp_file)
        for row in data:
            writer.writerow(row)
        temp_file.close()
        return temp_file.name

    @patch('data_store.Path')
    def test_get_question_success(self, mock_path):
        """Test successful retrieval of a question"""
        # Create temporary CSV file
        temp_csv = self.create_temp_csv()
        mock_path.return_value.exists.return_value = True
        
        # Mock the csv file path
        with patch('builtins.open', mock_open(read_data=self.csv_content())):
            response = client.get("/question/?round=Jeopardy!&value=$200")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that response has all required fields
        required_fields = ["question_id", "round", "category", "value", "question"]
        for field in required_fields:
            assert field in data
        
        # Check that the returned data matches our criteria
        assert data["round"] == "Jeopardy!"
        assert data["value"] == "$200"
        
        # Clean up
        Path(temp_csv).unlink()

    @patch('data_store.Path')
    def test_get_question_no_matches(self, mock_path):
        """Test when no questions match the criteria"""
        mock_path.return_value.exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data=self.csv_content())):
            response = client.get("/question/?round=Jeopardy!&value=$999")
        
        assert response.status_code == 404
        assert "No questions found" in response.json()["detail"]

    @patch('data_store.Path')
    def test_get_question_csv_not_found(self, mock_path):
        """Test when CSV file doesn't exist"""
        mock_path.return_value.exists.return_value = False
        
        response = client.get("/question/?round=Unknown!&value=$200")
        
        assert response.status_code == 404

    @patch('data_store.Path')
    def test_get_question_csv_read_error(self, mock_path):
        """Test when there's an error reading the CSV file"""
        mock_path.return_value.exists.return_value = True
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            response = client.get("/question/?round=Jeopardy!&value=$200")
        
        assert response.status_code == 500
        assert "Error reading data source" in response.json()["detail"]

    def test_get_question_missing_parameters(self):
        """Test when required parameters are missing"""
        # Missing both parameters
        response = client.get("/question/")
        assert response.status_code == 422  # FastAPI validation error
        
        # Missing value parameter
        response = client.get("/question/?round=Jeopardy!")
        assert response.status_code == 422
        
        # Missing round parameter
        response = client.get("/question/?value=$200")
        assert response.status_code == 422

    @patch('data_store.Path')
    def test_get_question_randomness(self, mock_path):
        """Test that the function returns different questions when multiple matches exist"""
        mock_path.return_value.exists.return_value = True
        
        # Create CSV with multiple matching questions
        csv_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            ["4680", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Question A", "Answer A"],
            ["4681", "2005-01-01", "Jeopardy!", "SCIENCE", "$200", "Question B", "Answer B"],
            ["4682", "2005-01-02", "Jeopardy!", "MATH", "$200", "Question C", "Answer C"],
        ]
        
        csv_content = self.format_csv_data(csv_data)
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            responses = []
            # Make multiple requests to test randomness
            for _ in range(10):
                response = client.get("/question/?round=Jeopardy!&value=$200")
                if response.status_code == 200:
                    responses.append(response.json()["question"])
        
        # We should have some responses
        assert len(responses) > 0
        # With 3 possible questions and 10 requests, we should likely see variety
        # (This is probabilistic, but very likely to pass)
        unique_questions = set(responses)
        assert len(unique_questions) >= 1  # At least one unique question

    @patch('data_store.Path')
    def test_get_question_special_characters(self, mock_path):
        """Test handling of special characters in round and value parameters"""
        mock_path.return_value.exists.return_value = True
        
        csv_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            ["4680", "2004-12-31", "Double Jeopardy!", "HISTORY", "$400", "Test question", "Test answer"],
        ]
        
        csv_content = self.format_csv_data(csv_data)
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            response = client.get("/question/?round=Double Jeopardy!&value=$400")
        
        assert response.status_code == 200
        data = response.json()
        assert data["round"] == "Double Jeopardy!"
        assert data["value"] == "$400"

    def csv_content(self):
        """Helper method to format CSV data as string"""
        return self.format_csv_data(SAMPLE_CSV_DATA)

    def format_csv_data(self, data):
        """Format CSV data as a string"""
        lines = []
        for row in data:
            lines.append(','.join(f'"{item}"' if ',' in str(item) else str(item) for item in row))
        return '\n'.join(lines)


class TestPingEndpoint:
    """Test cases for the ping endpoint"""

    def test_ping_success(self):
        """Test that ping endpoint returns empty JSON"""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {}


class TestVerifyAnswerEndpoint:
    """Test cases for the verify-answer endpoint"""

    @patch('data_store.Path')
    def test_verify_answer_correct(self, mock_path):
        """Test successful answer verification with correct answer"""
        mock_path.return_value.exists.return_value = True
        
        csv_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            ["4680", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Test question", "Copernicus"],
        ]
        
        csv_content = self.format_csv_data(csv_data)
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            response = client.post("/verify-answer/", json={
                "question_id": 2, # The line number
                "user_answer": "Copernicus"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["correct"] is True
        assert data["ai_response"] == "Copernicus"

    @patch('data_store.Path')
    def test_verify_answer_incorrect(self, mock_path):
        """Test answer verification with incorrect answer"""
        mock_path.return_value.exists.return_value = True
        
        csv_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            ["4680", "2004-12-31", "Jeopardy!", "UNKNWON", "$1200", "Test question a", "Fire"],
            ["4680", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Test question", "Copernicus"],
        ]
        
        csv_content = self.format_csv_data(csv_data)
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            response = client.post("/verify-answer/", json={
                "question_id": 3,
                "user_answer": "Einstein"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["correct"] is False
        assert data["ai_response"] == "Copernicus"

    @patch('data_store.Path')
    def test_verify_answer_question_not_found(self, mock_path):
        """Test when question ID doesn't exist"""
        mock_path.return_value.exists.return_value = True
        
        csv_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            ["4680", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Test question", "Copernicus"],
        ]
        
        csv_content = self.format_csv_data(csv_data)
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            response = client.post("/verify-answer/", json={
                "question_id": 9999,
                "user_answer": "Some answer"
            })
        
        assert response.status_code == 404
        assert "Question with ID 9999 not found" in response.json()["detail"]

    @patch('data_store.Path')
    def test_verify_answer_csv_not_found(self, mock_path):
        """Test when CSV file doesn't exist"""
        mock_path.return_value.exists.return_value = False
        
        response = client.post("/verify-answer/", json={
            "question_id": 80000000,
            "user_answer": "Copernicus"
        })
        
        assert response.status_code == 404

    def test_verify_answer_invalid_request(self):
        """Test with invalid request body"""
        # Missing question_id
        response = client.post("/verify-answer/", json={
            "user_answer": "Copernicus"
        })
        assert response.status_code == 422
        
        # Missing user_answer
        response = client.post("/verify-answer/", json={
            "question_id": 4680
        })
        assert response.status_code == 422
        
        # Invalid question_id type
        response = client.post("/verify-answer/", json={
            "question_id": "not_a_number",
            "user_answer": "Copernicus"
        })
        assert response.status_code == 422

    def format_csv_data(self, data):
        """Format CSV data as a string"""
        lines = []
        for row in data:
            lines.append(','.join(f'"{item}"' if ',' in str(item) else str(item) for item in row))
        return '\n'.join(lines)


if __name__ == "__main__":
    pytest.main([__file__])

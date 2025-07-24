import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, mock_open
from fastapi import HTTPException

from data_store import TriviaRecord, TriviaDataStore, trivia_store


# Sample test data
SAMPLE_CSV_DATA = [
    ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
    ["4680", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Test question 1", "Test answer 1"],
    ["4681", "2004-12-31", "Jeopardy!", "SCIENCE", "$200", "Test question 2", "Test answer 2"],
    ["4682", "2005-01-01", "Double Jeopardy!", "HISTORY", "$400", "Test question 3", "Test answer 3"],
    ["4683", "2005-01-02", "Jeopardy!", "HISTORY", "$200", "Test question 4", "Test answer 4"],
]


class TestTriviaRecord:
    """Test cases for the TriviaRecord model"""

    def test_trivia_record_creation(self):
        """Test creating a TriviaRecord with valid data"""
        record = TriviaRecord(
            question_id=1,
            show_number=4680,
            air_date="2004-12-31",
            round="Jeopardy!",
            category="HISTORY",
            value="$200",
            question="Test question",
            answer="Test answer"
        )
        
        assert record.question_id == 1
        assert record.show_number == 4680
        assert record.air_date == "2004-12-31"
        assert record.round == "Jeopardy!"
        assert record.category == "HISTORY"
        assert record.value == "$200"
        assert record.question == "Test question"
        assert record.answer == "Test answer"

    def test_trivia_record_validation(self):
        """Test TriviaRecord field validation"""
        # Test with invalid show_number (not an integer)
        with pytest.raises(ValueError):
            TriviaRecord(
                question_id=1,
                show_number="invalid",
                air_date="2004-12-31",
                round="Jeopardy!",
                category="HISTORY",
                value="$200",
                question="Test question",
                answer="Test answer"
            )

    def test_trivia_record_dict_conversion(self):
        """Test converting TriviaRecord to dictionary"""
        record = TriviaRecord(
            question_id=2,
            show_number=4681,
            air_date="2004-12-31",
            round="Jeopardy!",
            category="SCIENCE",
            value="$200",
            question="Test question 2",
            answer="Test answer 2"
        )
        
        record_dict = record.dict()
        
        assert record_dict["question_id"] == 2
        assert record_dict["show_number"] == 4681
        assert record_dict["air_date"] == "2004-12-31"
        assert record_dict["round"] == "Jeopardy!"
        assert record_dict["category"] == "SCIENCE"
        assert record_dict["value"] == "$200"
        assert record_dict["question"] == "Test question 2"
        assert record_dict["answer"] == "Test answer 2"


class TestTriviaDataStore:
    """Test cases for the TriviaDataStore class"""

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

    def csv_content(self):
        """Helper method to generate CSV content as string"""
        lines = []
        for row in SAMPLE_CSV_DATA:
            lines.append(','.join(row))
        return '\n'.join(lines)

    def test_init_default_path(self):
        """Test TriviaDataStore initialization with default path"""
        store = TriviaDataStore()
        assert str(store.data_path) == "resources/JEOPARDY_CSV.csv"

    def test_init_custom_path(self):
        """Test TriviaDataStore initialization with custom path"""
        custom_path = "/custom/path/data.csv"
        store = TriviaDataStore(custom_path)
        assert str(store.data_path) == custom_path

    def test_get_all_records_success(self):
        """Test successfully loading all records from CSV"""
        # Create temporary CSV file
        temp_csv = self.create_temp_csv()
        
        try:
            store = TriviaDataStore(temp_csv)
            records = store.get_all_records()
            
            # Should have 4 data records (excluding header)
            assert len(records) == 4
            
            # Check first record
            first_record = records[0]
            assert first_record.question_id == 2  # Line 2 in CSV (after header)
            assert first_record.show_number == 4680
            assert first_record.air_date == "2004-12-31"
            assert first_record.round == "Jeopardy!"
            assert first_record.category == "HISTORY"
            assert first_record.value == "$200"
            assert first_record.question == "Test question 1"
            assert first_record.answer == "Test answer 1"
            
            # Check last record
            last_record = records[3]
            assert last_record.question_id == 5  # Line 5 in CSV
            assert last_record.show_number == 4683
            
            # Verify question_id increments correctly
            for i, record in enumerate(records):
                assert record.question_id == i + 2  # Starting from line 2
                
        finally:
            # Clean up
            Path(temp_csv).unlink()

    def test_get_all_records_file_not_found(self):
        """Test handling when CSV file doesn't exist"""
        store = TriviaDataStore("nonexistent_file.csv")
        
        with pytest.raises(HTTPException) as exc_info:
            store.get_all_records()
        
        assert exc_info.value.status_code == 500
        assert "Data source not found" in str(exc_info.value.detail)

    @patch('builtins.open')
    def test_get_all_records_read_error(self, mock_open_func):
        """Test handling CSV read errors"""
        mock_open_func.side_effect = IOError("Permission denied")
        
        # Create a real file to pass the exists() check
        temp_csv = self.create_temp_csv()
        
        try:
            store = TriviaDataStore(temp_csv)
            
            with pytest.raises(HTTPException) as exc_info:
                store.get_all_records()
            
            assert exc_info.value.status_code == 500
            assert "Error reading data source" in str(exc_info.value.detail)
            assert "Permission denied" in str(exc_info.value.detail)
            
        finally:
            Path(temp_csv).unlink()

    def test_get_all_records_invalid_show_number(self):
        """Test handling invalid show number in CSV"""
        invalid_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            ["invalid_number", "2004-12-31", "Jeopardy!", "HISTORY", "$200", "Test question", "Test answer"],
        ]
        
        temp_csv = self.create_temp_csv(invalid_data)
        
        try:
            store = TriviaDataStore(temp_csv)
            
            with pytest.raises(HTTPException) as exc_info:
                store.get_all_records()
            
            assert exc_info.value.status_code == 500
            assert "Error reading data source" in str(exc_info.value.detail)
            
        finally:
            Path(temp_csv).unlink()

    def test_get_all_records_whitespace_handling(self):
        """Test that whitespace is properly stripped from CSV fields"""
        data_with_whitespace = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
            [" 4680 ", " 2004-12-31 ", " Jeopardy! ", " HISTORY ", " $200 ", " Test question ", " Test answer "],
        ]
        
        temp_csv = self.create_temp_csv(data_with_whitespace)
        
        try:
            store = TriviaDataStore(temp_csv)
            records = store.get_all_records()
            
            assert len(records) == 1
            record = records[0]
            
            # All fields should have whitespace stripped
            assert record.show_number == 4680
            assert record.air_date == "2004-12-31"
            assert record.round == "Jeopardy!"
            assert record.category == "HISTORY"
            assert record.value == "$200"
            assert record.question == "Test question"
            assert record.answer == "Test answer"
            
        finally:
            Path(temp_csv).unlink()

    def test_get_record_by_question_id_found(self):
        """Test successfully finding a record by question_id"""
        temp_csv = self.create_temp_csv()
        
        try:
            store = TriviaDataStore(temp_csv)
            
            # Get record with question_id = 3 (third data row, line 4 in CSV)
            record = store.get_record_by_question_id(3)
            
            assert record is not None
            assert record.question_id == 3
            assert record.show_number == 4681
            assert record.category == "SCIENCE"
            assert record.question == "Test question 2"
            
        finally:
            Path(temp_csv).unlink()

    def test_get_record_by_question_id_not_found(self):
        """Test when question_id doesn't exist"""
        temp_csv = self.create_temp_csv()
        
        try:
            store = TriviaDataStore(temp_csv)
            
            # Try to get record with non-existent question_id
            record = store.get_record_by_question_id(999)
            
            assert record is None
            
        finally:
            Path(temp_csv).unlink()

    def test_get_record_by_question_id_edge_cases(self):
        """Test edge cases for get_record_by_question_id"""
        temp_csv = self.create_temp_csv()
        
        try:
            store = TriviaDataStore(temp_csv)
            
            # Test with question_id = 2 (first data row)
            first_record = store.get_record_by_question_id(2)
            assert first_record is not None
            assert first_record.question_id == 2
            assert first_record.show_number == 4680
            
            # Test with question_id = 5 (last data row)
            last_record = store.get_record_by_question_id(5)
            assert last_record is not None
            assert last_record.question_id == 5
            assert last_record.show_number == 4683
            
            # Test with question_id = 1 (header row - should not exist)
            header_record = store.get_record_by_question_id(1)
            assert header_record is None
            
        finally:
            Path(temp_csv).unlink()


class TestGlobalTriviaStore:
    """Test cases for the global trivia_store instance"""

    def test_global_instance_exists(self):
        """Test that global trivia_store instance exists"""
        assert trivia_store is not None
        assert isinstance(trivia_store, TriviaDataStore)

    def test_global_instance_default_path(self):
        """Test that global instance uses default path"""
        assert str(trivia_store.data_path) == "resources/JEOPARDY_CSV.csv"


class TestIntegration:
    """Integration tests for TriviaDataStore with real-like data"""

    def test_empty_csv_file(self):
        """Test handling of empty CSV file (only headers)"""
        empty_data = [
            ["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"],
        ]
        
        temp_csv = self.create_temp_csv(empty_data)
        
        try:
            store = TriviaDataStore(temp_csv)
            records = store.get_all_records()
            
            assert len(records) == 0
            
        finally:
            Path(temp_csv).unlink()

    def test_large_dataset_simulation(self):
        """Test with a larger dataset to simulate real usage"""
        # Generate 100 test records
        large_data = [["Show Number", "Air Date", "Round", "Category", "Value", "Question", "Answer"]]
        
        for i in range(100):
            large_data.append([
                str(4680 + i),
                "2004-12-31",
                "Jeopardy!" if i % 2 == 0 else "Double Jeopardy!",
                f"CATEGORY_{i % 10}",
                f"${200 + (i % 5) * 200}",
                f"Test question {i + 1}",
                f"Test answer {i + 1}"
            ])
        
        temp_csv = self.create_temp_csv(large_data)
        
        try:
            store = TriviaDataStore(temp_csv)
            records = store.get_all_records()
            
            assert len(records) == 100
            
            # Test question_id assignment
            for i, record in enumerate(records):
                assert record.question_id == i + 2  # Starting from line 2
                assert record.show_number == 4680 + i
                assert record.question == f"Test question {i + 1}"
            
            # Test finding records by question_id
            middle_record = store.get_record_by_question_id(52)  # 51st record (line 52)
            assert middle_record is not None
            assert middle_record.show_number == 4730  # 4680 + 50
            assert middle_record.question == "Test question 51"
            
        finally:
            Path(temp_csv).unlink()

    def create_temp_csv(self, data):
        """Helper method to create a temporary CSV file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        writer = csv.writer(temp_file)
        for row in data:
            writer.writerow(row)
        temp_file.close()
        return temp_file.name

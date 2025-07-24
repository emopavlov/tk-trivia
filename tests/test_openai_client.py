"""
Test module for the OpenAI client functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, mock_open
import json

from src.openai_client import OpenAIClient


class TestOpenAIClient:
    
    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        client = OpenAIClient(api_key="test-key")
        assert client.api_key == "test-key"
    
    @patch("builtins.open", mock_open(read_data="test-api-key-from-file"))
    def test_init_load_from_file(self):
        """Test loading API key from file."""
        client = OpenAIClient()
        assert client.api_key == "test-api-key-from-file"
    
    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_init_file_not_found(self, mock_open_func):
        """Test error when API key file is not found."""
        with pytest.raises(ValueError, match="API key file not found"):
            OpenAIClient()
    
    @pytest.mark.asyncio
    async def test_verify_trivia_answer_success(self):
        """Test successful trivia answer verification."""
        client = OpenAIClient(api_key="test-key")
        
        # Mock the HTTP response
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '{"is_correct": true, "explanation": "The answer is correct."}'
                }
            }]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            # Create a mock async context manager
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Create a mock response - make json() async
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.raise_for_status = AsyncMock()
            mock_context.post.return_value = mock_response
            
            result = await client.verify_trivia_answer(
                question="What is the capital of France?",
                correct_answer="Paris",
                user_answer="Paris",
                category="Geography"
            )
            
            assert result["is_correct"] is True
            assert result["explanation"] == "The answer is correct."
            assert "raw_ai_response" in result
    
    @pytest.mark.asyncio
    async def test_verify_trivia_answer_invalid_json(self):
        """Test handling of invalid JSON response from AI."""
        client = OpenAIClient(api_key="test-key")
        
        # Mock the HTTP response with invalid JSON
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON"
                }
            }]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            # Create a mock async context manager
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Create a mock response - make json() async
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.raise_for_status = AsyncMock()
            mock_context.post.return_value = mock_response
            
            result = await client.verify_trivia_answer(
                question="What is the capital of France?",
                correct_answer="Paris",
                user_answer="Paris"
            )
            
            assert result["is_correct"] is False
            assert result["explanation"] == "Error parsing AI response"
            assert result["raw_ai_response"] == "This is not valid JSON"
    
    @pytest.mark.asyncio
    async def test_verify_trivia_answer_http_error(self):
        """Test handling of HTTP errors."""
        client = OpenAIClient(api_key="test-key")
        
        with patch("httpx.AsyncClient") as mock_client:
            # Create a mock async context manager
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Make the post method raise an exception
            mock_context.post.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Unexpected error calling OpenAI API"):
                await client.verify_trivia_answer(
                    question="What is the capital of France?",
                    correct_answer="Paris",
                    user_answer="Paris"
                )

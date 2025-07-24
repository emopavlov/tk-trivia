import json
import logging
import os
import sys
from typing import Optional

import httpx

# Set up logger for this module
logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI's Chat Completions API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to read from file.
        """
        self.api_key = api_key or self._load_api_key()
        self.base_url = "https://api.openai.com/v1"
        logger.debug(f"OpenAI client initialized with API key: {self.api_key[:10]}...")
        logger.debug(f"OpenAI base URL: {self.base_url}")
        
    def _load_api_key(self) -> str:
        """Load API key from the open_ai_api_key.txt file."""
        try:
            # Get the project root directory (parent of src)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            key_file_path = os.path.join(project_root, "open_ai_api_key.txt")
            
            logger.debug(f"Loading API key from: {key_file_path}")
            
            with open(key_file_path, "r") as f:
                api_key = f.read().strip()
                logger.info(f"Successfully loaded API key from file: {api_key[:10]}...")
                return api_key
        except FileNotFoundError:
            logger.error(f"API key file not found at: {key_file_path}")
            raise ValueError("API key file not found. Please provide api_key parameter or create open_ai_api_key.txt")
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
            raise ValueError(f"Error loading API key: {e}")
    
    async def verify_trivia_answer(
        self, 
        question: str, 
        correct_answer: str, 
        user_answer: str,
        category: str = ""
    ) -> dict:
        """
        Verify if a user's trivia answer is correct using OpenAI.
        
        Args:
            question: The trivia question
            correct_answer: The known correct answer
            user_answer: The user's submitted answer
            category: Optional category for additional context
        
        Returns:
            Dictionary with 'is_correct' boolean and 'explanation' string
        """
        logger.info(f"Verifying trivia answer for question: {question[:50]}...")
        logger.debug(f"Question: {question}")
        logger.debug(f"Correct answer: {correct_answer}")
        logger.debug(f"User answer: {user_answer}")
        logger.debug(f"Category: {category}")
        
        # Construct the prompt for OpenAI
        category_context = f" from the category '{category}'" if category else ""
        prompt = f"""
You are a trivia judge. Given the following trivia question{category_context}, evaluate if the user's answer is correct.

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Consider that trivia answers may have slight variations in wording, abbreviations, or format while still being essentially correct. Be reasonable in your judgment.

Respond with a JSON object containing:
- "is_correct": boolean (true if the answer is correct or reasonably equivalent)
- "explanation": string (brief explanation of your judgment)

Example response:
{{"is_correct": true, "explanation": "The user's answer 'Paris, France' is correct, even though the exact answer was 'Paris'."}}
"""

        logger.debug(f"Generated prompt: {prompt}")

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for consistent judgments
            "max_tokens": 200
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                logger.debug(f"Making OpenAI API request to {self.base_url}/chat/completions")
                logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
                logger.debug(f"Request headers: {dict(headers)}")
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                # Safe logging for mock compatibility
                try:
                    logger.debug(f"OpenAI API response status: {response.status_code}")
                except (TypeError, AttributeError):
                    logger.debug("OpenAI API response status: <mocked response>")
                    
                try:
                    logger.debug(f"OpenAI API response headers: {dict(response.headers)}")
                except (TypeError, AttributeError):
                    logger.debug("OpenAI API response headers: <mocked headers>")
                
                response.raise_for_status()
                
                # Handle both real httpx response and mocked response
                try:
                    result = await response.json()
                except TypeError:
                    # Handle case where response.json() is not awaitable (e.g., in tests)
                    result = response.json()
                
                try:
                    logger.debug(f"OpenAI API response body: {json.dumps(result, indent=2)}")
                except (TypeError, AttributeError):
                    logger.debug(f"OpenAI API response body: {result}")
                
                ai_response_content = result["choices"][0]["message"]["content"]
                logger.debug(f"AI response content: {ai_response_content}")
                
                # Parse the JSON response from the AI
                try:
                    parsed_response = json.loads(ai_response_content)
                    final_result = {
                        "is_correct": parsed_response.get("is_correct", False),
                        "explanation": parsed_response.get("explanation", "Unable to parse AI response"),
                        "raw_ai_response": ai_response_content
                    }
                    logger.debug(f"Parsed final result: {final_result}")
                    return final_result
                except json.JSONDecodeError as json_error:
                    logger.warning(f"Failed to parse AI response as JSON: {json_error}")
                    logger.debug(f"Raw AI response that failed to parse: {ai_response_content}")
                    # Fallback if AI doesn't return valid JSON
                    fallback_result = {
                        "is_correct": False,
                        "explanation": "Error parsing AI response",
                        "raw_ai_response": ai_response_content
                    }
                    logger.debug(f"Using fallback result: {fallback_result}")
                    return fallback_result
                    
            except httpx.HTTPError as e:
                logger.error(f"OpenAI API HTTP error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Error response status: {e.response.status_code}")
                    logger.error(f"Error response body: {e.response.text}")
                raise Exception(f"OpenAI API request failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI API: {e}")
                raise Exception(f"Unexpected error calling OpenAI API: {e}")


def _is_test_environment() -> bool:
    """Check if we're running in a test environment."""
    return (
        "pytest" in sys.modules or 
        "test" in sys.argv[0] or 
        any("test" in arg for arg in sys.argv)
    )


# Global instance to be used throughout the application
# Use a test API key when running tests to avoid loading the real one
if _is_test_environment():
    logger.info("Creating OpenAI client for test environment")
    openai_client = OpenAIClient(api_key="test-api-key-for-testing")
else:
    logger.info("Creating OpenAI client for production environment")
    openai_client = OpenAIClient()

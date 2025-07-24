import json
import os
from typing import Optional

import httpx


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
        
    def _load_api_key(self) -> str:
        """Load API key from the open_ai_api_key.txt file."""
        try:
            # Get the project root directory (parent of src)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            key_file_path = os.path.join(project_root, "open_ai_api_key.txt")
            
            with open(key_file_path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise ValueError("API key file not found. Please provide api_key parameter or create open_ai_api_key.txt")
        except Exception as e:
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
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = await response.json()
                ai_response_content = result["choices"][0]["message"]["content"]
                
                # Parse the JSON response from the AI
                try:
                    parsed_response = json.loads(ai_response_content)
                    return {
                        "is_correct": parsed_response.get("is_correct", False),
                        "explanation": parsed_response.get("explanation", "Unable to parse AI response"),
                        "raw_ai_response": ai_response_content
                    }
                except json.JSONDecodeError:
                    # Fallback if AI doesn't return valid JSON
                    return {
                        "is_correct": False,
                        "explanation": "Error parsing AI response",
                        "raw_ai_response": ai_response_content
                    }
                    
            except httpx.HTTPError as e:
                raise Exception(f"OpenAI API request failed: {e}")
            except Exception as e:
                raise Exception(f"Unexpected error calling OpenAI API: {e}")


# Global instance to be used throughout the application
openai_client = OpenAIClient()

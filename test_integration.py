#!/usr/bin/env python3
"""
Simple test script to verify the OpenAI integration works end-to-end.
This script will start the FastAPI server temporarily and make test requests.
"""

import asyncio
import httpx
import json
import time
from multiprocessing import Process
import uvicorn
import os


def start_server():
    """Start the FastAPI server."""
    os.chdir("/Users/epavlov/Playground/github/tk-trivia")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, log_level="info")


async def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test ping endpoint
            print("Testing ping endpoint...")
            response = await client.get(f"{base_url}/ping")
            print(f"Ping response: {response.status_code} - {response.json()}")
            
            # Test getting a question
            print("\nTesting get question endpoint...")
            response = await client.get(f"{base_url}/question/?round=Jeopardy!&value=$200")
            if response.status_code == 200:
                question_data = response.json()
                print(f"Question response: {json.dumps(question_data, indent=2)}")
                
                # Test verifying an answer (this will call OpenAI)
                print("\nTesting verify answer endpoint (calls OpenAI)...")
                verify_payload = {
                    "question_id": question_data["question_id"],
                    "user_answer": "test answer"
                }
                
                response = await client.post(
                    f"{base_url}/verify-answer/", 
                    json=verify_payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    verify_data = response.json()
                    print(f"Verify response: {json.dumps(verify_data, indent=2)}")
                else:
                    print(f"Verify failed: {response.status_code} - {response.text}")
            else:
                print(f"Get question failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error testing API: {e}")


async def main():
    """Main test function."""
    print("Starting FastAPI server...")
    server_process = Process(target=start_server)
    server_process.start()
    
    # Wait for server to start
    print("Waiting for server to start...")
    await asyncio.sleep(3)
    
    try:
        await test_api()
    finally:
        print("\nShutting down server...")
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    asyncio.run(main())

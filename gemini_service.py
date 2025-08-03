# gemini_service.py

import os
import httpx
from fastapi import HTTPException

# --- Gemini API Configuration ---
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"

async def generate_sql_from_gemini(schema_ddl: str, business_logic: str) -> str:
    """
    Asynchronously calls the Gemini API to generate a SQL query.
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not set.")

    prompt = f"""
    You are an expert PostgreSQL developer. Your task is to translate a user's business logic into a precise and executable PostgreSQL query based on the provided database schema.

    **Instructions:**
    1.  Analyze the database schema below to understand the table structures, columns, and relationships.
    2.  Read the user's business logic carefully.
    3.  Generate a single, clean, and correct PostgreSQL query that fulfills the user's request with no "\n" please.
    4.  Do not include any explanations, comments, or markdown formatting in your response. Only output the raw SQL query.

    **Database Schema (DDL):**
    ```sql
    {schema_ddl}
    ```

    **User's Business Logic:**
    "{business_logic}"

    **Generated PostgreSQL Query:**
    """
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            if (result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts") and result["candidates"][0]["content"]["parts"][0].get("text")):
                generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return generated_text.strip().replace("```sql", "").replace("```", "").strip()
            else:
                raise HTTPException(status_code=500, detail="Could not parse the response from the AI model.")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service Unavailable: Could not connect to the AI model: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

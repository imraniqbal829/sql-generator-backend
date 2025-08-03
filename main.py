# main.py

from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import asyncio


# --- Constants ---
# Define a directory to store the uploaded schema file.
UPLOAD_DIR = "uploads"
SCHEMA_FILE_PATH = os.path.join(UPLOAD_DIR, "schema.sql")


# --- Pydantic Models for Request and Response ---
class SQLRequest(BaseModel):
    """
    Defines the structure for the SQL generation request.
    Now, it only requires the business logic, as the schema is pre-uploaded.
    """
    business_logic: str

class SQLResponse(BaseModel):
    """
    Defines the structure of the outgoing response.
    It will contain the generated SQL query.
    """
    sql_query: str

class UploadResponse(BaseModel):
    """
    Defines the success message for the file upload.
    """
    message: str
    filename: str


# --- FastAPI Application Initialization ---
app = FastAPI(
    title="SQL Generator API",
    description="An API that uses Gemini to translate business logic into a SQL query based on a pre-uploaded database schema.",
    version="1.1.0",
)

# --- CORS Middleware Configuration ---
# This allows your frontend (e.g., running on localhost:3000) to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # The origin of your frontend application
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"], # Allow all headers
)

# --- Application Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    This function runs when the application starts up.
    It ensures the directory for storing the schema file exists.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)


# --- Gemini API Configuration ---
# Load the API key from an environment variable for better security.
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"


# --- Helper Function to Call Gemini ---
async def generate_sql_from_gemini(schema_ddl: str, business_logic: str) -> str:
    """
    Asynchronously calls the Gemini API to generate a SQL query.
    (This function remains largely the same)
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not set. Please configure the API key.")

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
            for i in range(3):
                response = await client.post(GEMINI_API_URL, json=payload)
                if response.status_code == 200:
                    break
                await asyncio.sleep(2 ** i)
            response.raise_for_status()
            result = response.json()
            if (result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts") and result["candidates"][0]["content"]["parts"][0].get("text")):
                generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return generated_text.strip().replace("```sql", "").replace("```", "").strip()
            else:
                print("Error: Unexpected response structure from Gemini API:", result)
                raise HTTPException(status_code=500, detail="Could not parse the response from the AI model.")
        except httpx.RequestError as e:
            print(f"Error calling Gemini API: {e}")
            raise HTTPException(status_code=503, detail="Service Unavailable: Could not connect to the AI model.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An internal server error occurred.")


# --- API Endpoints ---

@app.post("/upload-schema/", response_model=UploadResponse)
async def upload_ddl_schema(file: UploadFile = File(..., description="The dump.sql file containing the DDL schema.")):
    """
    Uploads a `dump.sql` file. The schema within this file is stored
    on the server and used for subsequent calls to `/generate-sql/`.
    """
    try:
        # Read the contents of the uploaded file
        contents = await file.read()
        # Write the contents to our designated schema file path
        with open(SCHEMA_FILE_PATH, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"There was an error uploading the file: {e}")
    finally:
        await file.close()

    return UploadResponse(message=f"Successfully uploaded and saved schema from {file.filename}", filename=file.filename)


@app.post("/generate-sql/", response_model=SQLResponse)
async def generate_sql_endpoint(request: SQLRequest):
    """
    Generates a SQL query based on the previously uploaded schema and
    the provided business logic.
    """
    # Check if the schema file exists before proceeding.
    if not os.path.exists(SCHEMA_FILE_PATH):
        raise HTTPException(
            status_code=400,
            detail="No schema file found. Please upload your dump.sql file to the /upload-ddl-schema/ endpoint first."
        )

    # Read the schema from the stored file.
    with open(SCHEMA_FILE_PATH, "r") as f:
        schema_ddl = f.read()

    if not request.business_logic:
        raise HTTPException(status_code=400, detail="Business logic must not be empty.")

    # Call the helper function to interact with the Gemini model
    generated_query = await generate_sql_from_gemini(
        schema_ddl=schema_ddl,
        business_logic=request.business_logic
    )

    return SQLResponse(sql_query=generated_query)


@app.get("/test/", response_model=str)
async def say_hello():
    return "Hello, world!"

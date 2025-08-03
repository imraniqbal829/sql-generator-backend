# main.py

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import asyncpg
from typing import List, Dict, Any

# Import functions from the new service and database files
from database import connect_to_db, close_db_connection, get_db_pool
from gemini_service import generate_sql_from_gemini

# --- Constants ---
UPLOAD_DIR = "uploads"
SCHEMA_FILE_PATH = os.path.join(UPLOAD_DIR, "schema.sql")


# --- Pydantic Models for Request and Response ---
class SQLRequest(BaseModel):
    """
    Defines the structure for the SQL generation request.
    It only requires the business logic, as the schema is pre-uploaded.
    """
    business_logic: str

class ExecuteSQLRequest(BaseModel):
    """
    Defines the structure for the SQL execution request.
    It requires the SQL query to be executed.
    """
    sql_query: str

class SQLResponse(BaseModel):
    """
    Defines the structure of the outgoing response for SQL generation.
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
    description="An API that uses Gemini to translate business logic into a SQL query, and then executes it.",
    version="1.4.0", # Version bump for refactoring
)

# --- CORS Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Application Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """
    On startup, create the uploads directory and initialize the database connection pool.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown_event():
    """
    On shutdown, close the database connection pool.
    """
    await close_db_connection()


# --- API Endpoints ---

@app.post("/upload-schema/", response_model=UploadResponse)
async def upload_ddl_schema(file: UploadFile = File(..., description="The dump.sql file containing the DDL schema.")):
    """
    Uploads a `dump.sql` file. The schema is stored for subsequent calls.
    """
    try:
        contents = await file.read()
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
    Generates a SQL query based on the previously uploaded schema.
    """
    if not os.path.exists(SCHEMA_FILE_PATH):
        raise HTTPException(status_code=400, detail="No schema file found. Please use the /upload-schema/ endpoint first.")
    with open(SCHEMA_FILE_PATH, "r") as f:
        schema_ddl = f.read()
    if not request.business_logic:
        raise HTTPException(status_code=400, detail="Business logic must not be empty.")
    
    # Call the segregated service function
    generated_query = await generate_sql_from_gemini(schema_ddl=schema_ddl, business_logic=request.business_logic)
    return SQLResponse(sql_query=generated_query)


@app.post("/execute-sql/", response_model=List[Dict[str, Any]])
async def execute_sql_endpoint(request: ExecuteSQLRequest):
    """
    Executes a given SQL query against the database and returns the result.
    """
    pool = get_db_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Database connection is not available.")
    
    async with pool.acquire() as connection:
        try:
            # Execute the query
            records = await connection.fetch(request.sql_query)
            # Convert the list of Record objects to a list of dictionaries
            result = [dict(record) for record in records]
            return result
        except asyncpg.PostgresError as e:
            # Catch specific SQL-related errors
            raise HTTPException(status_code=400, detail=f"SQL Error: {e}")
        except Exception as e:
            # Catch other potential errors
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during execution: {e}")

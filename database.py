# database.py

import os
import asyncpg

# --- Database Configuration ---
# Use the standard environment variables expected by the official PostgreSQL image
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db") # Default to the service name 'db' from docker-compose
DB_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

# This global variable will hold the connection pool.
pool = None

async def connect_to_db():
    """
    Initializes the database connection pool.
    """
    global pool
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        print("Database connection pool created successfully.")
    except Exception as e:
        print(f"FATAL: Could not connect to database: {e}")
        pool = None

async def close_db_connection():
    """
    Closes the database connection pool.
    """
    global pool
    if pool:
        await pool.close()
        print("Database connection pool closed.")

def get_db_pool():
    """
    Returns the current database connection pool.
    """
    return pool

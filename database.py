# database.py

import os
import asyncpg

# --- Database Configuration ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

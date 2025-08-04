# AI-Powered SQL Query Generator

This project is a backend service built with Python and FastAPI that leverages the power of Google's Gemini large language model. It translates natural language business logic into executable SQL queries based on a user-provided database schema, and then runs those queries to fetch data.

This guide provides two methods for running the application:

1.  **With Docker (Recommended)**: For a consistent, portable, and easy-to-manage environment.
2.  **Without Docker**: For running the application directly on your local machine.

---

## Features

-   **Upload Schema**: An endpoint to upload a `dump.sql` file, which defines the database's DDL schema.
-   **AI-Powered Translation**: Uses the Gemini Pro model to accurately convert natural language requests into PostgreSQL queries.
-   **Direct Database Execution**: Connects to a PostgreSQL database to execute the generated SQL query.
-   **Combined Workflow**: A single endpoint to both generate the SQL and return the fetched data, providing a seamless user experience.
-   **CORS Ready**: Pre-configured with CORS middleware to allow requests from a frontend application (e.g., running on `http://localhost:3000`).

---

## Tech Stack

-   **Backend**: Python 3.9+
-   **Framework**: FastAPI
-   **Containerization**: Docker, Docker Compose
-   **Database**: PostgreSQL
-   **AI Model**: Google Gemini 1.5 Pro
-   **Async Support**: `uvicorn`, `httpx`, `asyncpg`

---

## Prerequisites

-   A **Google Gemini API Key**.
-   **For Docker Setup**: Docker and Docker Compose installed.
-   **For Local Setup**: Python 3.9+ and a local PostgreSQL 14 instance.

---

## Setup and Installation (With Docker)

This is the recommended method for development and deployment.

### 1. Configure Environment Variables

Create a file named `.env` in the root of your project directory. This file will be used by Docker Compose to configure both the API and the database services.

Populate the `.env` file with the following content. **Note that `DB_HOST` must be `db`**, which is the service name of the database container in the `docker-compose.yml` file.

```env
# .env file for Docker setup

# Your secret API key from Google AI Studio
GEMINI_API_KEY="your_actual_gemini_api_key"

# PostgreSQL credentials for the Docker container
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="your_database_password"
POSTGRES_DB="db_name"
DB_HOST="db"
DB_PORT="5432"

```
### 2. Build and Run the Containers
Run the following command from the root of your project directory:

```bash
docker-compose up --build
```

This command will:

- Build the Docker image for your FastAPI application.

- Pull the official PostgreSQL 14 image.

- Start both services and connect them on a dedicated network.

- The application will be available at http://localhost:8000.


### 3. Load Initial Data (If Needed)
The Docker database starts empty. If you need to load your schema and data from a dump.sql file, wait for the containers to be running, and then execute this command in a new terminal window:

```bash
docker-compose exec db psql -U postgres -d db_name -f /app/dump.sql
```

(This assumes your dump.sql is in the project's root directory).

## Setup and Installation (Without Docker)
Follow these steps to run the application directly on your machine.

### 1. Create and Activate a Virtual Environment

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (on macOS/Linux)
source venv/bin/activate

# Or on Windows
# .\venv\Scripts\activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Set the environment variables directly in your terminal. Note that `DB_HOST` must be `localhost` for this setup.

```bash
# On macOS/Linux
export GEMINI_API_KEY='your_actual_gemini_api_key'
export POSTGRES_USER='postgres'
export POSTGRES_PASSWORD='your_database_password'
export POSTGRES_DB='db_name'
export DB_HOST='localhost'
export DB_PORT='5432'
```

### 4. Run the Application

```bash
uvicorn main:app --reload
```

The application will now be running at `http://localhost:8000`.

API Endpoints
You can interact with the API using tools like curl or Postman, or by visiting the interactive documentation at `http://localhost:8000/docs`.

### 1. Upload Schema
Upload your database schema file first.

- Endpoint: POST /upload-schema/

- Example curl command:
```bash
curl -X POST http://localhost:8000/upload-schema/ -H 'Content-Type: multipart/form-data' -F 'file=@/path/to/your/dump.sql'
```

### 2. Generate and Execute SQL
Send your business logic to this endpoint to get back the generated SQL and the data from the database.

- Endpoint: `POST /generate-and-execute/`

- Request Body `(raw JSON)`:

```JSON
{
  "business_logic": "Find the names of all employees in the Engineering department"
}
```

- Success Response:

```JSON
{
  "sql_query": "SELECT name FROM employees WHERE department = 'Engineering'",
  "data": [
    {
      "name": "Alice"
    },
    {
      "name": "Bob"
    }
  ]
}
```
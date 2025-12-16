# Action Item Extractor

A FastAPI-based web application that extracts actionable items from free-form text notes using both pattern-based heuristics and LLM-powered semantic understanding. The application allows users to create notes, extract action items, and manage their tasks through a simple web interface.

## Overview

The Action Item Extractor is designed to help users convert unstructured notes into organized action items. It provides two extraction methods:

- **Pattern-based extraction**: Uses predefined heuristics to identify action items from bullet lists, checkboxes, and keyword-prefixed lines
- **LLM-powered extraction**: Leverages Ollama and large language models to semantically understand and extract future action items from natural language text

The application features a RESTful API backend built with FastAPI and a minimal HTML/CSS/JavaScript frontend. Data is persisted in a SQLite database.

## Features

- Create and manage notes
- Extract action items from text using LLM-powered semantic analysis
- List all notes and action items
- Mark action items as done/undone
- Associate action items with specific notes
- Simple, responsive web interface

## Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- Ollama (for LLM-powered extraction)
  - Install from: https://ollama.com
  - Pull a model: `ollama pull llama3.1:8b` (or your preferred model)

## Setup

### 1. Install Dependencies

From the project root directory:

```bash
poetry install --no-interaction
```

This will install all required dependencies including:
- FastAPI and Uvicorn (web framework and ASGI server)
- Ollama (LLM integration)
- Pydantic (data validation)
- Python-dotenv (environment variable management)
- Pytest and HTTPX (testing)

### 2. Configure Environment Variables (Optional)

Create a `.env` file in the project root if you want to customize the Ollama model:

```bash
OLLAMA_MODEL=llama3.1:8b
```

If not specified, the application defaults to `llama3.1:8b`.

### 3. Initialize the Database

The database is automatically initialized when the application starts. The SQLite database file will be created at `week2/data/app.db`.

## Running the Application

### Start the Development Server

From the project root:

```bash
poetry run uvicorn week2.app.main:app --reload
```

The `--reload` flag enables auto-reload on code changes for development.

### Access the Application

- **Web Interface**: Open your browser and navigate to http://127.0.0.1:8000/
- **API Documentation**: http://127.0.0.1:8000/docs (Swagger UI)
- **Alternative API Docs**: http://127.0.0.1:8000/redoc (ReDoc)

## API Endpoints

### Notes Endpoints

#### `GET /notes`
Retrieve all notes.

**Response:**
```json
[
  {
    "id": 1,
    "content": "Meeting notes...",
    "created_at": "2025-01-15 10:30:00"
  }
]
```

#### `POST /notes`
Create a new note.

**Request Body:**
```json
{
  "content": "Your note content here"
}
```

**Response:**
```json
{
  "id": 1,
  "content": "Your note content here",
  "created_at": "2025-01-15 10:30:00"
}
```

#### `GET /notes/{note_id}`
Retrieve a specific note by ID.

**Response:**
```json
{
  "id": 1,
  "content": "Your note content here",
  "created_at": "2025-01-15 10:30:00"
}
```

**Error Responses:**
- `404`: Note not found

### Action Items Endpoints

#### `POST /action-items/extract`
Extract action items from text using LLM-powered extraction.

**Request Body:**
```json
{
  "text": "Meeting notes:\n- [ ] Set up database\n- Implement API endpoint",
  "save_note": true
}
```

**Response:**
```json
{
  "note_id": 1,
  "items": [
    {
      "id": 1,
      "text": "Set up database"
    },
    {
      "id": 2,
      "text": "Implement API endpoint"
    }
  ]
}
```

**Parameters:**
- `text` (required): The text to extract action items from
- `save_note` (optional): If `true`, saves the input text as a note and associates action items with it

#### `GET /action-items`
List all action items, optionally filtered by note ID.

**Query Parameters:**
- `note_id` (optional): Filter action items by note ID

**Response:**
```json
[
  {
    "id": 1,
    "note_id": 1,
    "text": "Set up database",
    "done": false,
    "created_at": "2025-01-15 10:30:00"
  }
]
```

#### `POST /action-items/{action_item_id}/done`
Mark an action item as done or undone.

**Request Body:**
```json
{
  "done": true
}
```

**Response:**
```json
{
  "id": 1,
  "done": true
}
```

## Database Schema

The application uses SQLite with two main tables:

### `notes`
- `id` (INTEGER PRIMARY KEY): Auto-incrementing note ID
- `content` (TEXT NOT NULL): Note content
- `created_at` (TEXT): Timestamp of creation (default: current datetime)

### `action_items`
- `id` (INTEGER PRIMARY KEY): Auto-incrementing action item ID
- `note_id` (INTEGER): Foreign key to `notes.id` (nullable)
- `text` (TEXT NOT NULL): Action item description
- `done` (INTEGER DEFAULT 0): Completion status (0 = not done, 1 = done)
- `created_at` (TEXT): Timestamp of creation (default: current datetime)

## Running Tests

The test suite uses pytest and includes unit tests for the extraction functions.

### Run All Tests

From the project root:

```bash
poetry run pytest week2/tests/ -v
```

### Run Specific Test File

```bash
poetry run pytest week2/tests/test_extract.py -v
```

### Run with Coverage

```bash
poetry run pytest week2/tests/ --cov=week2/app --cov-report=html
```

### Test Structure

The test suite (`week2/tests/test_extract.py`) includes:

- **Pattern-based extraction tests**: Tests for `extract_action_items()` function
- **LLM-powered extraction tests**: Comprehensive tests for `extract_action_items_llm()` covering:
  - Empty input handling
  - Bullet lists and checkboxes
  - Keyword-prefixed lines
  - Future vs. past tense discrimination
  - Implicit task extraction
  - Mixed format text
  - Text with no action items
  - Commitments and promises

## Project Structure

```
week2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── db.py                # Database operations and schema
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── notes.py         # Notes API endpoints
│   │   └── action_items.py  # Action items API endpoints
│   └── services/
│       └── extract.py        # Extraction logic (pattern-based and LLM)
├── frontend/
│   └── index.html           # Web interface
├── tests/
│   ├── __init__.py
│   └── test_extract.py      # Unit tests for extraction functions
├── data/                    # SQLite database directory (auto-created)
│   └── app.db
├── assignment.md            # Assignment instructions
├── writeup.md              # Student writeup template
└── README.md               # This file
```

## Development

### Code Style

The project uses:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- Type hints throughout the codebase

### Adding New Features

1. Add new endpoints in the appropriate router file (`routers/notes.py` or `routers/action_items.py`)
2. Add database operations in `db.py` if needed
3. Update the frontend in `frontend/index.html` for UI changes
4. Add tests in `tests/` directory
5. Update this README if adding new endpoints or features

## Troubleshooting

### Ollama Connection Issues

If LLM extraction fails:
1. Ensure Ollama is running: `ollama serve`
2. Verify the model is pulled: `ollama list`
3. Check the `OLLAMA_MODEL` environment variable matches an available model
4. Review application logs for detailed error messages

### Database Issues

If you encounter database errors:
1. Check that the `week2/data/` directory exists and is writable
2. Delete `week2/data/app.db` to reset the database (data will be lost)
3. Restart the application to reinitialize the database

### Port Already in Use

If port 8000 is already in use:
```bash
poetry run uvicorn week2.app.main:app --reload --port 8001
```

## License

This project is part of CS146S: The Modern Software Developer course assignments.

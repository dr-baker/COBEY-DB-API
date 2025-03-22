# Workout API Backend

A FastAPI-based backend service for managing workout sessions with PostgreSQL database and SSH tunnel security.

## Features

- FastAPI REST API
- PostgreSQL database with SQLModel ORM
- Automatic schema documentation
- SSH tunnel support for secure database connections
- Migration management with Alembic

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and update with your configuration
6. Run the server: `uvicorn main:app --reload`

## Environment Variables

See `.env.example` for all required environment variables.

## Database Schema Management

We use SQLModel for database models, which combines SQLAlchemy and Pydantic into a single model definition. This approach offers several advantages:

- Single source of truth for database schema and API models
- Automatic validation of input/output data
- Type safety throughout the application
- Reduced code duplication

### Adding or Modifying Tables

When you need to add or modify tables:

1. Edit the models in `app/models.py`
2. Generate a migration: `python -m app.cli.schema migrate -m "Description of changes"`
3. Apply the migration: `python -m app.cli.schema apply`
4. Generate updated documentation: `python -m app.cli.schema docs`

### CLI Tool

The project includes a command-line tool for schema management:

```
python -m app.cli.schema [command]
```

Available commands:

- `init`: Initialize the migration system (run once)
- `migrate`: Generate a new migration
- `apply`: Apply pending migrations
- `detect`: Detect schema changes without creating a migration
- `docs`: Generate schema documentation

### Schema Documentation

Auto-generated schema documentation is available in the `docs/schema` directory.

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Migrations

Database migrations are managed with Alembic and can be generated automatically from model changes.

## Examples

See the `examples` directory for usage examples of the API.

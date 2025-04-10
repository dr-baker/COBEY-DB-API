# Backend API Service

This repository contains the backend service for our cloud platform. It provides a RESTful API for managing user data, recordings, algorithms, and event logs.

## For API Users

The API documentation is available at:
- `docs/api.html`

## Backend Info

### Architecture Overview

The service is built using FastAPI and follows a clean, modular architecture:

```
backendapi/
├── src/
│   ├── api/                 # API layer
│   │   ├── dependencies.py  # Shared dependencies and utilities
│   │   └── routes/         # API route definitions
│   ├── core/               # Core application logic
│   │   ├── config.py       # Configuration management
│   │   └── logging.py      # Logging configuration
│   ├── db/                 # Database layer
│   │   ├── connection.py   # Database connection management + SSH
│   │   ├── introspection.py # Database schema introspection 
│   │   ├── migrations/     # Database migration system
│   │   │   ├── manager.py  # Migration manager
│   │   │   └── versions/   # Migration SQL files
│   │   └── queries/        # Query builders and executors
│   └── models/             
│       ├── users.py        
│       ├── recordings.py   
│       ├── sessions.py     
│       ├── algos.py        
│       └── event_log.py    
├── scripts/               # Utility scripts
├── examples/              # Example usage
└── tests/                 # Test suite (TODO)
```

### Key Components

1. **API Layer (`src/api/`)**
   - Handles HTTP request/response cycle
   - Route definitions and request validation
   - Authentication and authorization
   - Error handling and response formatting

2. **Core Layer (`src/core/`)**
   - Application configuration
   - Logging setup
   - Common utilities
   - Environment-specific settings

3. **Database Layer (`src/db/`)**
   - Database connection management
   - Query building and execution
   - Schema introspection
   - Custom migration system
   - Transaction management

4. **Models Layer (`src/models/`)**
   - Pydantic models for request/response validation
   - Database model definitions
   - Data transformation logic

### Quickstart

1. **Clone the repository**:
```bash
git clone <internal-repo-url>
cd backendapi
```

2. **Set up the development environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your development configuration
```

4. **Run database migrations**:
```bash
python -m scripts.migrate
```

5. **Start the development server**:
```bash
uvicorn src.main:app --reload
```

### Development Workflow

1. **Adding New Features**
   - Create a new branch from `main`
   - Implement your changes following the existing architecture
   - Add tests for new functionality
   - Update documentation as needed
   - Submit a pull request

2. **Database Changes**
   - Create a new migration file in `src/db/migrations/versions/`
     - Name format: `###_description.sql` (e.g., `001_create_users.sql`)
     - Write SQL for schema changes
   - Apply migrations:
     ```bash
     python -m scripts.migrate
     ```
   - Reset database and apply all migrations:
     ```bash
     python -m scripts.migrate --reset
     ```
   - Generate updated models:
     ```bash
     python -m scripts.generate_models
     ```

3. **Testing**
   - Run the test suite:
     ```bash
     pytest
     ```
   - Run specific test files:
     ```bash
     pytest tests/path/to/test_file.py
     ```

### Getting Started with the Codebase

The `examples/basic_usage.py` script provides a comprehensive example of how to interact with the API programmatically. This is the recommended starting point for understanding the codebase.

### Common Development Tasks

1. **Adding a New Table**
   - Create a migration file with the CREATE TABLE statement in `src/db/migrations/versions/`
   - Apply migrations with `python -m scripts.migrate`
   - Generate models using `python -m scripts.generate_models`
   - Update `src/api/dependencies.py` with new model mappings
   - Add routes in `src/api/routes/crud_routes.py`
   - Register the new router in `src/main.py`

2. **Modifying Existing Endpoints**
   - Locate the relevant route in `src/api/routes/`
   - Update the route handler and validation logic
   - Update tests to reflect changes
   - Update documentation if needed

3. **Adding New Dependencies**
   - Add the package to `requirements.txt`
   - Update the virtual environment:
     ```bash
     pip install -r requirements.txt
     ```

### Utility Scripts

The `scripts/` directory contains several utility scripts to assist with common tasks:

1. **migrate.py**: Handles database migrations, including applying and rolling back changes.
   ```bash
   # Apply pending migrations
   python -m scripts.migrate
   
   # Clear migration history and reapply all migrations
   python -m scripts.migrate --clear
   
   # Reset entire database and reapply all migrations
   python -m scripts.migrate --reset
   ```

2. **generate_models.py**: Introspects the database schema and generates Pydantic models in the `src/models` directory.

### Troubleshooting

Common issues and their solutions are documented in our internal wiki. For issues not covered there, please contact the backend team lead.

# Backend API

A FastAPI-based backend service that provides a RESTful API for managing user data, recordings, algorithms, and event logs.

## Features

- Explicit Pydantic models for request/response validation 
- CRUD operations for all database tables
- Pagination and filtering support
- Comprehensive API documentation
- Logging and error handling
- Well-structured code with clean separation of concerns

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backendapi
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

## Usage

### Starting the Server

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Documentation

#### Users API

The Users API provides endpoints for managing user data.

##### Endpoints

1. **Get User**
   ```http
   GET /users/{user_id}
   ```
   Retrieves a specific user by their unique identifier.
   - **Parameters**:
     - `user_id` (path): Unique identifier of the user
   - **Response**: User object with all fields

2. **List Users**
   ```http
   GET /users
   ```
   Retrieves a paginated list of users.
   - **Query Parameters**:
     - `page` (int, default=1): Page number
     - `size` (int, default=10, max=100): Items per page
   - **Response**: List of user objects

3. **Create User**
   ```http
   POST /users
   ```
   Creates a new user.
   - **Request Body**:
     ```json
     {
       "user_id": "string",
       "firebase_data": {
         "email": "string",
         "display_name": "string"
       },
       "body_data": {
         "height": "number",
         "weight": "number"
       }
     }
     ```
   - **Response**: Created user object

4. **Update User**
   ```http
   PUT /users/{user_id}
   ```
   Updates an existing user's information.
   - **Parameters**:
     - `user_id` (path): Unique identifier of the user
   - **Request Body**: Same as Create User
   - **Response**: Updated user object

5. **Delete User**
   ```http
   DELETE /users/{user_id}
   ```
   Deletes a user by their unique identifier.
   - **Parameters**:
     - `user_id` (path): Unique identifier of the user
   - **Response**: 204 No Content

#### Recordings API

The Recordings API provides endpoints for managing user recordings.

##### Endpoints

1. **Get Recording**
   ```http
   GET /recordings/{recording_id}
   ```
   Retrieves a specific recording by its unique identifier.
   - **Parameters**:
     - `recording_id` (path): Unique identifier of the recording
   - **Response**: Recording object with all fields

2. **List Recordings**
   ```http
   GET /recordings
   ```
   Retrieves a paginated list of recordings with optional filtering.
   - **Query Parameters**:
     - `user_id` (string, optional): Filter by user ID
     - `recording_type` (string, optional): Filter by recording type
     - `page` (int, default=1): Page number
     - `size` (int, default=10, max=100): Items per page
   - **Response**: List of recording objects

3. **Create Recording**
   ```http
   POST /recordings
   ```
   Creates a new recording.
   - **Request Body**:
     ```json
     {
       "recording_id": "string",
       "recording_link": "string",
       "recording_type": "string",
       "user_id": "string",
       "created_session_id": "string"
     }
     ```
   - **Response**: Created recording object

4. **Update Recording**
   ```http
   PUT /recordings/{recording_id}
   ```
   Updates an existing recording's information.
   - **Parameters**:
     - `recording_id` (path): Unique identifier of the recording
   - **Request Body**: Same as Create Recording
   - **Response**: Updated recording object

5. **Delete Recording**
   ```http
   DELETE /recordings/{recording_id}
   ```
   Deletes a recording by its unique identifier.
   - **Parameters**:
     - `recording_id` (path): Unique identifier of the recording
   - **Response**: 204 No Content

#### Algorithms API

The Algorithms API provides endpoints for managing algorithm metadata.

##### Endpoints

1. **Get Algorithm**
   ```http
   GET /algos/{algo_id}
   ```
   Retrieves a specific algorithm by its unique identifier.
   - **Parameters**:
     - `algo_id` (path): Unique identifier of the algorithm
   - **Response**: Algorithm object with all fields

2. **List Algorithms**
   ```http
   GET /algos
   ```
   Retrieves a paginated list of algorithms with optional filtering.
   - **Query Parameters**:
     - `recording_type` (string, optional): Filter by recording type
     - `version` (string, optional): Filter by version
     - `page` (int, default=1): Page number
     - `size` (int, default=10, max=100): Items per page
   - **Response**: List of algorithm objects

3. **Create Algorithm**
   ```http
   POST /algos
   ```
   Creates a new algorithm.
   - **Request Body**:
     ```json
     {
       "algo_id": "string",
       "recording_type": "string",
       "location": "string",
       "version": "string"
     }
     ```
   - **Response**: Created algorithm object

4. **Update Algorithm**
   ```http
   PUT /algos/{algo_id}
   ```
   Updates an existing algorithm's information.
   - **Parameters**:
     - `algo_id` (path): Unique identifier of the algorithm
   - **Request Body**: Same as Create Algorithm
   - **Response**: Updated algorithm object

5. **Delete Algorithm**
   ```http
   DELETE /algos/{algo_id}
   ```
   Deletes an algorithm by its unique identifier.
   - **Parameters**:
     - `algo_id` (path): Unique identifier of the algorithm
   - **Response**: 204 No Content

#### Event Log API

The Event Log API provides endpoints for managing event logs.

##### Endpoints

1. **Get Event**
   ```http
   GET /events/{event_id}
   ```
   Retrieves a specific event log entry by its unique identifier.
   - **Parameters**:
     - `event_id` (path): Unique identifier of the event
   - **Response**: Event log object with all fields

2. **List Events**
   ```http
   GET /events
   ```
   Retrieves a paginated list of event logs with optional filtering.
   - **Query Parameters**:
     - `user_id` (string, optional): Filter by user ID
     - `session_id` (string, optional): Filter by session ID
     - `event_type` (string, optional): Filter by event type
     - `event_source` (string, optional): Filter by event source
     - `ts_gte` (datetime, optional): Filter by timestamp greater than or equal to
     - `ts_lte` (datetime, optional): Filter by timestamp less than or equal to
     - `page` (int, default=1): Page number
     - `size` (int, default=10, max=100): Items per page
   - **Response**: List of event log objects

3. **Create Event**
   ```http
   POST /events
   ```
   Creates a new event log entry.
   - **Request Body**:
     ```json
     {
       "user_id": "string",
       "session_id": "string",
       "event_type": "string",
       "event_data": {},
       "event_source": "string",
       "log_level": "string",
       "ts": "datetime"
     }
     ```
   - **Response**: Created event log object

4. **Update Event**
   ```http
   PUT /events/{event_id}
   ```
   Updates an existing event log entry's information.
   - **Parameters**:
     - `event_id` (path): Unique identifier of the event
   - **Request Body**: Same as Create Event
   - **Response**: Updated event log object

5. **Delete Event**
   ```http
   DELETE /events/{event_id}
   ```
   Deletes an event log entry by its unique identifier.
   - **Parameters**:
     - `event_id` (path): Unique identifier of the event
   - **Response**: 204 No Content

### Error Responses

All endpoints may return the following error responses:

1. **400 Bad Request**
   ```json
   {
     "detail": "Error message describing the validation error"
   }
   ```

2. **404 Not Found**
   ```json
   {
     "detail": "Resource not found"
   }
   ```

3. **500 Internal Server Error**
   ```json
   {
     "detail": "Internal server error message"
   }
   ```

## Development

### Project Structure

```
backendapi/
├── src/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── health.py
│   │       └── crud_routes.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── introspection.py
│   │   └── queries/
│   │       ├── builder.py
│   │       └── executor.py
│   └── models/
│       ├── users.py
│       ├── recordings.py
│       ├── sessions.py
│       ├── algos.py
│       └── event_log.py
├── scripts/
│   ├── migrate.py
│   ├── reset_and_migrate.py
│   └── generate_models.py
├── examples/
│   └── basic_usage.py
├── tests/
├── .env.example
├── alembic.ini
├── main.py
└── requirements.txt
```

### Model Generation

The project uses explicit Pydantic models to represent database tables. If your database schema changes, you can regenerate the models using:

```bash
python -m scripts.generate_models
```

This will introspect your database schema and create appropriate Pydantic models in the `src/models` directory.

### Running Tests

```bash
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migrations:
```bash
alembic downgrade -1
```

### Working with the CRUD Router

The API uses a standardized CRUD router factory that generates consistent endpoints for each table. To add a new table to the API:

1. Generate models for your table with `python -m scripts.generate_models`
2. Update the MODEL_MAP in `src/api/dependencies.py` to include your new model
3. Add a router in `src/api/routes/crud_routes.py`:

```python
your_table_router = create_crud_router(
    table_name="your_table_name",
    prefix="/your-endpoint",
    tags=["your-tag"],
    auto_timestamps=True
)
```

4. Register the new router in `src/main.py`:

```python
app.include_router(crud_routes.your_table_router)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
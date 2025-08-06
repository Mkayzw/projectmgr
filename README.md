# Project Manager API 
- User authentication and authorization
- Workspaces and projects management
- Task management with deadlines, priorities, and assignments
- User collaboration
- Notifications system (email or mock)
- File attachments
- Background processing and asynchronous operations

## Tech Stack

| Purpose | Tool |
|---------|------|
| Web Framework | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth or JWT with python-jose |
| Background Jobs | FastAPI BackgroundTasks (or Celery + Redis) |
| File Storage | Supabase Storage or Amazon S3 |
| Caching (optional) | Redis |
| Tests | Pytest |
| Linting | ruff |
| Environment Management | python-dotenv |
| Docs | FastAPI's built-in Swagger / ReDoc |
| Deployment | Railway or Fly.io |
| CI/CD (optional) | GitHub Actions |

## Project Structure

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL (or Supabase account)
- Redis (optional, for caching and Celery)

### Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your environment variables
6. Run migrations: `alembic upgrade head`
7. Start the server: `uvicorn app.main:app --reload`

### Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://user:password@localhost:5432/tactix
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase (if using)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key


# Email (if implementing email notifications)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Creating Migrations

```bash
alembic revision --autogenerate -m "Description of changes"
```


## License

MIT
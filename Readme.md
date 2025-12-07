# Movies App Backend

### FastAPI + SQLAlchemy + Alembic + SQLite/PostgreSQL

This backend powers the **Movies App**, providing a scalable REST API for managing films, genres, ratings, and future user accounts.  
It uses **FastAPI** for blazing fast performance and **SQLAlchemy ORM** for database persistence and migrations via **Alembic**.

- Uses **SQLite during development**
- Easily switches to **PostgreSQL in production**

---

## Tech Stack

| Tool           | Purpose                               |
| -------------- | ------------------------------------- |
| **FastAPI**    | Modern API framework                  |
| **SQLAlchemy** | ORM + Models                          |
| **Alembic**    | Database migration engine             |
| **SQLite**     | Default development DB                |
| **PostgreSQL** | Production-ready DB (planned upgrade) |

---

## Project Setup

### Requirements

- Python **3.10 or higher**
- **pipenv** (recommended for environment management)

---

### Setup Instructions

#### 1) Install required dependencies

``bash
pipenv install sqlalchemy alembic "fastapi[standard]"

2. ### Activate the virtual environment
   bash
   Copy code
   pipenv shell
3. ### Initialize Alembic migrations (run only once)
   bash
   Copy code
   alembic init migrations
4. ### Configure Alembic to use SQLite
   Open alembic.ini and update:

ini

# Copy code

sqlalchemy.url = sqlite:///movies.db
For production, change to PostgreSQL:

ini

# Copy code

postgresql+psycopg2://user:password@localhost:5432/moviesdb 5) ### Scaffold the core files
bash

# Copy code

touch models.py app.py 6) ### Register SQLAlchemy metadata with Alembic
Update migrations/env.py:

python

# Copy code

from models import Base
target_metadata = Base.metadata

## Running the Application

Start the development server with auto-reloading:

bash

# Copy code

fastapi dev app.py

## API Documentation

Documentation URL
Swagger UI http://127.0.0.1:8000/docs
ReDoc http://127.0.0.1:8000/redoc

## Database Migrations (Alembic)

Generate a migration
bash

# Copy code

alembic revision --autogenerate -m "initial migration"
Apply pending migrations
bash

# Copy code

alembic upgrade head

### Future Enhancements

JWT Authentication & Real Users

Movie Ratings & User Reviews

Genre & Actor Relationship Support

Pagination & Query Filters

Data Seeder Script for Demo Environment

Full PostgreSQL Deployment

License
This project is open source under the MIT License .

```

```

FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (for psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy app
COPY . .

# Collect static (if using Django)
RUN uv run python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run with gunicorn (2 workers, 2 threads)
CMD ["uv", "run", "gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "60", "--keep-alive", "5"]
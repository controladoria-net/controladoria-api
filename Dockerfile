FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

WORKDIR /app
RUN uv sync --frozen --no-cache

EXPOSE 8000

CMD ["bash", "-c", "uv run alembic upgrade head && uv run main.py"]

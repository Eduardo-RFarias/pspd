FROM ghcr.io/astral-sh/uv:bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN uv sync

COPY main.py /app/

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"] 
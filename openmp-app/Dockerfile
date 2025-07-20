FROM ghcr.io/astral-sh/uv:bookworm-slim

RUN apt-get update && apt-get install -y gcc libomp-dev make

WORKDIR /app

COPY jogodavida_openmp.c Makefile /app/

RUN make jogodavida_openmp

COPY pyproject.toml uv.lock /app/

RUN uv sync

COPY main.py /app/

ENV OMP_NUM_THREADS=4
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]

FROM python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

    WORKDIR /app

    RUN pip install numpy pandas requests fastapi sqlalchemy dotenv pydantic setuptools uvicorn

    RUN pip freeze > requirements.txt

    CMD ["cat", "requirements.txt"]
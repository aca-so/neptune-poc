FROM python:3.10-slim

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry export -o requirements.txt

FROM python:3.10-slim

COPY --from=0 requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]

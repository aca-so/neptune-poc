FROM python:3.10-slim

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry export -o requirements.txt

FROM python:3.10-slim

WORKDIR /code

COPY --from=0 requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

ENV PYTHONPATH=/code

CMD ["python", "app/main.py"]

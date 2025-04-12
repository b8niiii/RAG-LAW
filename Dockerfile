FROM python:3.12.5
WORKDIR ~
COPY . .

RUN pip install --upgrade pip
RUN pip install poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-root

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install fastapi uvicorn

EXPOSE 8080

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
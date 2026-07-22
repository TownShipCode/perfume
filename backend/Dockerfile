FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir uvicorn

EXPOSE 8080

CMD ["bash", "start.sh"]

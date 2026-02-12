FROM python:latest

WORKDIR /usr/agent

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/

CMD ["python", "src/main.py"]
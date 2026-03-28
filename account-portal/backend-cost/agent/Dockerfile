FROM python:3.9-slim

RUN pip install psutil boto3 pynvml

COPY agent.py /app/agent.py
WORKDIR /app

CMD ["python", "agent.py"]

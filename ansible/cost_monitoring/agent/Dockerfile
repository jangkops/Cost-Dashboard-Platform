FROM python:3.9-slim
RUN pip install boto3 psutil pynvml
RUN useradd -m -u 1000 agent
USER agent
WORKDIR /app
COPY main.py .
CMD ["python", "main.py"]

FROM python:3.12-slim
WORKDIR /app
COPY services/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services /app/services
ENV PYTHONPATH=/app
CMD ["python", "services/policy-engine/main.py"]

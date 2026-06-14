FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*
RUN wget https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip && unzip terraform_1.9.8_linux_amd64.zip && mv terraform /usr/local/bin/terraform && rm terraform_1.9.8_linux_amd64.zip
COPY services/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services /app/services
COPY terraform /app/terraform
ENV PYTHONPATH=/app
CMD ["python", "services/remediation-worker/main.py"]

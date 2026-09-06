FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home tutor \
    && mkdir /app/data \
    && chown tutor:tutor /app/data
COPY main.py .
COPY tutor ./tutor
USER tutor
CMD ["python", "main.py"]

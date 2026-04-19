FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update     && apt-get install -y --no-install-recommends gcc libjpeg62-turbo-dev zlib1g-dev fonts-dejavu-core     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/generated_docs /app/data/media /app/fonts

CMD ["python", "bot.py"]

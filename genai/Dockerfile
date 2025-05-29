FROM python:3.12-slim

# Install OS packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose and run
ENV GENAI_PORT=3003
EXPOSE 3003
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${GENAI_PORT}"]

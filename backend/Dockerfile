FROM python:3.11-slim


# SEt up working directory
WORKDIR /app

# system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create directory for logs
RUN mkdir -p logs

# Expose port
EXPOSE 5000

ENV PYTHONPATH=/app
ENV FLASK_APP=src/apis/gid.py
ENV FLASK_ENV=production

# Command to run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
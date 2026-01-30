FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/backend/ .

# Expose port (Railway uses PORT env var)
EXPOSE 8000

# Run the application
# Railway may set PORT env var, default to 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

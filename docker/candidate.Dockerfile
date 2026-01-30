FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY src/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/frontend/ .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit - Candidate Portal
CMD ["streamlit", "run", "app_candidate.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]

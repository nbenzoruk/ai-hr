FROM python:3.11-slim

WORKDIR /app

# Build argument for app selection
ARG APP_FILE=app_candidate.py
ENV APP_FILE=${APP_FILE}

# Install dependencies
COPY src/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/frontend/ .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit with the specified app file
CMD streamlit run ${APP_FILE} --server.address 0.0.0.0 --server.port 8501

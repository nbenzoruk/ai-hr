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

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Starting Streamlit app: $APP_FILE on port 8501..."\n\
exec streamlit run "$APP_FILE" --server.address 0.0.0.0 --server.port 8501 --server.headless true\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the application
CMD ["/app/entrypoint.sh"]

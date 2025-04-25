FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .
COPY templates ./templates

# Expose Flask port
EXPOSE 5000

# Run using Gunicorn for proper logging
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--log-level=info"]

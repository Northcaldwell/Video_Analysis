# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable stdout/stderr buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./

# Upgrade pip, install requirements, and ensure Flask-SQLAlchemy is present
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir Flask-SQLAlchemy

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 5001

# Set necessary environment variables for Flask
ENV FLASK_APP=src:create_app \
    FLASK_ENV=production

# Run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]

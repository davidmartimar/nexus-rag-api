# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
# Set the working directory in the container
WORKDIR /app

# Create directory for persistent data and ensure permissions for SQLite
RUN mkdir -p /app/data && chmod 777 /app/data
VOLUME ["/app/data"]

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000 (FastAPI default)
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--proxy-headers", "--forwarded-allow-ips", "*"]
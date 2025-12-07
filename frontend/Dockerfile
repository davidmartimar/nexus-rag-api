# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose port 8501 (Streamlit default)
EXPOSE 8501

# Command to run Streamlit
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]
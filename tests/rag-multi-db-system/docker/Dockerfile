FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/

# Copy the Docker initialization scripts
COPY docker/init-scripts/ ./docker/init-scripts/

# Expose the necessary ports (adjust as needed)
EXPOSE 8000

# Command to run the application
CMD ["python", "src/main.py"]
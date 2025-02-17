# Use a lightweight Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Create a script to export environment variables
RUN echo "export \$(grep -v '^#' .env | xargs)" > /app/export_env.sh
RUN chmod +x /app/export_env.sh


# Expose the correct port
EXPOSE 8080



# Start the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
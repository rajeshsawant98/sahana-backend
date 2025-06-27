# Use a lightweight Python image
FROM python:3.10-slim

# Update system packages to fix vulnerabilities and remove unnecessary build dependencies
RUN apt-get update && \
	apt-get dist-upgrade -y && \
	apt-get autoremove -y && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps

# Expose the correct port
EXPOSE 8080

# Start the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
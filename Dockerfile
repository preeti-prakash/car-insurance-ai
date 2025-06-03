# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the .env file into the container (ensure the file exists in your project)
COPY .env /app/.env

# Expose the port Gradio will use
EXPOSE 8080

# Run the Gradio app
CMD ["python", "main.py"]

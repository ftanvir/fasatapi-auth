FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevents python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
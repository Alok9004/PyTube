FROM python:3.12-slim
# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /django

# Copy dependency file and install packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files into the container
COPY . .

# Expose Django port
EXPOSE 8000

# Default command to run the app using Gunicorn
CMD ["gunicorn", "pytube.wsgi:application", "--bind", "0.0.0.0:8000"]
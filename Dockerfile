FROM python:3.11-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ./api/requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt
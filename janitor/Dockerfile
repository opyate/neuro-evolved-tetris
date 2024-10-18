FROM python:3.12.6-bullseye

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# dependencies
RUN pip install --upgrade pip
RUN pip install redis==5.0.8
# copy app
COPY . .

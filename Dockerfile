# base image
FROM python:3.11.3-slim-bullseye

# env variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# working directory
WORKDIR /application

# install requirements
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy files
COPY . .

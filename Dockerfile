# Pull base image
FROM python:3.9.16-slim-bullseye

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .


# RUN /home/ubuntu/"$APP_NAME"/venv/bin/pip install gunicorn

# # setup path
# ENV PATH="${PATH}:/home/ubuntu/$APP_NAME/$APP_NAME/scripts"

# USER ubuntu

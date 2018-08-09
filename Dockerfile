FROM python:3.6

WORKDIR /app

# Intall dependencies
COPY requirements.txt /app/

COPY . /app

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]


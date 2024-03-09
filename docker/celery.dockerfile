FROM common-bottle-dockerfile

# Intall dependencies
COPY requirements.txt /app

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app

ENTRYPOINT ["celery", "-A", "crm", "worker"]
CMD ["--loglevel=INFO"]
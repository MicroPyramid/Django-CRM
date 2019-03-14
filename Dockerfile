FROM python:3.6

WORKDIR /app

# Intall dependencies
COPY . /app/

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
  apt update && \
  apt install -y git ruby-dev nodejs && \
  gem install compass sass && \
  npm -g install less && \
  pip install -r requirements.txt && \
  pip install redis coveralls

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
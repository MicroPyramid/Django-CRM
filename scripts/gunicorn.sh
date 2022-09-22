#!/bin/bash

set -euxo pipefail

APP_NAME=bottlecrm-api

cd /home/ubuntu/$APP_NAME/$APP_NAME
. ../venv/bin/activate

# debug
whoami; pwd; ls -al; env

exec gunicorn crm.wsgi:application \
  --name $APP_NAME \
  --workers 2 \
  --threads 4 \
  --worker-class gthread \
  --worker-tmp-dir /dev/shm \
  --bind 0.0.0.0:8000 \
  --log-level debug

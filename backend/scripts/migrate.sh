#!/bin/bash

set -euxo pipefail

APP_NAME=bottlecrm-api

cd /home/ubuntu/$APP_NAME/$APP_NAME
. ../venv/bin/activate

# debug
whoami; pwd; ls -al; env

exec python manage.py migrate

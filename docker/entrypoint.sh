#!/bin/bash

# Execute startup scripts
./wait-for-postgres.sh "$DBHOST"
python3 manage.py collectstatic --noinput
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8000
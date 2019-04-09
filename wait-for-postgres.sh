#!/bin/bash
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

echo "Testing Postgres connection with psql ..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "postgres" -c '\q'; do
  #~ >&2 echo "Postgres is unavailable - sleeping"
  >&2 echo -n .
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd

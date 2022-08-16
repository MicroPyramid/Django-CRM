# CRM Installation using docker

- pull application image

```sh
docker pull micropyramid/crm:0.1
```

- setup environment variables, below variables are required.

```sh
# environment type, eg: stage, live
export ENV_TYPE=""
# sentry dns value, logs backend django project errors
export SENTRY_DSN=""
# sentry dns value, logs frontend react errors
export REACT_APP_DSN=""
# swagger api base/root url, eg: http://127.0.0.1
export SWAGGER_ROOT_URL=""
# postgresql database host address, eg: example.com or some ip address
export DBHOST=""
# postgresql database port
export DBPORT=""
# postgresql database name
export DBNAME=""
# postgresql database user name
export DBUSER=""
# postgresql database password
export DBPASSWORD=""
# s3 bucket name, required for storing media and static files.
export S3_BUCKET_NAME=""
# access key to access s3 bucket
export AWS_ACCESS_KEY_ID=""
# secret key to access s3 bucket
export AWS_SECRET_ACCESS_KEY=""
```

- run application

```sh
docker run \
  -n crm \
  -p 8000:80 \
  -e ENV_TYPE="$ENV_TYPE" \
  -e SENTRY_DSN="$SENTRY_DSN" \
  -e REACT_APP_DSN="$REACT_APP_DSN" \
  -e SWAGGER_ROOT_URL="$SWAGGER_ROOT_URL" \
  -e DBHOST="$DBHOST" \
  -e DBPORT="$DBPORT" \
  -e DBNAME="$DBNAME" \
  -e DBUSER="$DBUSER" \
  -e DBPASSWORD="$DBPASSWORD" \
  -e S3_BUCKET_NAME="$S3_BUCKET_NAME" \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  micropyramid/crm:0.1
```

- GOTO: http://127.0.0.1:8000

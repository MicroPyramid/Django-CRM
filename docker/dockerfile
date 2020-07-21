FROM ubuntu:18.04


ARG APPDIR=/root/djcrm

RUN apt-get update -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libpcre3 mime-support postgresql-client libgnutls28-dev libcurl4-gnutls-dev libexpat-dev libpython3.6 ruby-full wkhtmltopdf build-essential libpcre3-dev libpq-dev python3-pip gcc python3-dev
RUN pip3 install setuptools
RUN gem install sass

RUN mkdir ${APPDIR}
WORKDIR ${APPDIR}
ADD . ${APPDIR}
RUN mkdir ${APPDIR}/media
RUN mkdir ${APPDIR}/static/CACHE

RUN pip3 install --no-cache-dir -r ${APPDIR}/requirements.txt
RUN python3 manage.py collectstatic --noinput
RUN python3 manage.py compress --force
RUN python3 manage.py migrate

# remove build pkgs
# RUN apt-get remove --purge -y build-essential libpcre3-dev libpq-dev python3-pip gcc python3-dev


# uwsgi configuration
ARG UWSGI_HTTP
ENV UWSGI_WSGI_FILE=crm/wsgi.py
ENV UWSGI_HTTP=:${UWSGI_HTTP} UWSGI_MASTER=1 UWSGI_HTTP_AUTO_CHUNKED=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy

# django env vars
# ENV DJANGO_ENVIRONMENT=live

EXPOSE ${UWSGI_HTTP}
CMD ["uwsgi", "--show-config"]
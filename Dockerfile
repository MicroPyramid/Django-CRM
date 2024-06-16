FROM ubuntu:20.04

# Instalação de pacotes do sistema
RUN apt-get update -y && \
    apt-get install -y \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    libmariadbclient-dev \
    libjpeg62-dev \
    zlib1g-dev \
    libwebp-dev \
    curl \
    vim \
    net-tools

# Setup do usuário
RUN useradd -ms /bin/bash ubuntu
USER ubuntu

# Configuração do ambiente virtual Python
WORKDIR /home/ubuntu/app
COPY requirements.txt .

# Identificador: Configuração do ambiente virtual Python
RUN python3 -m venv venv
RUN /home/ubuntu/app/venv/bin/pip install -U pip
RUN /home/ubuntu/app/venv/bin/pip install -r requirements.txt

# Configuração da aplicação
COPY . .

# Configuração do servidor WSGI (Gunicorn)
RUN /home/ubuntu/app/venv/bin/pip install gunicorn

# Comando padrão para iniciar a aplicação
CMD ["/home/ubuntu/app/venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "myapp.wsgi:application"]


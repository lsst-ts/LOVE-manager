FROM python:3.8.2-buster

# Install required packages
RUN apt-get update && \
    apt-get install -y \
    libsasl2-dev \
    python-dev \
    libldap2-dev \
    libssl-dev &&\
    rm -rf /var/lib/apt/lists/*

# Set workdir and install python requirements
WORKDIR /usr/src/love
COPY manager/requirements.txt .
RUN pip install -r requirements.txt

# Copy source code and build project
COPY manager ./manager
WORKDIR /usr/src/love/manager
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
RUN python manage.py collectstatic --noinput

# Expose static files and port
VOLUME /usr/src/love/manager/static
VOLUME /usr/src/love/manager/media
EXPOSE 8000

# Set env variables for runtime (to be replaced in docker-compose files)
ENV ADMIN_USER_PASS=test
ENV USER_USER_PASS=test
ENV CMD_USER_PASS=test
ENV NO_DEBUG=True

# Run daphne server in runtime
CMD ["./runserver.sh"]

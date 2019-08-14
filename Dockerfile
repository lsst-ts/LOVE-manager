FROM python:3.6.7-stretch

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
COPY manager .
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
RUN python manage.py collectstatic --noinput

# Expose static files and port
VOLUME /usr/src/love/static
EXPOSE 8000

# Set env variables for runtime (to be replaced in docker-cpomse files)
ENV ADMIN_USER_PASS=test
ENV USER_USER_PASS=test
ENV CMD_USER_PASS=test

# Run daphne server in runtime
CMD ["./runserver.sh"]

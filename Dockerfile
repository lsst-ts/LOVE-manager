FROM python:3.6.7-stretch

# Install required packages
RUN apt-get update && \
    apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev

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

# Run daphne server in runtime
# CMD daphne -b 0.0.0.0 -p 8000 manager.asgi:application
ENTRYPOINT ["./runserver.sh"]

FROM python:3.6.7-stretch

# Install required packages
RUN apt-get update && \
    apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev

# Set workdir and install python requirements
WORKDIR /usr/src/love
COPY manager/requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY manager .

RUN ls -lah

CMD python manage.py runserver 0.0.0.0:8000 --settings=manager.production_settings

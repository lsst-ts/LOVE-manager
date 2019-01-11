FROM python:3.6.7-stretch

RUN apt-get update && \
    apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev

COPY ./manager/requirements.txt /home/docker/

RUN cd /home/docker && pip install -r requirements.txt

COPY ./manager /home/docker/manager

WORKDIR /home/docker/manager

RUN mkdir -p /home/LOVE/manager && cp -r /home/docker/manager /home/LOVE/manager

WORKDIR /home/LOVE/manager/manager

CMD python manage.py runserver 0.0.0.0:8000 --settings=manager.production_settings
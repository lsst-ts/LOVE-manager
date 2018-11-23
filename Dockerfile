FROM python:3.6.7-stretch

COPY ./manager/requirements.txt /home/docker/

RUN cd /home/docker && pip install -r requirements.txt

COPY ./manager /home/docker/manager

WORKDIR /home/docker/manager

CMD ["python", "manage.py", "runserver"]
FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

ENV DockerHOME=/home/app/webapp  
RUN mkdir -p $DockerHOME
COPY . $DockerHOME
WORKDIR $DockerHOME

RUN apt-get update
RUN apt-get install redis-server -y

RUN pip install -r requirements.txt

EXPOSE 80
ENTRYPOINT ./production.sh
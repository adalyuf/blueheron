#!/bin/bash

#Python setup
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

#Celery detached background processes
celery --app=topranks worker --loglevel=info --detach --queues celery,express --concurrency=30 -n standard@%d

#Gunicorn web server
gunicorn topranks.wsgi -b 0.0.0.0:80 --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread

#To monitor celery in production, run flower locally with below command.
#celery --app=topranks --broker=redis://:TopRedisPass99@18.220.172.92:6379 flower --port=5566

#To have local machine help production queue, edit the devcontainer/docker-compose to use aws-production.env file and rebuild container
#Then rebuild container and start celery worker with below command
#celery --app=topranks --broker=redis://:TopRedisPass99@18.220.172.92:6379 worker --loglevel=info

# You'll know you're using the wrong database if the save commands come back in under 0.1s
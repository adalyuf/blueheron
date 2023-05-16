#!/bin/bash

#Redis daemon
redis-server --daemonize yes --requirepass LocalRedisPass
ps aux | grep redis

#Celery detached background processes
celery --app=topranks worker --loglevel=info --detach --queues express --concurrency=10 -n express1@%d
celery --app=topranks worker --loglevel=info --detach --queues celery,express --concurrency=50 -n worker1@%d
ps aux | grep celery

#For celery-flower dashboard, run following:
#local
#celery --app=topranks --broker=redis://:LocalRedisPass@localhost:6379 flower --port=5555

python manage.py runserver

#!/bin/bash

#Redis daemon
redis-server --daemonize yes
ps aux | grep redis

#Celery detached background processes
celery --app=topranks worker --loglevel=info --detach
ps aux | grep celery

#For celery-flower dashboard, run following:
#local
#celery --app=topranks --broker=redis://localhost:6379 flower --port=5555

python manage.py runserver

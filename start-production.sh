#!/bin/bash

# JS/CSS Asset build
# cd _keenthemes/tools/
# . /usr/local/share/nvm/nvm.sh
# nvm install 18
# nvm use 18
# npm install
# npm run build
# cd ../..
# cp assets/* static/ -r
# rm assets -r

#Python setup
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

#Redis daemon
# redis-server --daemonize yes

#Celery detached background processes
celery --app=topranks worker --loglevel=info --detach

#Gunicorn web server
#old slowness
# gunicorn topranks.wsgi -b 0.0.0.0:80
# new hotness: https://pythonspeed.com/articles/gunicorn-in-docker/
gunicorn topranks.wsgi -b 0.0.0.0:80 --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread

#To monitor celery in production, run flower locally with below command.
#celery --app=topranks --broker=redis://:TopRedisPass99@3.145.166.233:6379 flower --port=5555
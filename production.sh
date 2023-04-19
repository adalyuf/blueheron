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

#Redis daemon
redis-server --daemonize yes

#Celery detached background processes
celery --app=topranks worker --loglevel=info --detach

#Gunicorn web server
gunicorn topranks.wsgi -b 0.0.0.0:80


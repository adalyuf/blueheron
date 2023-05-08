#!/bin/bash
#Install Redis
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis -y

# JS/CSS Asset build
sh ./install-nvm-locally.sh

#Python setup
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate accounts #run first to ensure installation of postgres extension and creating unique index on email
python manage.py migrate account
python manage.py migrate
python manage.py importdomains domains.csv
python manage.py startproducts

#Redis daemon
redis-server --daemonize yes
ps aux | grep redis

#Celery detached background processes
celery --app=topranks worker --loglevel=info --detach
ps aux | grep celery

#For celery-flower dashboard, run following:
#local
#celery --app=topranks --broker=redis://localhost:6379 flower --port=5555

#To clear out the database:
# stop the server, if running
# go into a local terminal and go to the topranks directory
# docker ps
# docker stop topranks_devcontainer_db_1
# docker rm topranks_devcontainer_db_1
# docker volume ls
# docker volume rm topranks_devcontainer_postgres-data
#
# back in the vscode window, F1 and Dev Container: Rebuild and reopen

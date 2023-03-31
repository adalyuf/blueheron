#!/bin/bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate accounts #run first to ensure installation of postgres extension and creating unique index on email
python manage.py migrate account
python manage.py migrate
python manage.py importdomains domains.csv
python manage.py startproducts

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
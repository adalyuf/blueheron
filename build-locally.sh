#!/bin/bash

#Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
export NVM_DIR="/usr/local/share/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

#Build node modules
cd _keenthemes/tools/
nvm install 18
nvm use 18
npm install
npm run build
cd ../..
mkdir static_build -p
cp assets/* static_build/ -r
rm assets -r

#Install Redis
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis -y

#Python setup
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate accounts #run first to ensure installation of postgres extension and creating unique index on email
python manage.py migrate account
python manage.py migrate
python manage.py importdomains domains.csv
python manage.py startproducts
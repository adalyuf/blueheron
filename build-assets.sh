#!/bin/bash

cd _keenthemes/tools/
# . /usr/local/share/nvm/nvm.sh
nvm install 18
nvm use 18
npm install
npm run build
cd ../..
mkdir static -p
cp assets/* static/ -r
rm assets -r
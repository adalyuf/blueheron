# TopRanks.ai

To get container up and running:

```
git clone https://github.com/adalyuf/topranks.git
```

```
cd topranks
code .
```

Ask the author for the .env file with secrets and add this into the main (topranks) directory.

In VSCode press `F1` and `Rebuild and reopen in container`

The startup.sh script should run and will set up css/js files with npm and install packages with pip.

After this runs, start local versions of Redis, Celery, and the web server with `./start-local.sh`

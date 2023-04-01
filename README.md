# blueheron

To get container up and running:

```
git clone https://github.com/adalyuf/blueheron.git
```

```
cd blueheron
code .
```

Ask the author for the .env file with secrets and add this into the main (blueheron) directory.

The .env file has the following:

- OPENAI_API_KEY=
- DJANGO_SECRET_KEY=
- USE_NGROK=True

In VSCode press `F1` and `Rebuild and reopen in container`

The startup.sh script should run and will set up css/js files with npm and install packages with pip.

After this runs, start the server with `python manage.py runserver`

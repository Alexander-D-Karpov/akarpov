# akarpov

My collection of apps and tools

Writen in Python 3.11 and Django 4.2

Local upstream mirror:
https://git.akarpov.ru/sanspie/akarpov

## Start up

### installation
```shell
$ poetry install & poetry shell
$ python3 manage.py migrate
```

### local run
```shell
$ python3 manage.py runserver
$ celery -A config.celery_app worker --loglevel=info
$ uvicorn redirect.app:app --reload
```


### local run via docker

```shell
$ docker-compose -f local.yml up
```
Install file preview dependencies
```shell
$ docker-compose -f local.yml exec django /install_preview_dependencies
```
- server - http://127.0.0.1:8000
- mail - http://127.0.0.1:8025


### refactoring code
```shell
$ pre-commit install
$ black akarpov
$ no_implicit_optional akarpov
$ mypy --config-file setup.cfg akarpov
```

### list of projects:
- blog
- fileshare
- music radio + processor
- test platform
- short link generator
- about me app
- gallery
- notifications

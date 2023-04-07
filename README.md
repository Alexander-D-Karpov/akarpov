# akarpov

My collection of apps and tools

Writen in Python 3.11 and Django 4.2

### local run via docker

```shell
$ docker-compose -f local.yml up
```
- server - http://127.0.0.1:8000
- mail - http://127.0.0.1:8025


### refactoring code
```shell
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

# Hubble Python Services

[![codecov](https://codecov.io/gh/jina-ai/executor-normalizer/branch/main/graph/badge.svg?token=qS6ukBVDwL)](https://codecov.io/gh/jina-ai/executor-normalizer)

Hubble-related http services that rely on Python and Jina Core. It contains several components:

- Normalizer
- Generator

## Normalizer

Normalize Executor packages uploaded by users.

### Features

- Complete `config.yml`
- Complete `Dockerfile`
- Identify `Executor` class name
- Identify **Illegal** executor
- Support **topological sort of py-modules** based on there dependency relations

## Generator

Generate Kubernetes/Docker Compose/JCloud yaml configuration.

## Setup

```bash
$ git clone https://github.com/jina-ai/executor-normalizer.git
$ cd executor-normalizer

# Make a venv in local dir
$ make env

# Install as a CLI
$ make init
```



## Usage

### Command line interface

```bash
$ executor_manager normalize /path/to/executor_folder -v
$ executor_manager generate Hello/latest --type k8s --protocol http
```

### Http service

First, we need to build a docker image based on codebase.

`docker build -t local-hubble-normalizer .`

```
# access docs via http://127.0.0.1:8888/docs
$ docker run -it --rm -p 8888:8888 -v ${PWD}:/workspace local-hubble-normalizer
```

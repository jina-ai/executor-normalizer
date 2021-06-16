# Executor Package Normalizer in Hubble


***🦆 Note: `master` branch is the developing branch.**

## 💡 Features

- ✅ Complete `config.yml`
- ✅ Complete `Dockerfile`
- ✅ Identify `Executor` class name
- ✅ Identify **Illegal** executor
- ✅ Support **toplogical sort of py-modules** based on theire dependency relations

## 🚀 Setup

```bash

$ git clone https://github.com/jina-ai/executor-normalizer.git
$ cd executor-normalizer

# Option 1: install as a command tool
$ pip install .

# Option 2: build restful service docker image
$ docker build -t jinaai/executor_normalizer .
```



## 👋 Usage

-  Usage as a command tool for ease-of-testing

```bash
$ normalizer /path/to/executor_folder -v
```

- Deploy a service via Docker container

```
# access docs via http://127.0.0.1:8888/normalizer/docs
$ docker run -it --rm -p 8888:8888 -v ${PWD}:/workspace jinaai/executor_normalizer
```

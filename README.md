# Executor Package Normalizer in Hubble


***🦆 Note: `master` branch is the developing branch.**


## 🚀 Setup

```bash
# install locally
$ git clone https://github.com/jina-ai/executor-normalizer.git
$ cd executor-normalizer

$ pip install .
```

```bash
# deploy as a restful service
$ docker build -t jinaai/executor_normalizer .
$ docker run -it --rm -v ${PWD}:/workspace -p 8888:8888 jinaai/executor_normalizer
```

## 👋 Usage

```bash
# local
$ normalizer --help
$ normalizer /path/to/executor_folder -v

# deploy a restful service listening at `:8888`
$ uvicorn server.app:app --host 0.0.0.0 --port 8888 --reload

# build docker image and deploy service
$ docker build -t jinaai/executor_normalizer .
# access docs via http://127.0.0.1:8888/normalizer/docs
$ docker run -it --rm -p 8888:8888 -v ${PWD}:/workspace jinaai/executor_normalizer
```

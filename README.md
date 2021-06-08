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
$ docker build -t jinaai/executor_normalizer .
```

## 📖 Usage

```bash
# local
$ normalizer --help

# start server locally
$ uvicorn server.app:app --host 0.0.0.0 --port 8888 --reload

# start server container, access docs via http://127.0.0.1:8888/normalizer/docs
$ docker run -it --rm -p 8888:8888 jinaai/executor_normalizer
```

## 👋 Success cases

Test cases of executor patterns:

```bash
# step 1
$ git clone https://github.com/jina-ai/executor-cases.git
$ cd executor-cases/success

# step 2: test specific case
$ cd case1

# normalize the executor pacakge (i.e., complete `Dockerfile`)
$ cd case1 && normalize . -v

# step 3: test the Docker image
$ docker build -t jinaai/hub_case1 . --build-arg JINA_VERSION=master
$ docker run -it --rm jinaai/hub_case1
```

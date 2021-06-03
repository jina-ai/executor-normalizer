ARG PY_VERSION=3.8

FROM python:${PY_VERSION}-slim

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev

RUN pip install --pre jina

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR /workspace

CMD [ "/bin/bash" ]

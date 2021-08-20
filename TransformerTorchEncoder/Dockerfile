FROM jinaai/jina:master-perf

RUN apt-get -y update && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

COPY . ./transformer-text-encoder/
WORKDIR ./transformer-text-encoder

# install requirements before copying the workspace
RUN pip install -r requirements.txt
RUN pip install -r requirements.txt

# setup the workspace
COPY . /workspace
WORKDIR /workspace

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]

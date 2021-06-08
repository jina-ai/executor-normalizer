FROM jinaai/jina:master

# setup the workspace
WORKDIR /workspace

ADD . .

RUN pip install .

ENTRYPOINT [ "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8888", "--reload" ]

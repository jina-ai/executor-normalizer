FROM jinaai/jina:2.0.3-py38-standard

# setup the workspace
WORKDIR /workspace

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . .

RUN pip install .

ENTRYPOINT [ "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8888", "--reload" ]

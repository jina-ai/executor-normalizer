FROM replco/upm:full as upm_full


FROM jinaai/jina:latest

COPY --from=upm_full /usr/local/bin/upm /usr/local/bin/upm

# setup the workspace
WORKDIR /workspace

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . .

RUN pip install .

ENTRYPOINT [ "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8888", "--reload" ]

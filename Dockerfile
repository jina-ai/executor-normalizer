ARG JINA_VERSION
FROM jinaai/jina:latest

ARG JINA_VERSION

# setup the workspace
COPY . /workspace
WORKDIR /workspace

# install the third-party requirements
RUN pip install -r requirements.txt

# for testing the image
RUN pip install pytest && pytest

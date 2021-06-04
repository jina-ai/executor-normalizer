ARG JINA_VERSION
ARG BUILD_DATE

FROM jinaai/jina:$JINA_VERSION

# setup the workspace
COPY . /workspace
WORKDIR /workspace

# install the third-party requirements
RUN pip install -r requirements.txt

# for testing the image
RUN pip install pytest && pytest

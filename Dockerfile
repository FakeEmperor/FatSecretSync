FROM python:3.11-slim
LABEL MAINTAINER="FakeEmperor <6287317+FakeEmperor@users.noreply.github.com>"

ARG RELEASE_VERSION="0.0.1-dev.0"
LABEL VERSION="${RELEASE_VERSION}"

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and package dependencies
RUN apt update \
  && apt install --no-install-recommends -y \
            libsm6 \
            libxext6 \
            libmagic1 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY pre-requirements.txt /app
RUN pip install --pre -r pre-requirements.txt

COPY . /app
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${RELEASE_VERSION} pip install -e .

CMD ["fatsecret-sync", "bot", "start"]

FROM python:3.11-slim

ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN apt update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt install -qq --yes --no-install-recommends \
    locales \
    autoconf \
    automake \
    build-essential \
    ccache \
    cmake \
    gettext \
    git \
    libffi-dev \
    libltdl-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libssl-dev \
    libtinfo6 \
    libtool \
    openjdk-17-jdk \
    patch \
    pkg-config \
    sudo \
    unzip \
    zip \
    zlib1g-dev \
    && locale-gen en_US.UTF-8 \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade \
    buildozer \
    virtualenv \
    pip \
    appdirs \
    packaging \
    colorama \
    jinja2 \
    toml \
    build

RUN pip install --user --upgrade "Cython==0.29.37"

WORKDIR /root/hostcwd

ENTRYPOINT ["buildozer"]

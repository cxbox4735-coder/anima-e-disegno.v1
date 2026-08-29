FROM python:3.11-slim

ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

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
    default-jdk \
    patch \
    pkg-config \
    sudo \
    unzip \
    zip \
    zlib1g-dev \
    && locale-gen en_US.UTF-8 \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Installa buildozer e dipendenze globalmente (come root)
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

# IMPORTANTE: Cython va installato con --user perché il hostpython3 di p4a
# (quello che compila le estensioni C) vede solo i pacchetti user-site
RUN pip install --user --upgrade "Cython<0.30"

WORKDIR /root/hostcwd

ENTRYPOINT ["buildozer"]

FROM python:3.11-slim

ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    JAVA_HOME=/opt/jdk-17 \
    PATH="/opt/jdk-17/bin:${PATH}"

# Installa Java 17 da Eclipse Temurin (compatibile con vecchie Android CLI Tools)
RUN apt update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt install -qq --yes --no-install-recommends \
    wget \
    ca-certificates \
    && wget -q https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz \
    && tar -xzf OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz -C /opt \
    && mv /opt/jdk-17.0.12+7 /opt/jdk-17 \
    && rm OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz \
    && apt-get purge -y --auto-remove wget \
    && rm -rf /var/lib/apt/lists/*

# Dipendenze di sistema
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
    patch \
    pkg-config \
    sudo \
    unzip \
    zip \
    zlib1g-dev \
    && locale-gen en_US.UTF-8 \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Buildozer e dipendenze Python
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

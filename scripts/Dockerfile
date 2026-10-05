# Ubuntu 18.04 keeps the glibc requirement at 2.27 for older ArkOS installations.
FROM ubuntu:18.04@sha256:152dc042452c496007f07ca9127571cb9c29697f42acbfad72324b2bb2e43c98
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential cmake pkg-config libsdl2-dev python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work

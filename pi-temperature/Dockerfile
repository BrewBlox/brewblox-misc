FROM ubuntu:22.04
LABEL org.opencontainers.image.source=https://github.com/BrewBlox/brewblox-misc

WORKDIR /app

COPY ./publish-temp.sh /app/publish-temp.sh

RUN set -ex \
    && apt-get update \
    && apt-get install -y \
        mosquitto-clients \
    && rm -rf /var/lib/apt/lists/*

CMD ["/app/publish-temp.sh"]

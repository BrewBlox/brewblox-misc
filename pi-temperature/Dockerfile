FROM ubuntu:20.04
WORKDIR /app

ENV LD_LIBRARY_PATH=/opt/vc/lib

COPY ./publish-temp.sh /app/publish-temp.sh

RUN set -ex \
    && apt-get update \
    && apt-get install -y \
        mosquitto-clients \
        libraspberrypi-bin \
    && rm -rf /var/lib/apt/lists/*

CMD ["/app/publish-temp.sh"]

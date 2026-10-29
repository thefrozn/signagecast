# SignageCast als Docker-/Podman-Container (amd64). Alle Einstellungen und Daten liegen im Volume /data.
#   docker run -d --name signagecast --device /dev/dri -p 8888:8888 -p 19090:19090 -v signagecast:/data \
#     -e TZ=Europe/Berlin -e SC_HOST_IP=<IP des Docker-Hosts> ghcr.io/thefrozn/signagecast
# Verwaltung http://<host>:19090 (Startpasswort im Protokoll: docker logs signagecast), Stream http://<host>:8888/tv
# 19090 statt 9090: auf vielen Servern belegt dort schon Cockpit den Port (wichtig im Host-Netz). Ports änderbar über
# SC_VERWALTUNG_PORT und SC_STREAM_PORT.
FROM debian:trixie-slim

ARG MTX_VERSION=v1.21.3
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 PYTHONUNBUFFERED=1 \
    SC_BETRIEB=container SC_VERWALTUNG_PORT=19090 SC_STREAM_PORT=8888

RUN sed -i "s/^Components:.*/Components: main contrib non-free non-free-firmware/" /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends xvfb chromium ffmpeg vainfo intel-media-va-driver-non-free mesa-va-drivers \
      pulseaudio pulseaudio-utils fonts-roboto-unhinted fonts-dejavu-core fonts-open-sans fonts-lato fonts-montserrat \
      fonts-ubuntu fonts-cantarell fonts-comic-neue fonts-firacode fonts-noto-core fonts-noto-color-emoji \
      python3 curl ca-certificates procps tini tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && F=mediamtx_${MTX_VERSION}_linux_amd64.tar.gz && cd /tmp \
 && curl -sSfLO "https://github.com/bluenviron/mediamtx/releases/download/$MTX_VERSION/$F" \
 && curl -sSfL -o sum "https://github.com/bluenviron/mediamtx/releases/download/$MTX_VERSION/checksums.sha256" \
 && grep -F "*$F" sum | sha256sum -c - \
 && mkdir -p /opt/mediamtx && tar xzf "$F" -C /opt/mediamtx && rm -f "$F" sum \
 && useradd -r -M -d /var/lib/signagecast -s /usr/sbin/nologin signagecast \
 && mkdir -p /data/config && ln -s /data /var/lib/signagecast && ln -s /data/config /etc/signagecast

COPY VERSION LICENSE NOTICE.md /opt/signagecast/
COPY app /opt/signagecast/app
COPY www /opt/signagecast/www
COPY render /opt/signagecast/render
COPY cockpit/signagecast /opt/signagecast/cockpit/signagecast
COPY profile /opt/signagecast/profile
COPY docker/start.sh /opt/signagecast/docker/start.sh
RUN chmod -R a+rX,go-w /opt/signagecast && chmod 755 /opt/signagecast/render/tv-render.sh /opt/signagecast/docker/start.sh

LABEL org.opencontainers.image.title="SignageCast" \
      org.opencontainers.image.description="Turn any TV into a calm information screen with live wildlife cams" \
      org.opencontainers.image.source="https://github.com/thefrozn/signagecast" \
      org.opencontainers.image.licenses="MIT"
EXPOSE 8888 19090
VOLUME /data
HEALTHCHECK --interval=60s --timeout=5s --start-period=60s CMD curl -fs -o /dev/null http://127.0.0.1:8080/daten.json || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/signagecast/docker/start.sh"]

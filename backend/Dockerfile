FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PIPX_HOME=/opt/pipx
ENV PIPX_BIN_DIR=/usr/local/bin
ENV GOPATH=/go
ENV PATH="/go/bin:/usr/local/bin:${PATH}"
ENV HOME=/app/runtime/home
ENV XDG_CONFIG_HOME=/app/runtime/config
ENV XDG_CACHE_HOME=/app/runtime/cache
ENV XDG_DATA_HOME=/app/runtime/data
ENV TMPDIR=/app/runtime/tmp
ENV NXC_PATH=/app/runtime/home/.nxc
ENV NETEXEC_HOME=/app/runtime/nxc

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gosu \
    curl \
    git \
    nmap \
    pipx \
    golang-go \
    rustc \
    cargo \
    build-essential \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 openadzero \
    && useradd --system --uid 10001 --gid openadzero --home /app --shell /usr/sbin/nologin openadzero

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

RUN pipx install git+https://github.com/Pennyw0rth/NetExec \
    || pipx install --pip-args="--no-cache-dir" git+https://github.com/Pennyw0rth/NetExec
RUN mkdir -p /app/runtime/home/.nxc /app/runtime/config/nuclei /app/runtime/cache /app/runtime/data /app/runtime/tmp /app/runtime/nxc \
    && command -v nxc && HOME=/app/runtime/home NXC_PATH=/app/runtime/home/.nxc nxc --help >/tmp/nxc_help.txt

# Tooling used by the controlled Tool Automation Library. Some upstream tools
# are intentionally best-effort so local builds can still complete and the API
# can report missing optional binaries through /tool-automation/tool-health.
RUN pipx install impacket \
    && pipx install bloodyAD \
    && pipx install coercer \
    || true
RUN pipx install git+https://github.com/login-securite/DonPAPI.git || true
RUN pipx install git+https://github.com/micahvandeusen/gMSADumper.git || true
RUN git clone --depth 1 https://github.com/lgandx/Responder.git /opt/Responder \
    && ln -sf /opt/Responder/Responder.py /usr/local/bin/responder \
    || true

RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
RUN command -v nuclei && XDG_CONFIG_HOME=/app/runtime/config XDG_CACHE_HOME=/app/runtime/cache nuclei -version

COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY app /app/app
COPY scripts /app/scripts
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY nuclei-templates-safe /app/nuclei-templates-safe

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p \
      /app/evidence \
      /app/evidence/tool-runs \
      /app/evidence/findings \
      /app/evidence/artifacts \
      /app/runtime/home \
      /app/runtime/config \
      /app/runtime/cache \
      /app/runtime/data \
      /app/runtime/tmp \
      /app/runtime/home/.nxc \
      /app/runtime/config/nuclei \
      /app/runtime/nxc \
      /app/runtime/responder \
    && chown -R openadzero:openadzero /app/evidence /app/runtime

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

FROM python:3.14-slim-bookworm

ARG GO_VERSION=1.25.7


ENV DEBIAN_FRONTEND=noninteractive
ENV PIPX_HOME=/opt/pipx
ENV PIPX_BIN_DIR=/usr/local/bin
ENV PIPX_DEFAULT_PYTHON=/usr/local/bin/python
ENV GOPATH=/go
ENV CARGO_HOME=/opt/cargo
ENV RUSTUP_HOME=/opt/rustup
ENV PATH="/opt/metasploit-framework/bin:/opt/cargo/bin:/usr/local/go/bin:/go/bin:/usr/local/bin:${PATH}"
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
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/runtime/tmp /app/runtime/home /app/runtime/config /app/runtime/cache /app/runtime/data /app/runtime/nxc /opt/cargo /opt/rustup \
    && chmod 1777 /app/runtime/tmp

RUN python -m pip install --no-cache-dir --upgrade pip pipx

RUN curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tgz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tgz \
    && rm -f /tmp/go.tgz \
    && go version

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain stable \
    && rustc --version \
    && cargo --version





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
    && pipx inject impacket setuptools wheel \
    && pipx install bloodyAD \
    && pipx install coercer \
    || true
RUN pipx install git+https://github.com/login-securite/DonPAPI.git || true
RUN pipx install git+https://github.com/micahvandeusen/gMSADumper.git || true
RUN rm -rf /opt/Responder \
    && git clone --depth 1 https://github.com/lgandx/Responder.git /opt/Responder \
    || true

RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
RUN command -v nuclei && XDG_CONFIG_HOME=/app/runtime/config XDG_CACHE_HOME=/app/runtime/cache nuclei -version


# Extra AD / SMB / Kerberos tooling for full lab usage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    smbclient \
    samba-common-bin \
    ldap-utils \
    krb5-user \
    python3-pip \
    python3-venv \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade \
    setuptools \
    wheel \
    netifaces \
    aioquic \
    ldap3 \
    dnspython \
    pycryptodome \
    pycryptodomex \
    PyYAML \
    impacket

# enum4linux-ng
RUN git clone --depth 1 https://github.com/cddmp/enum4linux-ng.git /opt/enum4linux-ng \
    && python -m pip install --no-cache-dir -r /opt/enum4linux-ng/requirements.txt \
    && chmod +x /opt/enum4linux-ng/enum4linux-ng.py \
    && printf '%s\n' '#!/bin/sh' 'exec python /opt/enum4linux-ng/enum4linux-ng.py "$@"' > /usr/local/bin/enum4linux-ng \
    && chmod +x /usr/local/bin/enum4linux-ng \
    && enum4linux-ng -h >/tmp/enum4linux-ng-help.txt 2>&1 || true

# Kerbrute
RUN export PATH="/usr/local/go/bin:/go/bin:/usr/local/bin:${PATH}" \
    && git clone --depth 1 https://github.com/ropnop/kerbrute.git /tmp/kerbrute \
    && cd /tmp/kerbrute \
    && go build -o /usr/local/bin/kerbrute . \
    && chmod +x /usr/local/bin/kerbrute \
    && rm -rf /tmp/kerbrute \
    && kerbrute --help >/tmp/kerbrute-help.txt 2>&1 || true

# gMSADumper
RUN git clone --depth 1 https://github.com/micahvandeusen/gMSADumper.git /opt/gMSADumper \
    && if [ -f /opt/gMSADumper/requirements.txt ]; then python -m pip install --no-cache-dir -r /opt/gMSADumper/requirements.txt; fi \
    && chmod +x /opt/gMSADumper/gMSADumper.py \
    && printf '%s\n' '#!/bin/sh' 'exec python /opt/gMSADumper/gMSADumper.py "$@"' > /usr/local/bin/gMSADumper.py \
    && chmod +x /usr/local/bin/gMSADumper.py \
    && ln -sf /usr/local/bin/gMSADumper.py /usr/local/bin/gMSADumper \
    && gMSADumper.py -h >/tmp/gmsadumper-help.txt 2>&1 || true

# Responder Python deps + stable launcher.
RUN rm -f /usr/local/bin/responder \
    && test -f /opt/Responder/Responder.py \
    && if [ -f /opt/Responder/requirements.txt ]; then python -m pip install --no-cache-dir -r /opt/Responder/requirements.txt; fi \
    && python -m pip install --no-cache-dir netifaces aioquic \
    && { echo '#!/bin/sh'; echo 'exec /usr/local/bin/python /opt/Responder/Responder.py "$@"'; } > /usr/local/bin/responder \
    && chmod +x /usr/local/bin/responder \
    && responder -h >/tmp/responder-help.txt 2>&1 || true


# Metasploit Framework official nightly installer.
RUN if ! command -v msfconsole >/dev/null 2>&1; then \
      apt-get update \
      && apt-get install -y --no-install-recommends curl ca-certificates gnupg lsb-release \
      && rm -rf /var/lib/apt/lists/* \
      && curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > /tmp/msfinstall \
      && chmod 755 /tmp/msfinstall \
      && /tmp/msfinstall \
      && ln -sf /opt/metasploit-framework/bin/msfconsole /usr/local/bin/msfconsole \
      && ln -sf /opt/metasploit-framework/bin/msfvenom /usr/local/bin/msfvenom \
      && ln -sf /opt/metasploit-framework/bin/msfdb /usr/local/bin/msfdb ; \
    fi \
    && msfconsole --version >/tmp/msfconsole-version.txt 2>&1 || true


# Final Impacket wrapper repair.
# Some global pip installs can overwrite pipx symlinks in /usr/local/bin.
RUN python -m pip install --no-cache-dir --upgrade "setuptools<81" wheel \
    && pipx runpip impacket install --upgrade "setuptools<81" wheel \
    && for f in /opt/pipx/venvs/impacket/bin/*.py; do \
         b="$(basename "$f")"; \
         rm -f "/usr/local/bin/$b"; \
         ln -s "$f" "/usr/local/bin/$b"; \
       done \
    && readlink -f /usr/local/bin/GetNPUsers.py \
    && GetNPUsers.py -h >/tmp/impacket-getnpusers-help.txt 2>&1 || true

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

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PIPX_HOME=/opt/pipx
ENV PIPX_BIN_DIR=/usr/local/bin
ENV GOPATH=/go
ENV PATH="/go/bin:/usr/local/bin:/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
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

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

RUN pipx install git+https://github.com/Pennyw0rth/NetExec \
    || pipx install --pip-args="--no-cache-dir" git+https://github.com/Pennyw0rth/NetExec
RUN command -v nxc && nxc --help >/tmp/nxc_help.txt

RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
RUN command -v nuclei && nuclei -version

COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY app /app/app
COPY nuclei-templates-safe /app/nuclei-templates-safe

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

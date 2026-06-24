FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends nmap git pipx golang-go ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
ENV PATH="/root/.local/bin:${PATH}"
RUN pipx install git+https://github.com/Pennyw0rth/NetExec
ENV GOPATH=/go
ENV PATH="/go/bin:/root/.local/bin:${PATH}"
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY app /app/app
COPY nuclei-templates-safe /app/nuclei-templates-safe
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

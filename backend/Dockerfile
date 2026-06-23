FROM python:3.12-slim
ENV PATH="/root/.local/bin:${PATH}"
RUN apt-get update && apt-get install -y --no-install-recommends nmap git pipx build-essential python3-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
RUN pipx install git+https://github.com/Pennyw0rth/NetExec || true
COPY app /app/app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

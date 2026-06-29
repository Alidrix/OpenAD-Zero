from pathlib import Path
import os
import tempfile


evidence_dir = Path(os.environ.get("EVIDENCE_DIR", "/app/evidence"))
evidence_dir.mkdir(parents=True, exist_ok=True)

for child in ["tool-runs", "findings", "artifacts"]:
    (evidence_dir / child).mkdir(parents=True, exist_ok=True)

with tempfile.NamedTemporaryFile(dir=evidence_dir, delete=True) as f:
    f.write(b"ok")

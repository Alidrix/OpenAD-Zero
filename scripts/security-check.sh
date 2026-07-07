#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "[FAIL] $1"
  exit 1
}

if git ls-files | rg -q '(^|/)\.env(\.local|\.[^.]+\.local)?$'; then
  fail "Local .env file committed"
fi

if rg -n "BLOODHOUND_API_TOKEN|DATABASE_URL|REDIS_URL|OPENADZERO_API_TOKEN" frontend/src; then
  fail "Secret-like backend env exposed in frontend/src"
fi

if rg -n "VITE_OPENADZERO_API_TOKEN|VITE_[A-Z0-9_]*(TOKEN|SECRET|KEY)" frontend/src --glob '!**/*.test.*'; then
  fail "Secret-like VITE variable found in frontend/src"
fi


if rg -n "TWENTY_FIRST_API_KEY" --glob '!docs/**' --glob '!scripts/security-check.sh' --glob '!frontend/node_modules/**' --glob '!node_modules/**' .; then
  fail "21st.dev API key variable found"
fi

if rg -n "21st\.dev" --glob '!docs/**' --glob '!scripts/security-check.sh' --glob '!frontend/node_modules/**' --glob '!node_modules/**' .; then
  fail "21st.dev reference found outside allowed documentation"
fi

if rg -n "raw_command|shell_command|child_process|exec\(" frontend/src --glob '!**/*.test.*'; then
  fail "Raw frontend command execution material found"
fi


if rg -n "JSON\.stringify\([^)]*(command|argv|shell|raw_command|human_approved)" frontend/src --glob '!**/*.test.*'; then
  fail "Frontend approval payload may send raw command material"
fi

if rg -n "chmod 777" --glob '!node_modules/**' --glob '!frontend/node_modules/**' --glob '!scripts/security-check.sh' .; then
  fail "chmod 777 found"
fi

if rg -n "shell=True" backend/app; then
  fail "shell=True found in backend/app"
fi

if rg -n "subprocess\.(run|Popen|call|check_call|check_output)\(\s*f?['\"]" backend/app; then
  fail "String subprocess command found in backend/app"
fi

if rg -n "extractall\(|extract\(" backend/app/normalization backend/app/parsers; then
  fail "Unsafe ZIP extraction helper found in normalization/parsers"
fi

if find backend/tests/fixtures/normalization -type f \( -name "*.zip" -o -name "*.bin" -o -name "*.dat" -o -name "*.sqlite" -o -name "*.db" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.pdf" -o -name "*.7z" -o -name "*.tar" -o -name "*.gz" \) | grep -q .; then
  fail "Binary fixture found under backend/tests/fixtures/normalization"
fi


if rg -n "import subprocess|from subprocess" backend/app/pentest/rules; then
  fail "subprocess import found in pentest decision rules"
fi

if rg -n "command|argv|shell=True|raw_command" backend/app/pentest/rules --glob '!**/__pycache__/**'; then
  fail "Raw command material found in pentest decision rules"
fi

if python - <<'PYCHECK'
from pathlib import Path
text = Path("backend/app/approvals/schemas.py").read_text()
for cls in ["ApprovalPrepareRequest", "ApprovalApproveRequest", "ApprovalRejectRequest"]:
    start = text.index(f"class {cls}")
    end = text.find("\n\nclass ", start + 1)
    block = text[start:end if end != -1 else len(text)]
    if any(field in block for field in ["command:", "argv:", "shell:", "raw_command:", "command_hash:", "command_preview:", "human_approved:"]):
        raise SystemExit(1)
PYCHECK
then
  :
else
  fail "Approval frontend payload appears to accept command material"
fi

if rg -n "Path\(get_settings\(\)\.evidence_dir\)" backend/app --glob '!backend/app/core/paths.py' --glob '!backend/app/core/parameter_validation.py'; then
  fail "Direct evidence_dir path usage found"
fi

rg -q 'COPY scripts/docker-entrypoint\.sh /usr/local/bin/docker-entrypoint\.sh' backend/Dockerfile \
  || fail "Backend Dockerfile does not copy docker-entrypoint.sh"
rg -q 'ENTRYPOINT \["/usr/local/bin/docker-entrypoint.sh"\]' backend/Dockerfile \
  || fail "Backend Dockerfile does not define docker-entrypoint.sh as ENTRYPOINT"
rg -q 'exec gosu "\$APP_UID:\$APP_GID" "\$@"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not drop privileges with gosu APP_UID:APP_GID"
rg -q 'exec su-exec "\$APP_UID:\$APP_GID" "\$@"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not include su-exec APP_UID:APP_GID fallback"
rg -F -q 'APP_UID="${APP_UID:-10001}"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not default APP_UID to 10001"
rg -F -q 'APP_GID="${APP_GID:-10001}"' backend/scripts/docker-entrypoint.sh \
  || fail "docker-entrypoint.sh does not default APP_GID to 10001"


if PYTHONPATH=backend python - <<'PYCATALOG'
from app.tool_catalog.registry import list_template_metadata
bad=[]
danger={'mimikatz','lsass','secretsdump','psexec','wmiexec','smbexec','atexec','password spray','bruteforce','brute force','xp_cmdshell','pass-the-hash'}
for template in list_template_metadata():
    if template.execution_mode in {'manual_only','blocked'} and template.supported_for_run:
        bad.append(f"{template.template_id}:{template.execution_mode}:supported")
    argv_text = ' '.join(template.argv).casefold().replace('--no-bruteforce', '')
    if template.supported_for_run and any(word in argv_text for word in danger):
        bad.append(f"{template.template_id}:dangerous-keyword")
if bad:
    print('\n'.join(bad))
    raise SystemExit(1)
PYCATALOG
then
  :
else
  fail "Unsafe executable tool catalog template found"
fi

echo "[OK] security-check"

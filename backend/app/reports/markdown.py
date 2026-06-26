from datetime import datetime


def _v(x):
    return '' if x is None else str(x).replace('|', '\\|').replace('\n', ' ')


def _yn(x):
    return 'unknown' if x is None else ('yes' if x else 'no')


def _highest(risk):
    for s in ('critical', 'high', 'medium', 'low', 'info'):
        if risk.get(s, 0):
            return s
    return 'none'


def _recommendations(data):
    rec = set()
    for f in data.get('findings', []):
        blob = f'{f.get("title", "")} {f.get("description", "")} {f.get("source", "")}'.lower()
        sev = (f.get('severity') or '').lower()
        if 'smb signing' in blob:
            rec.add('Enable SMB signing where appropriate.')
        if 'rdp' in blob or f.get('port') == 3389:
            rec.add('Restrict RDP access and enforce MFA/jump host.')
        if 'winrm' in blob or f.get('port') in (5985, 5986):
            rec.add('Restrict WinRM and monitor usage.')
        if f.get('source') == 'nuclei' and sev in ('high', 'critical'):
            rec.add('Validate and remediate exposed web issue.')
        if f.get('source') == 'bloodhound' or 'path' in blob:
            rec.add('Review permissions, group memberships and delegation paths.')
    if not rec:
        rec.add('Review discovered exposures, validate business impact, and prioritize remediation by severity.')
    return sorted(rec)


def _ops_sections(data):
    obj = data.get('objective') or {}
    progress = data.get('progress') or {'score': 0, 'level': 'initialized', 'completed_items': [], 'missing_items': []}
    out = [
        '',
        '## Mission Objective',
        '',
        f'- Objective: {obj.get("objective_name") or "Not defined"}',
        f'- Type: {obj.get("objective_type") or "n/a"}',
        f'- Target: {obj.get("objective_target") or "n/a"}',
        f'- Status: {obj.get("objective_status") or "n/a"}',
        '',
        '## Mission Progress',
        '',
        f'- Score: {progress.get("score", 0)}%',
        f'- Level: {progress.get("level", "initialized")}',
        f'- Completed items: {", ".join(progress.get("completed_items") or []) or "None"}',
        f'- Missing items: {", ".join(progress.get("missing_items") or []) or "None"}',
        '',
        '## Mission Phases',
        '',
        '| Order | Phase | Status | Summary |',
        '|---|---|---|---|',
    ]
    for p in data.get('phases', []):
        out.append(
            f'| {_v(p.get("order_index"))} | {_v(p.get("name"))} | {_v(p.get("status"))} | {_v(p.get("summary"))} |'
        )
    out += ['', '## Timeline', '', '| Date | Source | Severity | Event |', '|---|---|---|---|']
    for t in data.get('timeline', []):
        out.append(
            f'| {_v(t.get("created_at"))} | {_v(t.get("source"))} | {_v(t.get("severity"))} | {_v(t.get("title"))} |'
        )
    return out


def render_markdown_report(data: dict) -> str:
    m = data['mission']
    risk = data.get('risk_summary', {})
    out = [
        '# OpenAD Zero Report',
        '',
        '## 1. Executive Summary',
        f'- Mission: {m.get("name")}',
        f'- Scenario: {m.get("scenario")}',
        f'- Mode: {m.get("mode")}',
        f'- Status: {m.get("status")}',
        f'- Hosts: {len(data.get("hosts", []))}',
        f'- Findings: {len(data.get("findings", []))}',
        f'- Highest severity: {_highest(risk)}',
        f'- Generated at: {datetime.utcnow().isoformat()}Z',
        '',
        '## 2. Mission Scope',
        f'- Raw scope: `{m.get("raw_scope")}`',
        f'- Validated targets: {", ".join(m.get("validated_targets") or []) or "None"}',
        f'- Created at: {m.get("created_at")}',
        f'- Started at: {m.get("started_at")}',
        f'- Completed at: {m.get("completed_at")}',
        '',
        '## 3. Methodology',
        '- Nmap discovery and service enumeration were used when nmap jobs exist.',
        '- NetExec SMB safe enumeration was included when SMB facts or shares exist.'
        if data.get('smb_facts') or data.get('smb_shares')
        else '- NetExec SMB safe enumeration was not present.',
        '- Nuclei safe web exposure scans were included when Nuclei findings exist.'
        if data.get('findings_by_source', {}).get('nuclei')
        else '- Nuclei safe web exposure scan data was not present.',
        '- BloodHound / SharpHound collection metadata was included when uploaded collections exist.'
        if data.get('bloodhound_collections')
        else '- BloodHound collection data was not present.',
        '- Evidence Manager metadata was included when evidence records exist.'
        if data.get('evidence')
        else '- Evidence Manager records were not present.',
        '',
        '## 4. Tool Summary',
    ]
    for k, v in data.get('tool_summary', {}).items():
        out.append(f'- {k}: {_yn(v)}')
    out += _ops_sections(data)
    out += [
        '',
        '## 5. Hosts and Services',
        '| IP | Hostname | OS Guess | DC Candidate | Services |',
        '|---|---|---|---|---|',
    ]
    for h in data.get('hosts', []):
        sv = ', '.join(f'{s["port"]}/{s["protocol"]} {s["name"]}' for s in h.get('services', []))
        out.append(
            f'| {_v(h.get("ip"))} | {_v(h.get("hostname"))} | {_v(h.get("os_guess"))} | {_yn(h.get("is_domain_controller_candidate"))} | {_v(sv)} |'
        )
    out += ['', '## 6. SMB / Windows Enumeration']
    if data.get('smb_facts'):
        for sf in data['smb_facts']:
            out.append(
                f'- {sf.get("ip")}: signing required={_yn(sf.get("smb_signing_required"))}, SMBv1={_yn(sf.get("smbv1_enabled"))}, null session={_yn(sf.get("null_session_possible"))}'
            )
    else:
        out.append('- No SMB facts available.')
    if data.get('smb_shares'):
        out.append('- Anonymous shares:')
        [
            out.append(f'  - {sh.get("ip")} {sh.get("name")} ({sh.get("access")})')
            for sh in data['smb_shares']
            if sh.get('anonymous')
        ]
    out += ['', '## 7. Web Exposure Findings']
    for w in data.get('web_targets', []):
        out.append(f'- Web target: {w.get("url")}')
    for f in data.get('findings_by_source', {}).get('nuclei', []):
        out.append(
            f'- {f.get("severity")}: {f.get("template_id")} matched {f.get("matched_at")} on {f.get("host") or f.get("ip")}'
        )
    out += ['', '## 8. Active Directory / BloodHound Analysis']
    for c in data.get('bloodhound_collections', []):
        out.append(
            f'- {c.get("filename")} SHA256={c.get("sha256")} zip_valid={_yn(c.get("zip_valid"))} ingestion={c.get("ingestion_status")}'
        )
    for s in data.get('bloodhound_stats', []):
        out.append(
            f'- Stats {s.get("domain_name")}: users={s.get("users_count")} computers={s.get("computers_count")} groups={s.get("groups_count")}'
        )
    for f in data.get('findings_by_source', {}).get('bloodhound', []):
        out.append(f'- {f.get("severity")}: {f.get("title")}')
    out += ['', '## 9. Findings', '| Severity | Source | Title | Host/IP | Confidence |', '|---|---|---|---|---|']
    for f in data.get('findings', []):
        out.append(
            f'| {_v(f.get("severity"))} | {_v(f.get("source"))} | {_v(f.get("title"))} | {_v(f.get("host") or f.get("ip"))} | {_v(f.get("confidence"))} |'
        )
    out += ['', '## 10. Evidence', '| Label | Category | Filename | SHA256 | Source |', '|---|---|---|---|---|']
    for e in data.get('evidence', []):
        out.append(
            f'| {_v(e.get("label"))} | {_v(e.get("category"))} | {_v(e.get("filename"))} | {_v(e.get("sha256"))} | {_v(e.get("source"))} |'
        )
    out += ['', '## 11. Recommended Next Steps'] + [f'- {r}' for r in _recommendations(data)]
    out += ['', '## 12. Technical Appendix', '### Jobs']
    for j in data.get('jobs', []):
        out.append(
            f'- {j.get("id")} {j.get("tool")}/{j.get("type")} status={j.get("status")} preview=`{j.get("command_preview")}`'
        )
    out += (
        ['### Evidence paths']
        + [f'- {e.get("stored_path")}' for e in data.get('evidence', [])]
        + ['### Report metadata', f'- Mission ID: {m.get("id")}']
    )
    return '\n'.join(out) + '\n'

# V2 Decision Rules

The decision-rule engine turns normalized scan assets, services, findings, signals, diagnostics, artifacts, and existing pentest actions into recommended next actions. It only recommends work: it does not launch tools, create RQ jobs, generate raw commands, or bypass approval/scope validation.

## Rule families

- **SMB**: TCP/445 recommends NetExec SMB fingerprint, signing review, null-session check, and null-session shares under `smb_enumeration`.
- **LDAP/Kerberos**: TCP/88, 389, 636, 3268, or 3269 recommends read-only AD discovery, LDAP signing review, Kerberos realm discovery, AD users/groups, computers, trusts, and a reinforced Kerberos user-enumeration preview. Domain is never invented; missing domain or userlist blocks affected actions.
- **Web**: HTTP-like ports produce normalized URLs for a Nuclei safe web exposure scan. The recommendation is constrained to safe local templates, severity filters, and no AI/headless/code/fuzzing/remote templates/free-form options.
- **WinRM/RDP**: Remote management and remote access ports produce assessment-only exposure, authentication, TLS/NLA, and policy reviews. No spraying, screenshots, command execution, or Evil-WinRM is proposed.
- **MSSQL**: TCP/1433 produces exposure and authentication surface reviews. Linked-server review is reinforced and blocked until credentials exist. xp_cmdshell and command execution are not proposed.
- **ADCS**: ADCS signals or certificate-service indicators produce exposure, ESC path, and certificate-template reviews. Exploitation remains manual-only/future work.
- **BloodHound / AD path analysis**: Existing BloodHound collection/import/path signals or artifacts recommend read-only graph analysis, shortest-path, dangerous privileges, kerberoastable-from-imported-data, and ACL reviews. SharpHound collection commands are not generated.
- **Credential exposure**: Anonymous SMB, null session, signing disabled, roastability, gMSA, weak policy, or exposed-secret signals recommend review/reporting actions and explicitly block secrets extraction as manual-only.
- **Evidence / reporting**: High or critical findings recommend evidence consolidation, interim report, executive summary, and remediation-plan preparation.

## Execution modes and priorities

Execution modes remain `safe_auto`, `approval_required`, `reinforced_approval_required`, and `manual_only`. In this prompt, `safe_auto` only means eligible for a future auto-run path; it never runs now. Priorities are numeric and stable: critical 100, high 80, medium 60, low 40, info 20. API action lists sort by descending priority and creation time.

## Idempotence

Each recommendation receives a stable `dedupe_key` derived from scan, phase, tool, template, and normalized resolved inputs. Recompute updates mutable metadata for proposed/waiting/blocked actions but does not reset approved, queued, running, completed, or rejected actions. Blocked actions can become proposed/waiting approval when missing inputs become available.

## Phase status

Phase states are refreshed from current actions: missing prerequisites or only blocked actions become `blocked`, proposed actions make the phase `ready`, waiting-approval actions make it `waiting_approval`, completed actions make it `completed`, and running/failed/skipped are preserved.

## Why nothing runs yet

Prompt 07 intentionally stops at recommendation intelligence. The next prompts can add the premium GUI, approval pop-up/Approve & Run, and RQ execution after approval while reusing these normalized recommendations.

## Prompt 11 Windows/AD tool catalog update

OpenAD-Zero now has a central Windows/AD tool catalogue grouped by family, risk, execution mode, parser/artifact expectations, and `supported_for_run` status. Decision rules normalize recommendations through the catalogue, approval preparation refuses manual-only/blocked templates, and approved-action run preparation remains limited to the existing Prompt 10 supported templates. The Attack Control Center includes a read-only Tool Catalog / Tool Readiness panel; it contains no run buttons.


## Prompt 12 normalization update

V2 artifact outputs now flow through `backend/app/normalization/` where supported Nmap, Nuclei, NetExec SMB, BloodHound ZIP, LDAP, Kerberos, and ADCS artifacts are converted into common parsed tables. This remains parsing-only: no extra tool launch, no new RQ job creation, and no subprocess is introduced by normalization.

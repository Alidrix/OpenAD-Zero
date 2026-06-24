import os
from pathlib import Path
from app.jobs.command_policy import CommandPolicyError
BLOCKED={'-headless','-code','-fuzz','-dast','-interactsh','-interactions-cache-size','-interactions-eviction','-interactions-poll-duration','-interactions-cooldown-period','-iserver','-iserver-url','-burp','-proxy','-h','-header','-cookie','-var','-v','-auth','-sfr','-system-resolvers'}
def validate_nuclei_command(command:list[str], targets_file:Path|None=None, output_file:Path|None=None, evidence_dir:Path|None=None)->None:
    if not command or os.path.basename(command[0])!='nuclei': raise CommandPolicyError('Nuclei runner only allows nuclei')
    low=[c.lower() for c in command]
    for c in low:
        if c in BLOCKED: raise CommandPolicyError(f'Blocked Nuclei option: {c}')
    if '-list' not in low or '-jsonl' not in low or '-o' not in low: raise CommandPolicyError('Nuclei command must use -list, -jsonl and -o')
    if targets_file and str(targets_file) not in command: raise CommandPolicyError('targets_file must be backend generated')
    if output_file and str(output_file) not in command: raise CommandPolicyError('output_file must be backend generated')
    if evidence_dir and output_file and not output_file.resolve().is_relative_to(evidence_dir.resolve()): raise CommandPolicyError('output must stay in evidence')

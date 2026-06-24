from sqlalchemy.orm import Session
from app.db.models import Host, Finding, NextAction, SMBFact
from app.integrations.nuclei.targets import build_web_targets_for_mission
WINDOWS_PORTS={445,389,88,3389,5985,5986}
def plan_for_mission(db: Session, mission_id: str) -> tuple[list[Finding], list[NextAction]]:
    findings=[]; actions=[]; smb=False; bh=False; web=False
    for host in db.query(Host).filter_by(mission_id=mission_id).all():
        ports={s.port for s in host.services}; names={s.name.lower() for s in host.services}
        dc=(88 in ports or 'kerberos' in names or 389 in ports or 'ldap' in names or (53 in ports and (88 in ports or 389 in ports)) or (445 in ports and (88 in ports or 389 in ports)))
        if dc:
            host.is_domain_controller_candidate=True; bh=True
            f=Finding(mission_id=mission_id, host_id=host.id, title='Domain Controller candidate detected', severity='info', description=f'{host.ip} exposes directory services consistent with a DC candidate.', source='planner', confidence='medium'); db.add(f); findings.append(f)
        if 445 in ports or any('smb' in n or 'microsoft-ds' in n for n in names): smb=True
        if build_web_targets_for_mission(db, mission_id): web=True
        if 3389 in ports or 'ms-wbt-server' in names:
            f=Finding(mission_id=mission_id, host_id=host.id, title='RDP exposed on internal host', severity='medium', description=f'{host.ip} exposes RDP.', source='planner', confidence='medium'); db.add(f); findings.append(f)
        if 5985 in ports or 5986 in ports or 'wsman' in names:
            f=Finding(mission_id=mission_id, host_id=host.id, title='WinRM exposed on internal host', severity='medium', description=f'{host.ip} exposes WinRM.', source='planner', confidence='medium'); db.add(f); findings.append(f)
    if bh and not db.query(NextAction).filter_by(mission_id=mission_id, command_template_id='bloodhound_prepare_collection').first():
        a=NextAction(mission_id=mission_id,title='Préparer la collecte BloodHound / SharpHound',description='Un environnement Active Directory probable a été détecté. Une collecte BloodHound permettra d’analyser les relations AD, les comptes, les machines, les groupes et les chemins potentiels vers les privilèges élevés.',reason='Un candidat contrôleur de domaine a été détecté.',risk_level=3,requires_approval=True,command_template_id='bloodhound_prepare_collection'); db.add(a); actions.append(a)
    if web and not db.query(NextAction).filter_by(mission_id=mission_id, command_template_id='nuclei_web_exposure_scan').first():
        a=NextAction(mission_id=mission_id,title='Scanner les expositions web avec Nuclei',description='Des services HTTP/HTTPS ont été détectés. Lancer Nuclei en mode safe pour identifier panels, misconfigurations et expositions connues.',reason='Services HTTP/HTTPS détectés par Nmap.',risk_level=2,requires_approval=True,status='proposed',command_template_id='nuclei_web_exposure_scan'); db.add(a); actions.append(a)
    if smb:
        
        for title, desc, tid in [('Énumération SMB contrôlée avec NetExec','Fingerprint SMB/Windows safe via NetExec côté backend.','netexec_smb_fingerprint'),('Vérifier les hôtes sans SMB signing requis','Générer une liste défensive des hôtes où SMB signing n’est pas requis.','netexec_smb_signing_check'),('Tester null session SMB','Tester uniquement si une session anonyme SMB est possible.','netexec_smb_null_session_check')]:
            a=NextAction(mission_id=mission_id,title=title,description=desc,reason='SMB a été détecté sur un ou plusieurs hôtes par Nmap.',risk_level=2,requires_approval=True,command_template_id=tid); db.add(a); actions.append(a)
    db.commit(); return findings, actions

def plan_after_netexec(db: Session, mission_id: str, facts: list[dict], shares: list[dict], action_type: str) -> tuple[list[Finding], list[NextAction]]:
    findings=[]; actions=[]
    if action_type == 'netexec_smb_fingerprint' and any(f.get('domain') or (f.get('hostname') or '').upper().startswith('DC') for f in facts) and not db.query(NextAction).filter_by(mission_id=mission_id, command_template_id='bloodhound_prepare_collection').first():
        a=NextAction(mission_id=mission_id,title='Préparer la collecte BloodHound / SharpHound',description='Action préparée uniquement; exécution automatique désactivée en V2.',reason='NetExec a détecté un domaine ou un contrôleur de domaine probable.',risk_level=3,requires_approval=True,command_template_id='bloodhound_prepare_collection'); db.add(a); actions.append(a)
    if action_type == 'netexec_smb_null_session_check' and any(f.get('null_session_possible') for f in facts):
        a=NextAction(mission_id=mission_id,title='Lister les partages accessibles anonymement',description='Lister uniquement les partages visibles anonymement, sans téléchargement ni spidering.',reason='Une null session SMB semble possible.',risk_level=2,requires_approval=True,command_template_id='netexec_smb_null_session_shares'); db.add(a); actions.append(a)
    if action_type == 'netexec_smb_signing_check':
        for fct in facts:
            if fct.get('smb_signing_required') is False:
                host=db.query(Host).filter_by(mission_id=mission_id, ip=fct.get('ip')).first()
                f=Finding(mission_id=mission_id, host_id=host.id if host else None, title='SMB signing not required', severity='high', description=f"{fct.get('ip')} does not require SMB signing. Document risk only; relay attacks are not executed by V2.", source='netexec', confidence='0.9'); db.add(f); findings.append(f)
    db.commit(); return findings, actions

def plan_after_nuclei(db: Session, mission_id: str, findings: list[Finding]) -> tuple[list[Finding], list[NextAction]]:
    actions=[]
    severities={f.severity for f in findings}
    if severities & {'high','critical'} and not db.query(NextAction).filter_by(mission_id=mission_id,title='Prioriser la validation manuelle du finding web critique').first():
        a=NextAction(mission_id=mission_id,title='Prioriser la validation manuelle du finding web critique',description='Valider manuellement le finding web critique ou haut avant toute décision.',reason='Nuclei a remonté un finding high/critical.',risk_level=3,requires_approval=True,status='proposed',command_template_id=None); db.add(a); actions.append(a)
    if 'medium' in severities and not db.query(NextAction).filter_by(mission_id=mission_id,title='Ajouter les findings web au rapport').first():
        a=NextAction(mission_id=mission_id,title='Ajouter les findings web au rapport',description='Documenter les findings web Nuclei dans le rapport.',reason='Nuclei a remonté un finding medium.',risk_level=1,requires_approval=False,status='proposed',command_template_id=None); db.add(a); actions.append(a)
    db.commit(); return [], actions


def plan_after_bloodhound_upload(db: Session, mission_id: str, zip_valid: bool) -> list[NextAction]:
    actions=[]
    if zip_valid and not db.query(NextAction).filter_by(mission_id=mission_id, command_template_id='bloodhound_analyze_imported_data').first():
        a=NextAction(mission_id=mission_id,title='Analyser les données BloodHound importées',description='Un ZIP SharpHound valide a été importé. Les données peuvent être utilisées pour préparer l’analyse des relations et des chemins AD.',reason='ZIP SharpHound valide importé.',risk_level=1,requires_approval=False,status='proposed',command_template_id='bloodhound_analyze_imported_data')
        db.add(a); actions.append(a); db.commit()
    return actions

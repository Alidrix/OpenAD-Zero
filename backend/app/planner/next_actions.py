from sqlalchemy.orm import Session
from app.db.models import Host, Finding, NextAction
WINDOWS_PORTS={445,389,88,3389,5985,5986}
def plan_for_mission(db: Session, mission_id: str) -> tuple[list[Finding], list[NextAction]]:
    findings=[]; actions=[]; smb=False; bh=False
    for host in db.query(Host).filter_by(mission_id=mission_id).all():
        ports={s.port for s in host.services}; names={s.name.lower() for s in host.services}
        dc=(88 in ports or 'kerberos' in names or 389 in ports or 'ldap' in names or (53 in ports and (88 in ports or 389 in ports)) or (445 in ports and (88 in ports or 389 in ports)))
        if dc:
            host.is_domain_controller_candidate=True; bh=True
            f=Finding(mission_id=mission_id, host_id=host.id, title='Domain Controller candidate detected', severity='info', description=f'{host.ip} exposes directory services consistent with a DC candidate.', source='planner', confidence='medium'); db.add(f); findings.append(f)
        if 445 in ports or any('smb' in n or 'microsoft-ds' in n for n in names): smb=True
        if 3389 in ports or 'ms-wbt-server' in names:
            f=Finding(mission_id=mission_id, host_id=host.id, title='RDP exposed on internal host', severity='medium', description=f'{host.ip} exposes RDP.', source='planner', confidence='medium'); db.add(f); findings.append(f)
        if 5985 in ports or 5986 in ports or 'wsman' in names:
            f=Finding(mission_id=mission_id, host_id=host.id, title='WinRM exposed on internal host', severity='medium', description=f'{host.ip} exposes WinRM.', source='planner', confidence='medium'); db.add(f); findings.append(f)
    if bh:
        a=NextAction(mission_id=mission_id,title='Préparer la collecte BloodHound / SharpHound',description='Afficher une étape préparatoire sans exécution en V1.',reason='Un candidat contrôleur de domaine a été détecté.',risk_level=3,requires_approval=True,command_template_id='bloodhound_collection_prepare'); db.add(a); actions.append(a)
    if smb:
        a=NextAction(mission_id=mission_id,title='Préparer une énumération SMB contrôlée',description='Afficher une action SMB sûre proposée pour une étape ultérieure.',reason='SMB a été détecté sur un ou plusieurs hôtes.',risk_level=2,requires_approval=True,command_template_id='nmap_smb_safe_followup'); db.add(a); actions.append(a)
    db.commit(); return findings, actions

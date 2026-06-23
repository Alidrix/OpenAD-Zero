from sqlalchemy.orm import Session
from app.db.models import Host, Service, Finding, NextAction, SMBFact

def _action_exists(db: Session, mission_id: str, template: str) -> bool:
    return db.query(NextAction).filter_by(mission_id=mission_id, command_template_id=template).first() is not None

def _add_action(db: Session, mission_id: str, title: str, description: str, reason: str, risk: int, template: str) -> NextAction | None:
    if _action_exists(db, mission_id, template):
        return None
    action = NextAction(mission_id=mission_id, title=title, description=description, reason=reason, risk_level=risk, requires_approval=True, command_template_id=template, status='proposed')
    db.add(action); return action

def plan_for_mission(db: Session, mission_id: str) -> tuple[list[Finding], list[NextAction]]:
    findings=[]; actions=[]; smb=False; bh=False
    for host in db.query(Host).filter_by(mission_id=mission_id).all():
        ports={s.port for s in host.services}; names={s.name.lower() for s in host.services}
        dc=(88 in ports or 'kerberos' in names or 389 in ports or 'ldap' in names or (53 in ports and (88 in ports or 389 in ports)) or (445 in ports and (88 in ports or 389 in ports)))
        if dc:
            host.is_domain_controller_candidate=True; bh=True
            if not db.query(Finding).filter_by(mission_id=mission_id, host_id=host.id, title='Domain Controller candidate detected').first():
                f=Finding(mission_id=mission_id, host_id=host.id, title='Domain Controller candidate detected', severity='info', description=f'{host.ip} exposes directory services consistent with a DC candidate.', source='planner', confidence='medium'); db.add(f); findings.append(f)
        if 445 in ports or any('smb' in n or 'microsoft-ds' in n for n in names): smb=True
        if 3389 in ports or 'ms-wbt-server' in names:
            if not db.query(Finding).filter_by(mission_id=mission_id, host_id=host.id, title='RDP exposed on internal host').first():
                f=Finding(mission_id=mission_id, host_id=host.id, title='RDP exposed on internal host', severity='medium', description=f'{host.ip} exposes RDP.', source='planner', confidence='medium'); db.add(f); findings.append(f)
        if 5985 in ports or 5986 in ports or 'wsman' in names:
            if not db.query(Finding).filter_by(mission_id=mission_id, host_id=host.id, title='WinRM exposed on internal host').first():
                f=Finding(mission_id=mission_id, host_id=host.id, title='WinRM exposed on internal host', severity='medium', description=f'{host.ip} exposes WinRM.', source='planner', confidence='medium'); db.add(f); findings.append(f)
    if bh:
        a=_add_action(db, mission_id,'Préparer la collecte BloodHound / SharpHound','Afficher une étape préparatoire sans exécution en V2.','Un candidat contrôleur de domaine a été détecté.',3,'bloodhound_prepare_collection')
        if a: actions.append(a)
    if smb:
        for args in [
            ('Préparer une énumération SMB contrôlée','Afficher une action SMB sûre proposée pour une étape ultérieure.','SMB a été détecté sur un ou plusieurs hôtes.',2,'nmap_smb_safe_followup'),
            ('Énumération SMB contrôlée avec NetExec','Fingerprint Windows/SMB contrôlé via NetExec, après validation humaine.','SMB/445 a été détecté par Nmap.',2,'netexec_smb_fingerprint'),
            ('Vérifier les hôtes sans SMB signing requis','Générer seulement une liste défensive des hôtes où SMB signing n’est pas requis.','SMB/445 a été détecté par Nmap.',2,'netexec_smb_signing_check'),
            ('Tester null session SMB','Tester uniquement si une null session SMB est possible, sans énumération de fichiers.','SMB/445 a été détecté par Nmap.',2,'netexec_smb_null_session_check')]:
            a=_add_action(db, mission_id,*args)
            if a: actions.append(a)
    db.commit(); return findings, actions

def plan_after_netexec(db: Session, mission_id: str) -> tuple[list[Finding], list[NextAction]]:
    findings=[]; actions=[]
    for fact in db.query(SMBFact).filter_by(mission_id=mission_id).all():
        host=db.query(Host).filter_by(mission_id=mission_id, ip=fact.ip).first()
        if fact.domain or (fact.hostname and fact.hostname.upper().startswith('DC')):
            a=_add_action(db, mission_id,'Préparer la collecte BloodHound / SharpHound','Action préparée seulement; BloodHound/SharpHound réel reste désactivé en V2.','NetExec a détecté un domaine ou un hôte DC probable.',3,'bloodhound_prepare_collection')
            if a: actions.append(a)
        if fact.smb_signing_required is False:
            exists=db.query(Finding).filter_by(mission_id=mission_id, host_id=host.id if host else None, title='SMB signing not required').first()
            if not exists:
                f=Finding(mission_id=mission_id, host_id=host.id if host else None, title='SMB signing not required', severity='high', description=f'{fact.ip} does not require SMB signing. Document the relay risk; no relay attack is executed by OpenAD Zero V2.', source='netexec', confidence='0.9'); db.add(f); findings.append(f)
        if fact.null_session_possible:
            a=_add_action(db, mission_id,'Lister les partages accessibles anonymement','Lister uniquement les noms de partages et droits visibles anonymement, sans spider ni téléchargement.','Une null session SMB semble possible.',2,'netexec_smb_null_session_shares')
            if a: actions.append(a)
    db.commit(); return findings, actions

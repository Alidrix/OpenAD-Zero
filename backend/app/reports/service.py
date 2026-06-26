import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.paths import mission_evidence_dir
from app.db.models import Report
from app.reports.collector import collect_report_data
from app.reports.markdown import render_markdown_report
from app.operations.progress import calculate_progress_score
from app.reports.html import render_html_report

DEFAULT_SECTIONS=['executive_summary','mission_scope','methodology','tool_summary','hosts_services','smb_windows','web_exposure','bloodhound','findings','evidence','next_steps','technical_appendix']

def generate_report(db: Session, mission_id: str, include_sections: list[str] | None = None) -> Report:
    data=collect_report_data(db, mission_id); data['progress']=calculate_progress_score(db, mission_id)
    sections=include_sections or DEFAULT_SECTIONS
    report=Report(mission_id=mission_id,status='generating',title=f"OpenAD Zero Report - {data['mission']['name']}",sections_json={'sections':sections})
    db.add(report); db.commit(); db.refresh(report)
    base=mission_evidence_dir(mission_id, 'reports', report.id)
    md=render_markdown_report(data); html=render_html_report(md, data)
    md_path=base/'report.md'; html_path=base/'report.html'; meta_path=base/'report_metadata.json'
    md_path.write_text(md, encoding='utf-8'); html_path.write_text(html, encoding='utf-8')
    metadata={'mission_id':mission_id,'report_id':report.id,'generated_at':report.generated_at.isoformat(),'sections':sections,'counts':{'hosts':len(data.get('hosts',[])),'findings':len(data.get('findings',[])),'evidence':len(data.get('evidence',[]))}}
    meta_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    report.status='generated'; report.markdown_path=str(md_path); report.html_path=str(html_path); report.metadata_path=str(meta_path); report.sections_json={'sections':sections,'counts':metadata['counts']}
    db.add(report); db.commit(); db.refresh(report); return report

def get_latest_report(db: Session, mission_id: str) -> Report | None:
    return db.query(Report).filter_by(mission_id=mission_id).order_by(Report.generated_at.desc()).first()

def get_report_file(report: Report, format: str) -> Path:
    path = report.markdown_path if format in ('markdown','md') else report.html_path if format=='html' else None
    if not path: raise ValueError('Unsupported report format')
    p=Path(path)
    if not p.exists(): raise FileNotFoundError(str(p))
    return p

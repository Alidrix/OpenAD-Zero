from sqlalchemy import inspect
from app.db.models import ParseDiagnostic, ParsedAsset, ParsedService, ParsedSignal, Scan

def test_parsed_tables_and_relations(db_session):
    tables=set(inspect(db_session.bind).get_table_names())
    assert {'parsed_assets','parsed_services','parsed_findings','parsed_signals','parse_diagnostics'} <= tables
    scan=Scan(name='s',scan_type='manual',tool_name='manual'); db_session.add(scan); db_session.flush()
    asset=ParsedAsset(scan_id=scan.id,source_type='test',ip_address='10.0.0.1',confidence=1.0)
    db_session.add(asset); db_session.flush()
    service=ParsedService(scan_id=scan.id,asset_id=asset.id,source_type='test',ip_address='10.0.0.1',port=445,protocol='tcp',state='open',confidence=1.0)
    signal=ParsedSignal(scan_id=scan.id,asset_id=asset.id,service_id=service.id,source_type='test',signal='smb_open',value='true',confidence=1.0)
    diag=ParseDiagnostic(scan_id=scan.id,source_type='test',level='warning',message='ok')
    db_session.add_all([service, signal, diag]); db_session.commit()
    assert scan.parsed_assets[0].ip_address == '10.0.0.1'

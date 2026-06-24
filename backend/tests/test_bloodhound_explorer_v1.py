import asyncio
import pytest
from app.db.models import Mission, BloodHoundCollection, Finding
from app.integrations.bloodhound.query_catalog import QueryCatalog, QueryCatalogError
from app.integrations.bloodhound.mapper import map_object, map_relation
from app.integrations.bloodhound.explorer import BloodHoundExplorer

class FakeClient:
    def __init__(self, result=None, enabled=True, reachable=True): self.result=result or {'rows':[]}; self.enabled=enabled; self.reachable=reachable; self.queries=[]
    def status(self): return {'enabled':self.enabled}
    async def ping(self): return self.reachable
    async def run_cypher_query(self, query, include_properties=True): self.queries.append(query); return self.result

def mission(db):
    m=Mission(id='mx',name='m',scenario='s',mode='safe',raw_scope='10.0.0.1',validated_targets=[]); db.add(m); db.commit(); return m

def test_query_catalog_loads_and_validates_limit():
    c=QueryCatalog(); assert c.get('search_objects')['read_only'] is True
    _, params, cypher=c.render('search_objects', {'search':'admin','limit':999})
    assert params['limit']==50 and 'admin' in cypher
    with pytest.raises(QueryCatalogError): c.get('raw cypher from frontend')
    with pytest.raises(QueryCatalogError): c.render('object_detail', {})

def test_mapper_objects_and_edges():
    u=map_object({'labels':['User'],'properties':{'objectid':'S-1','name':'USER@LAB','enabled':True}})
    c=map_object({'labels':['Computer'],'properties':{'objectid':'C-1','name':'PC@LAB'}})
    g=map_object({'labels':['Group'],'properties':{'objectid':'G-1','name':'DOMAIN ADMINS@LAB','highvalue':True}})
    assert (u['type'],c['type'],g['high_value'])==('User','Computer',True)
    assert map_relation({'edge_type':'GenericAll'})['risk']=='critical'
    assert map_relation({'edge_type':'GenericWrite'})['risk']=='high'
    assert map_relation({'edge_type':'CanRDP'})['risk']=='medium'
    assert map_relation({'edge_type':'Other'})['risk']=='info'

def test_explorer_search_detail_relations_permissions_path(db_session, tmp_path, monkeypatch):
    async def run():
        monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path)); mission(db_session)
        row={'n':{'labels':['User'],'properties':{'objectid':'S-1','name':'USER@LAB','enabled':True}}}
        e=BloodHoundExplorer(db_session, FakeClient({'rows':[row]}))
        assert (await e.search_objects('mx','user'))[0]['type']=='User'
        assert (await e.object_detail('mx','S-1'))['name']=='USER@LAB'
        relrow={'edge_type':'GenericAll','source':'USER@LAB','target':'DA@LAB','target_type':'Group'}
        e.client.result={'rows':[relrow]}
        assert (await e.relations('mx','S-1'))[0]['risk']=='critical'
        assert (await e.permissions('mx','S-1'))[0]['edge_type']=='GenericAll'
        e.client.result={'rows':[{'nodes':[{'object_id':'S-1','name':'USER@LAB'},{'object_id':'G-1','name':'DOMAIN ADMINS@LAB'}],'edges':[relrow]}]}
        p=await e.pathfinding('mx','S-1')
        assert p['path_found'] and p['finding_id']
        await e.pathfinding('mx','S-1')
        assert db_session.query(Finding).filter_by(mission_id='mx',source='bloodhound').count()==1
    asyncio.run(run())

def test_explorer_status_disabled_unreachable(db_session):
    async def run():
        mission(db_session)
        st=await BloodHoundExplorer(db_session, FakeClient(enabled=False,reachable=False)).status('mx')
        assert not st['enabled'] and not st['reachable'] and not st['ingested']
        db_session.add(BloodHoundCollection(mission_id='mx',ingestion_status='ingested',ingestion_enabled=True)); db_session.commit()
        st=await BloodHoundExplorer(db_session, FakeClient(enabled=True,reachable=False)).status('mx')
        assert st['ingested'] and not st['reachable']
    asyncio.run(run())

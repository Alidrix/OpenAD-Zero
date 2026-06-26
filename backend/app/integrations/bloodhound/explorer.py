import json
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.paths import EvidencePathError, mission_evidence_dir
from app.db.models import BloodHoundCollection, Finding
from app.events.publisher import publish
from app.events.schemas import MissionEvent

from .client import BloodHoundClient
from .mapper import IMPORTANT_EDGE_TYPES, map_object, map_relation
from .query_catalog import QueryCatalog

log = logging.getLogger(__name__)


class BloodHoundExplorer:
    def __init__(self, db: Session, client=None, catalog=None):
        self.db = db
        self.client = client or BloodHoundClient()
        self.catalog = catalog or QueryCatalog()

    def _ingested(self, mission_id):
        return (
            self.db.query(BloodHoundCollection)
            .filter_by(mission_id=mission_id, ingestion_status='ingested')
            .order_by(BloodHoundCollection.created_at.desc())
            .first()
        )

    async def status(self, mission_id):
        enabled = self.client.status().get('enabled', False)
        reachable = await self.client.ping() if enabled else False
        c = self._ingested(mission_id)
        return {
            'enabled': enabled,
            'reachable': reachable,
            'ingested': bool(c),
            'last_collection_id': c.id if c else None,
            'message': 'BloodHound Explorer ready'
            if enabled and reachable and c
            else 'BloodHound Explorer requires BloodHound CE configured, reachable, and ingested data.',
        }

    def _rows(self, res):
        return res.get('data') or res.get('rows') or res.get('results') or ([] if not isinstance(res, list) else res)

    def _evidence(self, mission_id, query_id, params, result, summary):
        try:
            base = mission_evidence_dir(mission_id, 'bloodhound', 'queries', str(uuid.uuid4()))
        except EvidencePathError:
            log.warning('failed to create BloodHound query evidence directory', exc_info=True)
            return None
        (base / 'query_id.txt').write_text(query_id + '\n')
        (base / 'parameters.json').write_text(json.dumps(params, indent=2, default=str))
        (base / 'result.json').write_text(json.dumps(result, indent=2, default=str))
        (base / 'summary.json').write_text(json.dumps(summary, indent=2, default=str))
        (base / 'README.txt').write_text(
            'OpenAD Zero BloodHound Explorer V1 read-only predefined query evidence. No free-form Cypher or exploitation was executed.\n'
        )
        return str(base)

    async def _run(self, mission_id, qid, params):
        q, clean, cypher = self.catalog.render(qid, params)
        res = await self.client.run_cypher_query(cypher)
        return clean, res

    async def search_objects(self, mission_id, search, limit=20, object_types=None):
        clean, res = await self._run(
            mission_id, 'search_objects', {'search': search, 'limit': limit, 'object_types': object_types or []}
        )
        out = [map_object(r.get('n', r) if isinstance(r, dict) else r) for r in self._rows(res)]
        if object_types:
            out = [o for o in out if o['type'] in object_types]
        self._evidence(mission_id, 'search_objects', clean, res, {'count': len(out)})
        await publish(
            MissionEvent(
                type='bloodhound.object.search.completed',
                mission_id=mission_id,
                payload={'query': search, 'count': len(out)},
            )
        )
        return out

    async def object_detail(self, mission_id, object_id):
        clean, res = await self._run(mission_id, 'object_detail', {'object_id': object_id})
        rows = self._rows(res)
        obj = map_object(
            (rows[0].get('n', rows[0]) if isinstance(rows[0], dict) else rows[0]) if rows else {'object_id': object_id}
        )
        self._evidence(mission_id, 'object_detail', clean, res, {'object_id': object_id})
        await publish(
            MissionEvent(
                type='bloodhound.object.loaded',
                mission_id=mission_id,
                payload={'object_id': obj['object_id'], 'name': obj['name'], 'type': obj['type']},
            )
        )
        return obj

    async def relations(self, mission_id, object_id, direction='outbound', limit=100):
        qid = 'inbound_relations' if direction == 'inbound' else 'outbound_relations'
        clean, res = await self._run(mission_id, qid, {'object_id': object_id, 'limit': limit})
        rel = [map_relation(r) for r in self._rows(res)]
        self._evidence(mission_id, qid, clean, res, {'count': len(rel)})
        return rel

    async def permissions(self, mission_id, object_id, limit=100):
        clean, res = await self._run(mission_id, 'important_permissions', {'object_id': object_id, 'limit': limit})
        rel = [map_relation(r) for r in self._rows(res)]
        rel = [r for r in rel if r['edge_type'] in IMPORTANT_EDGE_TYPES]
        self._evidence(mission_id, 'important_permissions', clean, res, {'count': len(rel)})
        return rel

    async def pathfinding(self, mission_id, source_object_id, target='Domain Admins', max_depth=8):
        clean, res = await self._run(
            mission_id,
            'shortest_path_domain_admins',
            {'source_object_id': source_object_id, 'target': target, 'max_depth': max_depth},
        )
        rows = self._rows(res)
        graph = rows[0] if rows else {}
        nodes = graph.get('nodes', [])
        edges = [map_relation(e) for e in graph.get('edges', graph.get('relationships', []))]
        found = bool(nodes or edges or graph.get('p'))
        out = {
            'path_found': found,
            'source': nodes[0] if nodes else {'object_id': source_object_id},
            'target': nodes[-1] if nodes else {'name': target},
            'nodes': nodes,
            'edges': edges,
            'length': len(edges),
            'risk': 'critical' if found else 'info',
        }
        finding = None
        if found:
            finding = self._finding(mission_id, out, res)
            out['finding_id'] = finding.id
        self._path_evidence(mission_id, out, finding)
        await publish(
            MissionEvent(
                type='bloodhound.pathfinding.completed',
                mission_id=mission_id,
                payload={'path_found': found, 'length': out['length'], 'risk': out['risk']},
            )
        )
        return out

    def _finding(self, mission_id, path, res):
        sig = {
            'source': path['source'],
            'target': path['target'],
            'length': path['length'],
            'edge_types': [e['edge_type'] for e in path['edges']],
        }
        existing = (
            self.db.query(Finding)
            .filter_by(mission_id=mission_id, source='bloodhound', title='Potential path to Domain Admins detected')
            .all()
        )
        for f in existing:
            if (f.raw_json or {}).get('signature') == sig:
                return f
        f = Finding(
            mission_id=mission_id,
            title='Potential path to Domain Admins detected',
            severity='critical',
            source='bloodhound',
            confidence='0.9',
            description=f'A read-only BloodHound pathfinding query identified a potential path from {path["source"]} to Domain Admins. This is an analysis finding only; no exploitation was performed.',
            raw_json={
                'signature': sig,
                'path': path,
                'raw_query_result': res,
                'timestamp': datetime.utcnow().isoformat(),
            },
        )
        self.db.add(f)
        self.db.commit()
        self.db.refresh(f)
        return f

    def _path_evidence(self, mission_id, path, finding):
        try:
            base = mission_evidence_dir(mission_id, 'bloodhound', 'pathfinding', str(uuid.uuid4()))
        except EvidencePathError:
            log.warning('failed to create BloodHound pathfinding evidence directory', exc_info=True)
            return
        for name, data in {
            'source': path.get('source'),
            'target': path.get('target'),
            'path': path,
            'graph': {'nodes': path.get('nodes'), 'edges': path.get('edges')},
            'finding': (finding.raw_json if finding else None),
        }.items():
            (base / f'{name}.json').write_text(json.dumps(data, indent=2, default=str))
        (base / 'README.txt').write_text('Read-only pathfinding evidence. No offensive action was executed.\n')

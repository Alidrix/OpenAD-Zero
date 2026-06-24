IMPORTANT_EDGE_TYPES={'GenericAll','GenericWrite','WriteDacl','WriteOwner','AddMember','ForceChangePassword','AllowedToDelegate','CanRDP','CanPSRemote','AdminTo','HasSession','MemberOf','Owns'}
RISK_BY_EDGE={'MemberOf':'info','CanRDP':'medium','CanPSRemote':'medium','AdminTo':'high','HasSession':'high','GenericAll':'critical','GenericWrite':'high','WriteDacl':'critical','WriteOwner':'critical','AddMember':'high','ForceChangePassword':'high','AllowedToDelegate':'critical','Owns':'critical'}
TRAVERSABLE={e:True for e in IMPORTANT_EDGE_TYPES}
OBJECT_TYPES={'User','Computer','Group','Domain','OU','GPO'}

def edge_risk(edge_type:str)->str: return RISK_BY_EDGE.get(edge_type,'info')
def edge_traversable(edge_type:str): return TRAVERSABLE.get(edge_type,'unknown')
def _props(row): return row.get('properties') or row.get('props') or row.get('raw_properties') or row

def map_object(row:dict)->dict:
    p=_props(row); labels=row.get('labels') or row.get('type') or p.get('type') or []
    typ=labels if isinstance(labels,str) else next((x for x in labels if x in OBJECT_TYPES),'Unknown')
    oid=row.get('object_id') or row.get('objectid') or p.get('objectid') or p.get('object_id') or row.get('id') or p.get('id')
    name=row.get('name') or p.get('name') or p.get('displayname') or oid
    domain=row.get('domain') or p.get('domain') or (name.split('@')[-1] if isinstance(name,str) and '@' in name else None)
    return {'object_id':oid,'name':name,'type':typ,'domain':domain,'high_value':bool(p.get('highvalue') or p.get('high_value')),'owned':bool(p.get('owned')),'enabled':p.get('enabled'),'properties':{k:p.get(k) for k in ['enabled','lastlogon','pwdlastset','admincount','hasspn','highvalue','owned','operatingsystem','unconstraineddelegation','member_count'] if k in p},'raw_properties':p}

def map_relation(row:dict)->dict:
    et=row.get('edge_type') or row.get('relationship') or row.get('type') or 'Unknown'
    src=row.get('source') or row.get('source_name') or row.get('start') or {}
    tgt=row.get('target') or row.get('target_name') or row.get('end') or {}
    src_name=src.get('name') if isinstance(src,dict) else src; tgt_name=tgt.get('name') if isinstance(tgt,dict) else tgt
    return {'edge_type':et,'source':src_name,'target':tgt_name,'source_id':row.get('source_id') or (src.get('object_id') if isinstance(src,dict) else None),'target_id':row.get('target_id') or (tgt.get('object_id') if isinstance(tgt,dict) else None),'source_type':row.get('source_type') or (src.get('type') if isinstance(src,dict) else None),'target_type':row.get('target_type') or (tgt.get('type') if isinstance(tgt,dict) else None),'risk':edge_risk(et),'description':row.get('description') or 'Potentially dangerous permission relationship.' if et in IMPORTANT_EDGE_TYPES else 'BloodHound relationship.','traversable':edge_traversable(et),'raw':row}

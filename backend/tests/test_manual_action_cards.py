from app.api.routes_missions import create_manual_action, list_manual_actions, update_manual_action, ManualActionCreate, ManualActionUpdate
from app.db.models import Mission
from fastapi import HTTPException
import pytest


def mission(db):
    m=Mission(id='m-manual',name='m',scenario='s',mode='safe',raw_scope='10.0.0.0/24',validated_targets=['10.0.0.1']); db.add(m); db.commit(); return m


def test_create_list_update_manual_action_card(db_session):
    mission(db_session)
    payload=ManualActionCreate(capability_id='lateral_movement',title='Manual lab validation note',description='Manual validation performed outside OpenAD Zero in an authorized lab environment.',risk_level=5,operator_note='',evidence_reference='')
    card=create_manual_action('m-manual',payload,db_session)
    assert card['capability_id']=='lateral_movement'; assert card['status']=='draft'
    assert len(list_manual_actions('m-manual',db_session)) == 1
    updated=update_manual_action('m-manual',card['id'],ManualActionUpdate(operator_note='Reviewed note',status='documented'),db_session)
    assert updated['operator_note']=='Reviewed note'; assert updated['status']=='documented'


def test_cannot_create_manual_action_unknown_capability(db_session):
    mission(db_session)
    with pytest.raises(HTTPException):
        create_manual_action('m-manual',ManualActionCreate(capability_id='unknown',title='x',description='x',risk_level=5),db_session)


def test_cannot_create_executable_command_through_manual_endpoint(db_session):
    mission(db_session)
    with pytest.raises(HTTPException):
        create_manual_action('m-manual',ManualActionCreate(capability_id='lateral_movement',title='run command',description='powershell command here',risk_level=5),db_session)

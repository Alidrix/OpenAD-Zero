def test_api_contracts(client, demo_mission):
    mission_id=demo_mission.id
    checks=[('/api/health', ['status']),('/api/capabilities', None),('/api/missions', None),(f'/api/missions/{mission_id}', ['id','hosts','findings','evidence_summary']),(f'/api/missions/{mission_id}/evidence', None),(f'/api/missions/{mission_id}/report', ['report']),(f'/api/missions/{mission_id}/phases', None),(f'/api/missions/{mission_id}/timeline', None),(f'/api/missions/{mission_id}/progress', ['score'])]
    for path, fields in checks:
        r=client.get(path)
        assert r.status_code == 200, path
        data=r.json()
        if fields:
            for field in fields: assert field in data


def test_demo_endpoint_disabled_by_default(client):
    r=client.post('/api/demo/seed')
    assert r.status_code == 404

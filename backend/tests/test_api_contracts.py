def test_api_contracts(client, demo_mission):
    mid=demo_mission.id
    checks=[('/api/health','status'),('/api/health/db','status'),('/api/health/redis','status'),('/api/health/tools','nmap'),('/api/health/worker','queues'),('/api/capabilities',None),('/api/missions',None),(f'/api/missions/{mid}','id'),(f'/api/missions/{mid}/evidence',None),(f'/api/missions/{mid}/report','report'),(f'/api/missions/{mid}/phases',None),(f'/api/missions/{mid}/timeline',None),(f'/api/missions/{mid}/progress','score')]
    for url,key in checks:
        r=client.get(url)
        assert r.status_code == 200, url
        data=r.json()
        assert data is not None
        if key: assert key in data

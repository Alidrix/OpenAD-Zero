from app.api import routes_health


def test_api_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
    assert r.json()['service'] == 'openadzero-api'


def test_db_health(client):
    r = client.get('/api/health/db')
    assert r.status_code == 200
    assert 'status' in r.json()


def test_redis_health(client):
    r = client.get('/api/health/redis')
    assert r.status_code == 200
    assert 'status' in r.json()


def test_tools_health(client):
    r = client.get('/api/health/tools')
    assert r.status_code == 200
    data = r.json()
    assert {'nmap', 'netexec', 'nuclei'} <= set(data)


def test_worker_health_without_real_redis(client, monkeypatch):
    class FakeRedis:
        def ping(self):
            return True

        def llen(self, name):
            return 0

    monkeypatch.setattr(routes_health, 'get_redis_connection', lambda: FakeRedis())
    r = client.get('/api/health/worker')
    assert r.status_code == 200
    assert r.json()['redis_available'] is True
    assert 'openadzero-default' in r.json()['queues']

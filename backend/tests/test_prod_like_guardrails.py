def test_auth_status_returns_no_secret(client):
    response = client.get('/api/auth/status')
    assert response.status_code == 200
    text = response.text.lower()
    assert 'api_token' not in response.json()
    assert 'secret' not in text
    assert 'token_configured' in response.json()

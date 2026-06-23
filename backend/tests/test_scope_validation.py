import pytest
from app.core.scope import validate_scope, ScopeValidationError
def test_single_ip_valid(): assert validate_scope('192.168.1.10').targets==['192.168.1.10']
def test_cidr_valid(): assert validate_scope('192.168.1.0/24').targets==['192.168.1.0/24']
def test_mixed_valid(): assert validate_scope('192.168.1.10, 10.0.0.0/24\n192.168.1.20').targets==['192.168.1.10','10.0.0.0/24','192.168.1.20']
def test_duplicates_removed(): assert validate_scope('192.168.1.10 192.168.1.10').targets==['192.168.1.10']
@pytest.mark.parametrize('raw', ['bad','0.0.0.0/0','192.168.0.0/16','8.8.8.8'])
def test_invalid_refused(raw):
    with pytest.raises(ScopeValidationError): validate_scope(raw)

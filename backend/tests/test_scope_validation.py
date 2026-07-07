import pytest

from app.core.scope import ScopeValidationError, validate_scope


def test_single_private_ip_valid():
    assert validate_scope('192.168.1.10').targets == ['192.168.1.10']


@pytest.mark.parametrize(
    'raw,expected',
    [
        ('192.168.1.0/24', ['192.168.1.0/24']),
        ('192.168.0.0/16', ['192.168.0.0/16']),
        ('10.0.0.0/16', ['10.0.0.0/16']),
        ('172.16.0.0/16', ['172.16.0.0/16']),
    ],
)
def test_private_cidrs_up_to_16_valid(raw, expected):
    assert validate_scope(raw).targets == expected


def test_mixed_valid_and_duplicates_removed():
    assert validate_scope('192.168.1.10, 10.0.0.0/24\n192.168.1.10').targets == ['192.168.1.10', '10.0.0.0/24']


@pytest.mark.parametrize('raw', ['bad', '0.0.0.0/0', '::/0', '8.8.8.8', '2001:db8::/32', '10.0.0.0/15'])
def test_invalid_refused(raw):
    with pytest.raises(ScopeValidationError):
        validate_scope(raw)

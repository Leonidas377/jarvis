import pytest
from server.services.extraction.security import validate_url_safe, SecurityException

def test_valid_public_https_url():
    url = "https://www.nature.com/articles/d41586-024-00001-w"
    validated = validate_url_safe(url)
    assert validated == url

def test_valid_public_http_url():
    url = "http://example.com/test-article"
    validated = validate_url_safe(url)
    assert validated == url

def test_blocked_unsupported_schemes():
    forbidden_schemes = [
        "file:///etc/passwd",
        "file://C:/Windows/win.ini",
        "javascript:alert(1)",
        "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        "ftp://ftp.is.co.za/rfc/rfc1808.txt",
        "gopher://gopher.floodgap.com/"
    ]
    for bad_url in forbidden_schemes:
        with pytest.raises(SecurityException) as exc_info:
            validate_url_safe(bad_url)
        assert "Unsupported or unsafe URL scheme" in str(exc_info.value) or "valid domain" in str(exc_info.value)

def test_blocked_localhost_and_loopback():
    loopbacks = [
        "http://localhost:8000/api/secret",
        "http://127.0.0.1:8000/admin",
        "http://127.0.1.1/internal",
        "http://[::1]:8080/metrics"
    ]
    for bad_url in loopbacks:
        with pytest.raises(SecurityException) as exc_info:
            validate_url_safe(bad_url)
        err_msg = str(exc_info.value)
        assert ("loopback/metadata host" in err_msg) or ("private or restricted network address" in err_msg)

def test_blocked_private_network_ips():
    private_ips = [
        "http://10.0.0.1/admin",
        "http://172.16.0.5/internal",
        "http://172.31.255.254/router",
        "http://192.168.1.1/setup",
        "http://192.168.0.100:3000/keys",
        "http://169.254.169.254/latest/meta-data/"
    ]
    for bad_url in private_ips:
        with pytest.raises(SecurityException) as exc_info:
            validate_url_safe(bad_url)
        err_msg = str(exc_info.value)
        assert ("private or restricted network address" in err_msg) or ("loopback/metadata host" in err_msg)

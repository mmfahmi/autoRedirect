import pytest
from app import app as flask_app


@pytest.fixture
def client():
    with flask_app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200


def test_about(client):
    response = client.get("/about")
    assert response.status_code == 200


def test_vpn_detected(client, monkeypatch):
    def mock_is_likely_vpn(ip_address):
        return True
    monkeypatch.setattr("app.is_likely_vpn", mock_is_likely_vpn)
    response = client.get("/")
    assert response.status_code == 302  # Redirect
    assert response.location.endswith("/vpn-detected")
    
def test_no_vpn_detected(client, monkeypatch):
    def mock_is_likely_vpn(ip_address):
        return False
    monkeypatch.setattr("app.is_likely_vpn", mock_is_likely_vpn)
    response = client.get("/")
    assert response.status_code == 200  # Normal content
    assert b"Welcome!" in response.data  # Updated to match actual content in normal_content.html
    
def test_vpn_detected_page(client):
    response = client.get("/vpn-detected")
    assert response.status_code == 200
    assert b"VPN Detected" in response.data  # Updated to match actual content in vpn_detected.html
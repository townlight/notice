from fastapi.testclient import TestClient

import townlight_notice
from townlight_notice.main import app


client = TestClient(app)


def test_package_version_is_012() -> None:
    assert townlight_notice.__version__ == "0.3.0"


def test_root_endpoint_states_runtime_boundary() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Townlight Notice"
    assert data["status"] == "notice compliance foundation"
    assert "TownlightCore-backed deadline plans" in data["message"]
    assert "archive/handoff packets" in data["message"]
    assert "database-backed registry/deadline/publication-proof workpapers" in data["message"]
    assert "official publication" in data["message"]
    assert "Post-v0.3.0 roadmap" in data["next_step"]


def test_health_endpoint_reports_versions() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "townlight_notice"
    assert data["version"] == "0.3.0"
    assert data["townlight_core_version"] == "1.3.0.dev2"

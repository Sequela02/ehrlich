import pytest
from fastapi.testclient import TestClient

from ehrlich.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestDepict:
    def test_returns_svg(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/depict", params={"smiles": "CCO"})
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers["content-type"]
        assert "<svg" in resp.text

    def test_custom_dimensions(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/depict", params={"smiles": "CCO", "w": 100, "h": 80})
        assert resp.status_code == 200
        assert "<svg" in resp.text

    def test_invalid_smiles_returns_error_svg(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/depict", params={"smiles": "invalid!!!"})
        assert resp.status_code == 200
        assert "<svg" in resp.text
        assert "Invalid SMILES" in resp.text

    def test_cache_header(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/depict", params={"smiles": "CCO"})
        assert "max-age=86400" in resp.headers.get("cache-control", "")


class TestConformer:
    def test_returns_molblock(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/conformer", params={"smiles": "CCO"})
        assert resp.status_code == 200
        data = resp.json()
        assert "mol_block" in data
        assert "energy" in data
        assert "num_atoms" in data
        assert data["num_atoms"] > 0

    def test_invalid_smiles_400(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/conformer", params={"smiles": "invalid!!!"})
        assert resp.status_code == 400


class TestDescriptors:
    def test_returns_data(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/descriptors", params={"smiles": "CCO"})
        assert resp.status_code == 200
        data = resp.json()
        assert "molecular_weight" in data
        assert "logp" in data
        assert "tpsa" in data

    def test_has_lipinski(self, client: TestClient) -> None:
        resp = client.get("/api/v1/molecule/descriptors", params={"smiles": "CCO"})
        data = resp.json()
        assert "passes_lipinski" in data
        assert data["passes_lipinski"] is True


class TestTargets:
    def test_returns_five(self, client: TestClient) -> None:
        resp = client.get("/api/v1/targets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5

    def test_has_required_fields(self, client: TestClient) -> None:
        resp = client.get("/api/v1/targets")
        data = resp.json()
        for target in data:
            assert "pdb_id" in target
            assert "name" in target
            assert "organism" in target

import pytest
from fastapi.testclient import TestClient

from ehrlich.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestMethodology:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/methodology")
        assert resp.status_code == 200

    def test_has_all_top_level_keys(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        assert set(data.keys()) == {"phases", "domains", "tools", "data_sources", "models"}

    def test_phases_count(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        assert len(data["phases"]) == 6

    def test_phase_fields(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        phase = data["phases"][0]
        assert phase["number"] == 1
        assert phase["name"] == "Classification & PICO"
        assert phase["model"] == "haiku"
        assert len(phase["description"]) > 0

    def test_models_count(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        assert len(data["models"]) == 3

    def test_model_roles(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        roles = {m["role"] for m in data["models"]}
        assert roles == {"Director", "Researcher", "Summarizer"}

    def test_domains_from_registry(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        assert len(data["domains"]) == 3
        names = {d["name"] for d in data["domains"]}
        assert "molecular_science" in names
        assert "training_science" in names
        assert "nutrition_science" in names

    def test_domain_has_tool_count(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        for domain in data["domains"]:
            assert domain["tool_count"] > 0

    def test_domain_has_score_definitions(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        mol = next(d for d in data["domains"] if d["name"] == "molecular_science")
        assert len(mol["score_definitions"]) == 3
        keys = {sd["key"] for sd in mol["score_definitions"]}
        assert "prediction_score" in keys

    def test_tools_grouped_by_context(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        contexts = {g["context"] for g in data["tools"]}
        assert "Chemistry" in contexts
        assert "Investigation" in contexts
        assert "Training Science" in contexts
        assert "Nutrition Science" in contexts

    def test_total_tool_count(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        total = sum(len(g["tools"]) for g in data["tools"])
        assert total == 67

    def test_tool_has_name_and_description(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        for group in data["tools"]:
            for tool in group["tools"]:
                assert "name" in tool
                assert "description" in tool
                assert len(tool["name"]) > 0

    def test_data_sources_count(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        assert len(data["data_sources"]) == 16

    def test_data_source_fields(self, client: TestClient) -> None:
        data = client.get("/api/v1/methodology").json()
        source = data["data_sources"][0]
        assert "name" in source
        assert "url" in source
        assert "purpose" in source
        assert "auth" in source
        assert "context" in source

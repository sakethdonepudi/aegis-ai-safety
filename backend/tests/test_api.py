"""API contract tests using dependency overrides (no Db2 or LLM required)."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_pipeline, get_repository
from app.core.errors import DatabaseUnavailableError, LLMUnavailableError
from app.main import app


def verification_payload() -> dict:
    return {
        "session_id": 7,
        "submitted_text": "SolarCell-X achieved 92% conversion efficiency under standard test conditions.",
        "model_provider": "test/model",
        "status": "COMPLETED",
        "error_message": None,
        "created_at": datetime(2026, 1, 1, 12, 0).isoformat(),
        "counts": {
            "total": 1,
            "supported": 1,
            "contradicted": 0,
            "insufficient_evidence": 0,
            "verification_error": 0,
        },
        "claims": [
            {
                "claim_id": 1,
                "original_claim": "SolarCell-X achieved 92% conversion efficiency.",
                "normalized_claim": "SolarCell-X achieved 92% conversion efficiency.",
                "claim_type": "NUMERICAL",
                "position_start": 0,
                "position_end": 48,
                "classification": "SUPPORTED",
                "explanation": "Passage P1 states 92%.",
                "limitations": "Synthetic evidence.",
                "verification_method": "test",
                "result_created_at": datetime(2026, 1, 1, 12, 0).isoformat(),
                "evidence": [
                    {
                        "passage_id": 1,
                        "passage_text": "SolarCell-X achieved 92% efficiency.",
                        "page_number": 1,
                        "passage_index": 0,
                        "document_id": 1,
                        "document_title": "Synthetic study",
                        "filename": "study.txt",
                        "relevance_score": 5.2,
                    }
                ],
            }
        ],
    }


class FakePipeline:
    def verify(self, **kwargs):
        return verification_payload()


class FailingPipeline:
    def verify(self, **kwargs):
        raise LLMUnavailableError("The configured language model was unavailable.")


class FakeRepository:
    def health(self):
        return {
            "connected": True,
            "server": "TESTDB",
            "server_time": datetime(2026, 1, 1),
            "schema": "AEGIS",
            "tables": [
                "DOCUMENTS",
                "PASSAGES",
                "VERIFICATION_SESSIONS",
                "CLAIMS",
                "VERIFICATION_RESULTS",
                "EVIDENCE_LINKS",
            ],
            "missing_tables": [],
        }


class UnavailableRepository:
    def health(self):
        raise DatabaseUnavailableError("unreachable")


@pytest.fixture()
def client():
    app.dependency_overrides[get_pipeline] = lambda: FakePipeline()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_reports_configuration(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert {"llm_provider", "llm_model", "database"} <= body.keys()


def test_db_health_reports_tables(client):
    response = client.get("/api/db/health")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["schema"] == "AEGIS"
    assert len(body["tables"]) == 6


def test_db_health_returns_503_without_leaking_details():
    app.dependency_overrides[get_repository] = lambda: UnavailableRepository()
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/db/health")
        assert response.status_code == 503
        body = response.json()
        assert body["connected"] is False
        assert "unreachable" not in response.text
        assert "password" not in response.text.lower()
    finally:
        app.dependency_overrides.clear()


def test_verify_returns_structured_result(client):
    response = client.post(
        "/api/verify",
        json={
            "submitted_text": "SolarCell-X achieved 92% conversion efficiency under standard test conditions.",
            "document_ids": [1],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claims"][0]["classification"] == "SUPPORTED"
    assert body["claims"][0]["evidence"][0]["passage_id"] == 1
    assert body["counts"]["supported"] == 1


def test_verify_rejects_short_text(client):
    response = client.post("/api/verify", json={"submitted_text": "short", "document_ids": [1]})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_verify_rejects_negative_document_ids(client):
    response = client.post(
        "/api/verify",
        json={"submitted_text": "A sufficiently long research claim.", "document_ids": [-3]},
    )
    assert response.status_code == 422


def test_llm_failure_is_a_clear_503():
    app.dependency_overrides[get_pipeline] = lambda: FailingPipeline()
    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/verify",
                json={
                    "submitted_text": "A sufficiently long research claim to verify.",
                    "document_ids": [1],
                },
            )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "llm_unavailable"
    finally:
        app.dependency_overrides.clear()


def test_upload_rejects_unsupported_extension(client):
    response = client.post(
        "/api/documents",
        files={"file": ("payload.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_upload"


def test_missing_session_returns_404(client):
    class MissingRepository(FakeRepository):
        def get_session(self, session_id):
            from app.core.errors import NotFoundError

            raise NotFoundError("Verification session not found.")

    app.dependency_overrides[get_repository] = lambda: MissingRepository()
    response = client.get("/api/verifications/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"

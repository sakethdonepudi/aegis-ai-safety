"""Claim verification tests, including the evidence-link guardrails."""

from __future__ import annotations

from app.models.domain import Classification, ExtractedClaim, PassageCandidate
from app.services.claim_verification import ClaimVerificationService
from tests.fakes import ScriptedLLM, verification_response

CLAIM = ExtractedClaim(
    original_claim="SolarCell-X achieved 92% conversion efficiency.",
    normalized_claim="SolarCell-X achieved 92% conversion efficiency.",
    claim_type="NUMERICAL",
)

PASSAGES = [
    PassageCandidate(
        passage_id=11,
        document_id=1,
        document_title="Synthetic study",
        filename="study.txt",
        passage_text="SolarCell-X achieved a conversion efficiency of 92% under standard test conditions.",
        page_number=1,
        passage_index=0,
        retrieval_score=7.25,
    ),
    PassageCandidate(
        passage_id=12,
        document_id=1,
        document_title="Synthetic study",
        filename="study.txt",
        passage_text="The coating reduced manufacturing cost by 15%.",
        page_number=1,
        passage_index=1,
        retrieval_score=2.0,
    ),
]


def service_returning(payload: str) -> ClaimVerificationService:
    return ClaimVerificationService(ScriptedLLM(lambda system, user: payload))


def test_supported_with_valid_passage_reference():
    result = service_returning(verification_response("SUPPORTED", [11])).verify(CLAIM, PASSAGES)
    assert result.classification == Classification.SUPPORTED
    assert [item.passage_id for item in result.evidence] == [11]
    assert result.evidence[0].relevance_score == 7.25


def test_fabricated_passage_id_is_downgraded():
    payload = verification_response("SUPPORTED", [999])
    result = service_returning(payload).verify(CLAIM, PASSAGES)
    assert result.classification == Classification.INSUFFICIENT_EVIDENCE
    assert result.evidence == []
    assert "downgraded" in result.explanation.lower()


def test_contradicted_without_evidence_is_downgraded():
    payload = verification_response("CONTRADICTED", [])
    result = service_returning(payload).verify(CLAIM, PASSAGES)
    assert result.classification == Classification.INSUFFICIENT_EVIDENCE
    assert result.evidence == []


def test_missing_evidence_never_becomes_contradiction():
    def handler(system: str, user: str) -> str:
        raise AssertionError("The LLM must not be called without candidates")

    result = ClaimVerificationService(ScriptedLLM(handler)).verify(CLAIM, [])
    assert result.classification == Classification.INSUFFICIENT_EVIDENCE
    assert "not evidence that the claim is false" in result.explanation


def test_malformed_model_json_becomes_verification_error():
    result = service_returning("not json at all").verify(CLAIM, PASSAGES)
    assert result.classification == Classification.VERIFICATION_ERROR


def test_unsupported_classification_becomes_verification_error():
    result = service_returning(verification_response("PROBABLY_TRUE", [11])).verify(CLAIM, PASSAGES)
    assert result.classification == Classification.VERIFICATION_ERROR


def test_lowercase_classification_is_accepted():
    result = service_returning(verification_response("supported", [11])).verify(CLAIM, PASSAGES)
    assert result.classification == Classification.SUPPORTED


def test_duplicate_references_are_collapsed():
    payload = verification_response("SUPPORTED", [11, 11, 12])
    result = service_returning(payload).verify(CLAIM, PASSAGES)
    assert [item.passage_id for item in result.evidence] == [11, 12]


def test_numeric_conflict_overrides_insufficient_model_judgment():
    numeric_claim = ExtractedClaim(
        original_claim="The encoder consists of 8 identical layers.",
        normalized_claim="The encoder consists of 8 identical layers.",
        claim_type="NUMERICAL",
    )
    numeric_passage = PassageCandidate(
        passage_id=21,
        document_id=1,
        document_title="Attention Is All You Need",
        filename="paper.pdf",
        passage_text="The encoder is composed of a stack of N = 6 identical layers.",
        page_number=3,
        passage_index=0,
        retrieval_score=5.0,
    )
    payload = verification_response("INSUFFICIENT_EVIDENCE", [21])
    result = service_returning(payload).verify(numeric_claim, [numeric_passage])
    assert result.classification == Classification.CONTRADICTED
    assert "Deterministic numeric comparison" in result.explanation
    assert "deterministic_numeric_check" in result.verification_method
    assert result.numerical_analysis is not None
    assert "6 identical layers" in result.numerical_analysis

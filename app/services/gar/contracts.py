from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List
from app.extensions import db
from app.models.contracts.contract import Contract

def parse_contract_text(contract: Contract, *, text: str, model_name: str, model_version: str, policy_version: str, context: Dict[str, Any] | None = None):
    """Persist a fresh parse (idempotent if text is same)."""
    contract.ai_parsed_text = text
    contract.ai_parsed_summary = None
    contract.ai_extracted_data = {}
    contract.ai_model_name = model_name
    contract.ai_model_version = model_version
    contract.ai_policy_version = policy_version
    contract.ai_last_parsed_at = datetime.utcnow()
    if context:
        contract.ai_context = {**(contract.ai_context or {}), **context}
    db.session.commit()

def save_parsed_outputs(contract: Contract, *, summary: str | None, extracted: Dict[str, Any] | None, recommendations: List[Dict[str, Any]] | None = None):
    if summary is not None:
        contract.ai_parsed_summary = summary
    if extracted is not None:
        contract.ai_extracted_data = extracted
    if recommendations is not None:
        contract.ai_recommendations = recommendations
    db.session.commit()

def score_contract(contract: Contract, *, scorecard: Dict[str, Any], rank: int | None = None, is_preferred: bool | None = None, reason: str | None = None):
    contract.ai_scorecard = scorecard
    contract.ai_rank = rank
    if is_preferred is not None:
        contract.ai_is_preferred = is_preferred
    contract.ai_reason_for_recommendation = reason
    contract.ai_last_scored_at = datetime.utcnow()
    db.session.commit()

def update_embedding(contract: Contract, embedding: list[float]):
    contract.ai_embedding = embedding
    db.session.commit()

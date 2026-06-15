"""
External memory persistence and blob storage reference tools (Pillar 6: Write & Persist).

Empowers the agent to persist durable customer facts across turns/sessions to prevent
memory loss, and offload large intermediate tables/files out-of-context via lightweight reference handles.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Durable Key-Value store storage location
DATA_STORE_DIR = Path(__file__).resolve().parent.parent.parent / "eval" / "results" / "memory_store"
DATA_STORE_DIR.mkdir(parents=True, exist_ok=True)


def write_user_profile(customer_id: str, fact_key: str, fact_value: Any) -> dict:
    """
    Persists durable user facts (e.g. customer status, verified VIP identity, exact location constraints)
    to an external key-value database to prevent memory degradation and context clash across long conversations.

    Args:
        customer_id: The identifier of the customer (e.g. VIP-777).
        fact_key: The specific factual aspect being persisted (e.g., 'vip_status', 'arid_indoor_constraint').
        fact_value: The value representing the fact.

    Returns:
        dict: A success message confirming durable external key-value persistence.
    """
    logger.info("Persisting durable fact for customer %s: %s = %s", customer_id, fact_key, fact_value)
    
    file_path = DATA_STORE_DIR / f"profile_{customer_id}.json"
    data = {}
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception:
            pass

    data[fact_key] = fact_value
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error("Failed to write to external memory store: %s", e)
        return {"status": "error", "message": str(e)}

    return {"status": "success", "message": f"Persisted fact '{fact_key}' to external Key-Value memory store."}


def fetch_result(artifact_id: str) -> dict:
    """
    Retrieves the content of a large intermediate calculation or external document by its reference handle,
    avoiding active window prompt bloat.

    Args:
        artifact_id: The unique reference handle (e.g., 'audit_report_88', 'care_manual_extended').

    Returns:
        dict: The losslessly restored contents of the requested artifact.
    """
    logger.info("Fetching out-of-context artifact result for handle: %s", artifact_id)

    # Simulated lookup for standard enterprise test suite artifacts
    if artifact_id == "care_manual_extended":
        content = {
            "title": "Extended Bonsai Care Manual for Arid Environments",
            "section_1": "Keep soil pH strictly between 6.5 and 7.0. Mist leaves twice daily.",
            "section_2": "Root winterization requires reducing watering schedule by 50%."
        }
    elif artifact_id == "audit_report_88":
        content = {
            "customer_tier": "VIP Gold Tier",
            "prior_orders": ["50 bags potting soil", "Drip irrigation manifold"],
            "eligible_for_discounts": True
        }
    else:
        content = {"status": "not_found", "message": f"No external artifact found for handle {artifact_id}."}

    return {"status": "success", "artifact_id": artifact_id, "content": content}

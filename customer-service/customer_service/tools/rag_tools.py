"""
Lightweight RAG retrieval tools (Pillar 3: Retrieve on Demand).

Injects static domain manuals, edge-case rules, and warranty policies into the active context
only when relevant, eliminating base prompt static bloat.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def retrieve_domain_rules(query: str) -> dict:
    """
    Retrieves dynamic domain rules and installation guides based on semantic search queries,
    keeping base prompt size minimal and focused.

    Args:
        query: The domain topic being searched (e.g., 'drip irrigation installation', 'petunia fertilizer').

    Returns:
        dict: The retrieved context snippets.
    """
    logger.info("Retrieving dynamic RAG rules for query: %s", query)

    query_lower = query.lower()
    if "drip irrigation" in query_lower:
        chunks = [
            "Install pressure regulator (max 25 PSI) before attaching main tubing header.",
            "Winterization Protocol: Purge lines with air compressor at 30 PSI maximum.",
            "Warranty Details: Full 3-year replacement warranty on valves and tubing manifolds."
        ]
    elif "bonsai" in query_lower:
        chunks = [
            "Indoor Arid Env: Provide artificial humidity tray beneath shallow root base.",
            "Leaf Disease Warning: Fungal spotting requires immediate sulfur-based fungicide misting."
        ]
    else:
        chunks = [
            "General Maintenance: Keep soil moist but avoid root submersion.",
            "Auto-apply standard 10% discount on orders exceeding $100."
        ]

    return {"status": "success", "retrieved_chunks": chunks, "query": query}

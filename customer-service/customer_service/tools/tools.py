# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tools module for the customer service agent with strict Pydantic validation and payload pruning."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


# --- Pydantic Schemas for Strict Tool Schema Hardening & Response Filtering (Pillar 1: Prune) ---

class CartItemModel(BaseModel):
    product_id: str
    name: str
    quantity: int

class CartSummaryModel(BaseModel):
    items: List[CartItemModel]
    subtotal: float
    total_items_count: int

class ProductRecommendationModel(BaseModel):
    product_id: str
    name: str
    description: str

class RecommendationResponseModel(BaseModel):
    recommendations: List[ProductRecommendationModel]


def send_call_companion_link(phone_number: str) -> dict:
    """
    Sends a link to the user's phone number to start a video session.

    **KNOWN LIMITATIONS:**
    - ONLY sends a link to connect with a human expert.
    - The AI CANNOT see or process video. Do not promise video inspection.

    Args:
        phone_number (str): The phone number to send the link to.

    Returns:
        dict: A dictionary with the status and message.
    """
    logger.info("Sending call companion link to %s", phone_number)
    return {"status": "success", "message": f"Link sent to {phone_number}"}


def approve_discount(discount_type: Literal["percentage", "flat"], value: float, reason: str) -> dict:
    """
    Approve the flat rate or percentage discount requested by the user.

    **KNOWN LIMITATIONS:**
    - Maximum discount allowed without manager approval is 10.
    - Cannot approve discounts > 10 directly. Must use sync_ask_for_approval instead.

    Args:
        discount_type: The type of discount, either "percentage" or "flat".
        value: The value of the discount.
        reason: The reason for the discount.
    """
    if value > 10:
        logger.info("Denying %s discount of %s", discount_type, value)
        return {"status": "rejected", "message": "discount too large. Must be 10 or less."}
    logger.info("Approving a %s discount of %s because %s", discount_type, value, reason)
    return {"status": "ok"}


def sync_ask_for_approval(discount_type: Literal["percentage", "flat"], value: float, reason: str) -> dict:
    """
    Asks the manager for approval for a discount.

    **KNOWN LIMITATIONS:**
    - Only submits an approval request to a manager.
    - Does not directly apply the discount to the cart.

    Args:
        discount_type: The type of discount, either "percentage" or "flat".
        value: The value of the discount.
        reason: The reason for the discount.
    """
    logger.info("Asking for approval for a %s discount of %s because %s", discount_type, value, reason)
    return {"status": "approved"}


def update_salesforce_crm(customer_id: str, details: dict) -> dict:
    """
    Updates the Salesforce CRM with customer details.

    **KNOWN LIMITATIONS:**
    - Background sync only. Does not email the customer or modify the active shopping cart.
    """
    logger.info("Updating Salesforce CRM for customer ID %s with details: %s", customer_id, details)
    return {"status": "success", "message": "Salesforce record updated."}


def access_cart_information(customer_id: str) -> dict:
    """
    Retrieves the customer's cart contents. Use this to check cart contents before related operations.

    **KNOWN LIMITATIONS:**
    - Read-only operation. Cannot modify the cart.

    Args:
        customer_id (str): The ID of the customer.

    Returns:
        dict: A strictly pruned dictionary representing the cart contents.
    """
    logger.info("Accessing cart information for customer ID: %s", customer_id)

    raw_cart = {
        "items": [
            {"product_id": "soil-123", "name": "Standard Potting Soil", "quantity": 1, "unneeded_verbose_metadata": "unpruned_database_garbage_blob"},
            {"product_id": "fert-456", "name": "General Purpose Fertilizer", "quantity": 1, "unneeded_verbose_metadata": "unpruned_database_garbage_blob"},
        ],
        "subtotal": 25.98,
        "internal_server_debug_traces": "long_unpruned_token_bloat_string_that_should_be_stripped"
    }

    # Pillar 1: Prune & Offload (Wrap in Pydantic to truncate and filter unneeded payload bloat)
    cleaned_items = [CartItemModel(**item) for item in raw_cart["items"]]
    summary = CartSummaryModel(items=cleaned_items, subtotal=raw_cart["subtotal"], total_items_count=len(cleaned_items))
    return summary.model_dump()


def modify_cart(customer_id: str, items_to_add: list[dict], items_to_remove: list[dict]) -> dict:
    """
    Modifies the user's shopping cart by adding and/or removing items.

    **KNOWN LIMITATIONS:**
    - Check cart contents using access_cart_information before modifying.
    """
    logger.info("Modifying cart for customer ID: %s", customer_id)
    logger.info("Adding items: %s", items_to_add)
    logger.info("Removing items: %s", items_to_remove)
    return {
        "status": "success",
        "message": "Cart updated successfully.",
        "items_added": True,
        "items_removed": True,
    }


def get_product_recommendations(plant_type: str, customer_id: str) -> dict:
    """
    Provides product recommendations based on the type of plant.

    **KNOWN LIMITATIONS:**
    - Does not verify current stock availability. Use check_product_availability separately.
    """
    logger.info("Getting product recommendations for plant type: %s and customer %s", plant_type, customer_id)
    if plant_type.lower() == "petunias":
        raw_recs = [
            {"product_id": "soil-456", "name": "Bloom Booster Potting Mix", "description": "Provides extra nutrients that Petunias love.", "internal_ranking_scores": [0.99, 0.98]},
            {"product_id": "fert-789", "name": "Flower Power Fertilizer", "description": "Specifically formulated for flowering annuals.", "internal_ranking_scores": [0.95, 0.91]},
        ]
    else:
        raw_recs = [
            {"product_id": "soil-123", "name": "Standard Potting Soil", "description": "A good all-purpose potting soil.", "internal_ranking_scores": [0.89]},
            {"product_id": "fert-456", "name": "General Purpose Fertilizer", "description": "Suitable for a wide variety of plants.", "internal_ranking_scores": [0.85]},
        ]

    # Pillar 1: Prune & Offload (Filter response payload to remove token bloat)
    filtered = [ProductRecommendationModel(**rec) for rec in raw_recs]
    response = RecommendationResponseModel(recommendations=filtered)
    return response.model_dump()


def check_product_availability(product_id: str, store_id: str) -> dict:
    """
    Checks the availability of a product at a specified store.
    """
    logger.info("Checking availability of product ID: %s at store: %s", product_id, store_id)
    return {"available": True, "quantity": 10, "store": store_id}


def schedule_planting_service(customer_id: str, date: str, time_range: str, details: str) -> dict:
    """
    Schedules a planting service appointment.
    """
    logger.info("Scheduling planting service for customer ID: %s on %s (%s)", customer_id, date, time_range)
    logger.info("Details: %s", details)
    start_time_str = time_range.split("-")[0]
    confirmation_time_str = f"{date} {start_time_str}:00"
    return {
        "status": "success",
        "appointment_id": str(uuid.uuid4()),
        "date": date,
        "time": time_range,
        "confirmation_time": confirmation_time_str,
    }


def get_available_planting_times(date: str) -> list:
    """
    Retrieves available planting service time slots for a given date.
    """
    logger.info("Retrieving available planting times for %s", date)
    return ["9-12", "13-16"]


def send_care_instructions(customer_id: str, plant_type: str, delivery_method: str) -> dict:
    """
    Sends an email or SMS with instructions on how to take care of a specific plant type.
    """
    logger.info("Sending care instructions for %s to customer: %s via %s", plant_type, customer_id, delivery_method)
    return {
        "status": "success",
        "message": f"Care instructions for {plant_type} sent via {delivery_method}.",
    }


def generate_qr_code(customer_id: str, discount_value: float, discount_type: str, expiration_days: int) -> dict:
    """
    Generates a QR code for a discount.

    **KNOWN LIMITATIONS:**
    - Creates QR code string data. CANNOT directly email it to the customer.
    """
    if discount_type == "" or discount_type == "percentage":
        if discount_value > 10:
            return {"status": "rejected", "message": "cannot generate a QR code for this amount, must be 10% or less"}
    if discount_type == "fixed" and discount_value > 20:
        return {"status": "rejected", "message": "cannot generate a QR code for this amount, must be 20 or less"}

    logger.info("Generating QR code for customer: %s with %s - %s discount.", customer_id, discount_value, discount_type)
    expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime("%Y-%m-%d")
    return {
        "status": "success",
        "qr_code_data": "MOCK_QR_CODE_DATA",
        "expiration_date": expiration_date,
    }

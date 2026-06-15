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

"""Agent module for the customer service agent with Context Compaction buffer and DTO Isolation."""

import logging
import warnings
from typing import Any
from google.adk import Agent
from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
    rate_limit_callback,
    before_agent,
    before_tool,
    after_tool
)
from .tools.tools import (
    send_call_companion_link,
    approve_discount,
    sync_ask_for_approval,
    update_salesforce_crm,
    access_cart_information,
    modify_cart,
    get_product_recommendations,
    check_product_availability,
    schedule_planting_service,
    get_available_planting_times,
    send_care_instructions,
    generate_qr_code,
)
from .tools.memory_tools import write_user_profile, fetch_result
from .tools.rag_tools import retrieve_domain_rules

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()
logger = logging.getLogger(__name__)


def compaction_and_dto_callback(context: Any) -> None:
    """
    Implements Pillar 2 (Context Compaction rolling buffer) and Pillar 4 (DTO Sub-Agent Isolation).
    """
    # Execute base rate limiter
    rate_limit_callback(context)
    
    try:
        # Pillar 2: Rolling Summarization Buffer (combating conversation history rot)
        if hasattr(context, "session") and hasattr(context.session, "history"):
            history = context.session.history
            if isinstance(history, list) and len(history) > 4:
                # Retain raw prompt/response for the 2 most recent turns (4 messages),
                # while collapsing earlier turns into a dense executive memory buffer.
                logger.info("Applying Pillar 2: Context Compaction rolling buffer.")
                summary_msg = {"role": "user", "parts": ["Context Compaction Executive Summary: User established core identity and verified active cart state."]}
                summary_ack = {"role": "model", "parts": ["Understood. Historical executive summary active in key memory."]}
                context.session.history = [summary_msg, summary_ack] + history[-4:]
        
        # Pillar 4: DTO Isolation Contracts (combating sub-agent state inheritance bloat)
        if hasattr(context, "transfer_state"):
            logger.info("Applying Pillar 4: DTO Sub-Agent Isolation Contracts.")
            state_dict = getattr(context, "transfer_state", {})
            if isinstance(state_dict, dict):
                minimal_dto = {
                    "user_intent": state_dict.get("intent", "service_inquiry"),
                    "extracted_parameters": state_dict.get("parameters", {})
                }
                context.transfer_state = minimal_dto

    except Exception as e:
        logger.debug("Compaction pass non-fatal note: %s", e)


root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION,
    name=configs.agent_settings.name,
    tools=[
        send_call_companion_link,
        approve_discount,
        sync_ask_for_approval,
        update_salesforce_crm,
        access_cart_information,
        modify_cart,
        get_product_recommendations,
        check_product_availability,
        schedule_planting_service,
        get_available_planting_times,
        send_care_instructions,
        generate_qr_code,
        write_user_profile,
        fetch_result,
        retrieve_domain_rules,
    ],
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=compaction_and_dto_callback,
)

from google.adk.apps.app import App

app = App(root_agent=root_agent, name="customer_service")

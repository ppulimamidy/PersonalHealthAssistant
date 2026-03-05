"""
Anthropic Client
Provides a singleton AsyncAnthropic client for AI operations
"""

import os
from typing import Optional
import anthropic

from common.utils.logging import get_logger

logger = get_logger(__name__)

# Global Anthropic client instance
_async_anthropic_client: Optional[anthropic.AsyncAnthropic] = None  # pylint: disable=invalid-name


def get_anthropic_client() -> anthropic.AsyncAnthropic:
    """
    Get async Anthropic client singleton.

    Returns:
        anthropic.AsyncAnthropic: Async Anthropic client instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not configured
    """
    global _async_anthropic_client  # pylint: disable=global-statement,invalid-name

    if _async_anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        _async_anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
        logger.info("Anthropic async client initialized successfully")

    return _async_anthropic_client


def reset_anthropic_client() -> None:
    """Reset the Anthropic client singleton (useful for testing)"""
    global _async_anthropic_client  # pylint: disable=global-statement,invalid-name
    _async_anthropic_client = None
    logger.info("Anthropic client reset")

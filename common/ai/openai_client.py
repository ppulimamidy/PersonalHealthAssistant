"""
OpenAI Client
Provides a singleton OpenAI client for AI operations
"""

import os
from typing import Optional
from openai import OpenAI, AsyncOpenAI

from common.utils.logging import get_logger

logger = get_logger(__name__)

# Global OpenAI client instances
_openai_client: Optional[OpenAI] = None  # pylint: disable=invalid-name
_async_openai_client: Optional[AsyncOpenAI] = None  # pylint: disable=invalid-name


def get_openai_client() -> OpenAI:
    """
    Get OpenAI client singleton

    Returns:
        OpenAI: OpenAI client instance

    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    global _openai_client  # pylint: disable=global-statement,invalid-name

    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        _openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")

    return _openai_client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Get async OpenAI client singleton

    Returns:
        AsyncOpenAI: Async OpenAI client instance

    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    global _async_openai_client  # pylint: disable=global-statement,invalid-name

    if _async_openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        _async_openai_client = AsyncOpenAI(api_key=api_key)
        logger.info("Async OpenAI client initialized successfully")

    return _async_openai_client


def reset_openai_client() -> None:
    """Reset the OpenAI client singleton (useful for testing)"""
    global _openai_client, _async_openai_client  # pylint: disable=global-statement,invalid-name
    _openai_client = None
    _async_openai_client = None
    logger.info("OpenAI clients reset")

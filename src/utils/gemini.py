"""Gemini client factory with dev/prod authentication support."""

import json
from typing import Any, Optional

from google import genai
from google.genai import types

from src.config import get_settings


def get_gemini_client() -> genai.Client:
    """
    Returns configured Gemini client based on environment.
    - Dev: Uses API key
    - Prod/Workstation: Uses Vertex AI with ADC (service account)
    """
    settings = get_settings()

    if settings.is_dev():
        # Local development with API key
        client = genai.Client(api_key=settings.google_api_key)
    else:
        # Prod and Workstation use service account via ADC
        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )

    return client


def generate_content(
    prompt: str,
    system_instruction: Optional[str] = None,
) -> str:
    """Generate text content using Gemini."""
    client = get_gemini_client()
    settings = get_settings()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
    )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )

    return response.text


def generate_structured(
    prompt: str,
    response_schema: dict[str, Any],
    system_instruction: Optional[str] = None,
) -> dict[str, Any]:
    """
    Generate structured output using Gemini.
    Used for chart data extraction.
    """
    client = get_gemini_client()
    settings = get_settings()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
    )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )

    return json.loads(response.text)

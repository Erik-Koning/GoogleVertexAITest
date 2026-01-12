"""Extract structured chart data from context using Gemini."""

from typing import Any, Optional

from src.utils.gemini import generate_structured


EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant. Your job is to extract numerical data from the provided context that can be used to create a chart.

Rules:
1. Only extract data that is explicitly mentioned in the context
2. Do not make up or estimate values
3. Use appropriate labels from the context
4. If no suitable data exists for a chart, return empty data
5. Round percentages to 1 decimal place
6. Ensure all values are numbers (not strings)"""

EXTRACTION_PROMPT = """Based on the user's question and the context provided, extract data suitable for a {chart_type} chart.

User Question: {user_query}

Context:
{context}

Extract the relevant numerical data and provide an appropriate chart title."""


def extract_chart_data(
    user_query: str,
    context: str,
    chart_type: str,
) -> Optional[dict[str, Any]]:
    """
    Extract chart data from context using Gemini structured output.

    Args:
        user_query: The user's question
        context: The RAG context from Vertex AI Search
        chart_type: The type of chart to generate

    Returns:
        Dictionary with 'data' and 'title' keys, or None if extraction fails
    """
    # Define the response schema for structured output
    response_schema = {
        "type": "object",
        "properties": {
            "data": {
                "type": "object",
                "description": "Key-value pairs where keys are labels and values are numbers",
                "additionalProperties": {"type": "number"},
            },
            "title": {
                "type": "string",
                "description": "A descriptive title for the chart",
            },
            "has_data": {
                "type": "boolean",
                "description": "Whether suitable data was found in the context",
            },
        },
        "required": ["data", "title", "has_data"],
    }

    prompt = EXTRACTION_PROMPT.format(
        chart_type=chart_type,
        user_query=user_query,
        context=context,
    )

    try:
        result = generate_structured(
            prompt=prompt,
            response_schema=response_schema,
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
        )

        if not result.get("has_data") or not result.get("data"):
            return None

        return {
            "data": result["data"],
            "title": result["title"],
        }
    except Exception:
        return None

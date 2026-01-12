"""PDF metadata definitions for document sync."""

# Define metadata for each PDF in the repo
# Maps filename -> metadata that gets stored in GCS and Vertex AI Search

PDF_METADATA: dict[str, dict[str, str]] = {
    "fund-a-facts.pdf": {
        "display_name": "Fund A - Fund Facts",
        "source_url": "https://yoursite.com/funds/fund-a-facts.pdf",
        "category": "fund_facts",
        "fund_code": "FUND-A",
    },
    "fund-b-facts.pdf": {
        "display_name": "Fund B - Fund Facts",
        "source_url": "https://yoursite.com/funds/fund-b-facts.pdf",
        "category": "fund_facts",
        "fund_code": "FUND-B",
    },
    "fund-c-facts.pdf": {
        "display_name": "Fund C - Fund Facts",
        "source_url": "https://yoursite.com/funds/fund-c-facts.pdf",
        "category": "fund_facts",
        "fund_code": "FUND-C",
    },
    "fund-d-facts.pdf": {
        "display_name": "Fund D - Fund Facts",
        "source_url": "https://yoursite.com/funds/fund-d-facts.pdf",
        "category": "fund_facts",
        "fund_code": "FUND-D",
    },
    "fund-e-facts.pdf": {
        "display_name": "Fund E - Fund Facts",
        "source_url": "https://yoursite.com/funds/fund-e-facts.pdf",
        "category": "fund_facts",
        "fund_code": "FUND-E",
    },
    "tfsa-guide.pdf": {
        "display_name": "TFSA Complete Guide",
        "source_url": "https://yoursite.com/guides/tfsa-guide.pdf",
        "category": "tfsa",
    },
    "tfsa-contribution-rules.pdf": {
        "display_name": "TFSA Contribution Rules",
        "source_url": "https://yoursite.com/guides/tfsa-contribution-rules.pdf",
        "category": "tfsa",
    },
    "rrsp-guide.pdf": {
        "display_name": "RRSP Complete Guide",
        "source_url": "https://yoursite.com/guides/rrsp-guide.pdf",
        "category": "rrsp",
    },
    "rrsp-withdrawal-rules.pdf": {
        "display_name": "RRSP Withdrawal Rules",
        "source_url": "https://yoursite.com/guides/rrsp-withdrawal-rules.pdf",
        "category": "rrsp",
    },
    "home-buyers-plan.pdf": {
        "display_name": "Home Buyers' Plan Guide",
        "source_url": "https://yoursite.com/guides/home-buyers-plan.pdf",
        "category": "rrsp",
    },
}


def get_metadata_for_file(filename: str) -> dict[str, str]:
    """Get metadata for a PDF file, with defaults if not defined."""
    if filename in PDF_METADATA:
        return PDF_METADATA[filename]

    # Default metadata for unknown files
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return {
        "display_name": stem.replace("-", " ").replace("_", " ").title(),
        "source_url": "",
        "category": "fund_facts",  # Default category
    }

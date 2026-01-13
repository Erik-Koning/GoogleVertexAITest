"""Startup validation for FAISS indexes."""

from pathlib import Path

from src.config import get_settings


async def validate_faiss_indexes() -> None:
    """Validate all FAISS indexes exist on startup."""
    settings = get_settings()

    indexes = {
        "fund_facts": settings.faiss_index_fundfacts,
        "rrsp": settings.faiss_index_rrsp,
        "tfsa": settings.faiss_index_tfsa,
    }

    found_indexes = []
    missing_indexes = []

    for name, path_str in indexes.items():
        if not path_str:
            continue

        index_path = Path(path_str)

        if not index_path.exists():
            missing_indexes.append(f"{name}: {path_str}")
            continue

        # Check for required FAISS files
        index_file = index_path / "index.faiss"
        pkl_file = index_path / "index.pkl"

        if not index_file.exists() or not pkl_file.exists():
            missing_indexes.append(f"{name}: {path_str} (missing index.faiss or index.pkl)")
            continue

        found_indexes.append(f"{name}: {path_str}")

    if found_indexes:
        print("FAISS indexes found:")
        for idx in found_indexes:
            print(f"  - {idx}")

    if missing_indexes:
        print("WARNING: Some FAISS indexes are missing:")
        for idx in missing_indexes:
            print(f"  - {idx}")
        print("The application will start but searches for those topics may fail.")

    if not found_indexes:
        print("WARNING: No FAISS indexes found! Searches will fail until indexes are available.")


# Keep old name for backwards compatibility with main.py
sync_pdfs_on_startup = validate_faiss_indexes

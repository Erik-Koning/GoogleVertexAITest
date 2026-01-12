"""Startup validation for FAISS index."""

from pathlib import Path

from src.config import get_settings


async def validate_faiss_index() -> None:
    """Validate FAISS index exists on startup."""
    settings = get_settings()
    index_path = Path(settings.faiss_index_path)

    if not index_path.exists():
        print(f"WARNING: FAISS index not found at: {index_path}")
        print("The application will start but searches will fail until the index is available.")
        return

    # Check for required FAISS files
    index_file = index_path / "index.faiss"
    pkl_file = index_path / "index.pkl"

    if not index_file.exists() and not pkl_file.exists():
        print(f"WARNING: FAISS index files not found in: {index_path}")
        print("Expected index.faiss and index.pkl files.")
        return

    print(f"FAISS index found at: {index_path}")


# Keep old name for backwards compatibility with main.py
sync_pdfs_on_startup = validate_faiss_index

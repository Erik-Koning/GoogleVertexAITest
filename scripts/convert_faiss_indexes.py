#!/usr/bin/env python3
"""
Convert Python FAISS indexes to Node.js compatible format.

Converts index.faiss + index.pkl to faiss.index + docstore.json
for each topic-specific index directory.
"""
import json
import pickle
import shutil
from pathlib import Path

# Source directories (Python format)
# Adjust these paths if your indexes are in different locations
INDEXES = {
    "tfsa": Path("./src/faiss_index_tfsa"),
    "rrsp": Path("./src/faiss_index_rrsp"),
    "fund_facts": Path("./src/faiss_index_fundfacts"),
}

# Output directory for Node.js
OUTPUT_BASE = Path("./faiss_indexes")


def convert_index(name: str, source_dir: Path, output_dir: Path) -> bool:
    """Convert a single FAISS index from Python to Node.js format."""
    index_file = source_dir / "index.faiss"
    pkl_file = source_dir / "index.pkl"

    if not index_file.exists():
        print(f"  ⚠️  Skipping {name}: {index_file} not found")
        return False

    if not pkl_file.exists():
        print(f"  ⚠️  Skipping {name}: {pkl_file} not found")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy the FAISS index (binary format is compatible)
    shutil.copy(index_file, output_dir / "faiss.index")

    # Convert pickle docstore to JSON
    with open(pkl_file, "rb") as f:
        data = pickle.load(f)

    # LangChain pickle contains (docstore, index_to_docstore_id)
    docstore, index_to_id = data

    # Build JSON structure expected by @langchain/community
    docstore_json = {}
    for idx, doc_id in index_to_id.items():
        doc = docstore.search(doc_id)
        docstore_json[str(idx)] = {
            "pageContent": doc.page_content,
            "metadata": doc.metadata if doc.metadata else {},
        }

    with open(output_dir / "docstore.json", "w") as f:
        json.dump(docstore_json, f, indent=2)

    index_size = (output_dir / "faiss.index").stat().st_size
    docstore_size = (output_dir / "docstore.json").stat().st_size
    doc_count = len(docstore_json)

    print(f"  ✓ {name}: {doc_count} documents ({index_size:,} + {docstore_size:,} bytes)")
    return True


def main():
    print("Converting FAISS indexes from Python to Node.js format...\n")

    OUTPUT_BASE.mkdir(exist_ok=True)
    converted = 0

    for name, source_dir in INDEXES.items():
        output_dir = OUTPUT_BASE / name
        if convert_index(name, source_dir, output_dir):
            converted += 1

    print(f"\nConverted {converted}/{len(INDEXES)} indexes to {OUTPUT_BASE}/")

    if converted > 0:
        print("\nOutput structure:")
        print("  faiss_indexes/")
        for name in INDEXES.keys():
            if (OUTPUT_BASE / name).exists():
                print(f"    {name}/")
                print(f"      faiss.index")
                print(f"      docstore.json")

        print("\nSet in .env:")
        print("  FAISS_INDEX_BASE_PATH=./faiss_indexes")


if __name__ == "__main__":
    main()

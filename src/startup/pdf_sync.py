"""PDF sync manager for uploading documents to GCS and triggering Vertex AI import."""

import base64
import hashlib
from pathlib import Path

from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import storage

from src.config import get_settings
from src.startup.metadata import get_metadata_for_file


class PDFSyncManager:
    """Manages syncing PDFs from repo to GCS and Vertex AI Search."""

    def __init__(self):
        self.settings = get_settings()
        self.storage_client = storage.Client(project=self.settings.gcp_project_id)
        self.bucket = self.storage_client.bucket(self.settings.gcs_bucket_name)
        self.local_pdf_dir = Path(__file__).parent.parent.parent / "pdfs"

    def get_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of local file."""
        return hashlib.md5(file_path.read_bytes()).hexdigest()

    def get_gcs_checksum(self, blob_name: str) -> str | None:
        """Get MD5 checksum of GCS object, None if doesn't exist."""
        blob = self.bucket.blob(blob_name)
        if blob.exists():
            blob.reload()
            return blob.md5_hash
        return None

    def _checksums_match(self, local_md5: str, gcs_md5_base64: str | None) -> bool:
        """Compare local hex MD5 with GCS base64 MD5."""
        if gcs_md5_base64 is None:
            return False
        gcs_md5_hex = base64.b64decode(gcs_md5_base64).hex()
        return local_md5 == gcs_md5_hex

    def sync_pdfs(self) -> list[str]:
        """
        Sync local PDFs to GCS.

        Returns:
            List of newly uploaded filenames
        """
        if not self.local_pdf_dir.exists():
            print(f"PDF directory not found: {self.local_pdf_dir}")
            return []

        uploaded = []

        for pdf_file in self.local_pdf_dir.glob("*.pdf"):
            blob_name = f"documents/{pdf_file.name}"
            local_checksum = self.get_file_checksum(pdf_file)

            blob = self.bucket.blob(blob_name)

            # Check if file exists and matches
            if blob.exists():
                blob.reload()
                if self._checksums_match(local_checksum, blob.md5_hash):
                    print(f"Skipping (unchanged): {pdf_file.name}")
                    continue

            # Get metadata for this file
            metadata = get_metadata_for_file(pdf_file.name)

            # Upload with metadata
            blob.metadata = {
                "display_name": metadata.get("display_name", pdf_file.stem),
                "source_url": metadata.get("source_url", ""),
                "category": metadata.get("category", "fund_facts"),
                "checksum": local_checksum,
            }
            blob.upload_from_filename(str(pdf_file))
            uploaded.append(pdf_file.name)
            print(f"Uploaded: {pdf_file.name}")

        return uploaded

    def trigger_import_if_needed(self, uploaded_files: list[str]) -> None:
        """Trigger Vertex AI Search import if new files were uploaded."""
        if not uploaded_files:
            print("No new PDFs to import.")
            return

        print(f"Triggering Vertex AI Search import for {len(uploaded_files)} files...")

        client = discoveryengine.DocumentServiceClient()
        parent = (
            f"projects/{self.settings.gcp_project_id}"
            f"/locations/global"
            f"/collections/default_collection"
            f"/dataStores/{self.settings.vertex_search_data_store_id}"
            f"/branches/default_branch"
        )

        # Import from GCS
        request = discoveryengine.ImportDocumentsRequest(
            parent=parent,
            gcs_source=discoveryengine.GcsSource(
                input_uris=[f"gs://{self.settings.gcs_bucket_name}/documents/*.pdf"],
                data_schema="content",
            ),
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
        )

        operation = client.import_documents(request=request)
        print(f"Import operation started: {operation.operation.name}")
        # Don't block on completion - import runs async


async def sync_pdfs_on_startup() -> None:
    """Called during FastAPI startup to sync PDFs."""
    settings = get_settings()

    # Skip in dev if configured
    if settings.is_dev() and not settings.sync_pdfs_in_dev:
        print("Skipping PDF sync in dev mode (SYNC_PDFS_IN_DEV=false)")
        return

    try:
        syncer = PDFSyncManager()
        uploaded = syncer.sync_pdfs()
        syncer.trigger_import_if_needed(uploaded)
    except Exception as e:
        print(f"PDF sync failed: {e}")
        # Don't fail startup on sync errors

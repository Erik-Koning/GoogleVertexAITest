"""Application configuration with dev/prod environment support."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Environment
    environment: str = "dev"

    # GCP
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"

    # Gemini
    gemini_model: str = "gemini-1.5-pro"
    google_api_key: str = ""  # Dev only

    # Vertex AI Search
    vertex_search_data_store_id: str = ""
    vertex_search_engine_id: str = ""

    # GCS
    gcs_bucket_name: str = ""

    # PDF Sync
    sync_pdfs_in_dev: bool = False
    pdf_base_url: str = ""

    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "dev"

    def is_prod(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "prod"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

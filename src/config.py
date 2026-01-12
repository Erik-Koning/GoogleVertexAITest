"""Application configuration with dev/prod environment support."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars (e.g., TF_VAR_* from Terraform)
    )

    # Environment: "dev" (API key), "prod" (ADC/service account), "workstation" (service account)
    environment: str = "dev"

    # GCP
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"

    # Gemini
    gemini_model: str = "gemini-2.5-flash"
    google_api_key: str = ""  # Dev only
    allow_general_knowledge_fallback: bool = True  # Allow Gemini to answer from internal knowledge when no docs found

    # Vertex AI Search
    vertex_search_data_store_id: str = ""
    vertex_search_engine_id: str = ""

    # GCS
    gcs_bucket_name: str = ""

    # PDF Sync
    sync_pdfs_in_dev: bool = False
    pdf_base_url: str = ""

    def is_dev(self) -> bool:
        """Check if running in local development mode (API key auth)."""
        return self.environment == "dev"

    def is_prod(self) -> bool:
        """Check if running in production mode (service account via ADC)."""
        return self.environment == "prod"

    def is_workstation(self) -> bool:
        """Check if running in Cloud Workstation (service account via ADC)."""
        return self.environment == "workstation"

    def uses_service_account(self) -> bool:
        """Check if using service account authentication (prod or workstation)."""
        return self.environment in ("prod", "workstation")

    def validate_required(self) -> list[str]:
        """
        Validate required settings and return list of missing/invalid configs.
        Returns empty list if all required settings are valid.
        """
        errors = []

        # Validate environment value
        valid_environments = ("dev", "prod", "workstation")
        if self.environment not in valid_environments:
            errors.append(f"ENVIRONMENT must be one of: {', '.join(valid_environments)}")

        if not self.gcp_project_id:
            errors.append("GCP_PROJECT_ID is not set")

        # API key only required for local dev
        if self.is_dev() and not self.google_api_key:
            errors.append("GOOGLE_API_KEY is required for dev environment (use ENVIRONMENT=workstation for service account auth)")

        if not self.vertex_search_data_store_id:
            errors.append("VERTEX_SEARCH_DATA_STORE_ID is not set")

        if not self.vertex_search_engine_id:
            errors.append("VERTEX_SEARCH_ENGINE_ID is not set")

        if not self.gcs_bucket_name:
            errors.append("GCS_BUCKET_NAME is not set")

        return errors


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        message = self._format_message(errors)
        super().__init__(message)

    def _format_message(self, errors: list[str]) -> str:
        lines = [
            "",
            "=" * 60,
            "CONFIGURATION ERROR",
            "=" * 60,
            "",
            "The following required settings are missing or invalid:",
            "",
        ]
        for error in errors:
            lines.append(f"  • {error}")
        lines.extend([
            "",
            "To fix this:",
            "  1. Run: ./scripts/generate_env.sh",
            "  2. Edit .env and add your GOOGLE_API_KEY",
            "  3. Restart the application",
            "",
            "For setup instructions, see: SETUP.md",
            "=" * 60,
        ])
        return "\n".join(lines)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_validated_settings() -> Settings:
    """
    Get settings and validate required configuration.
    Raises ConfigurationError with helpful message if validation fails.
    """
    settings = get_settings()
    errors = settings.validate_required()
    if errors:
        raise ConfigurationError(errors)
    return settings

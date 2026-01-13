"""Tests for application configuration."""

import pytest
from unittest.mock import patch


class TestSettings:
    """Tests for Settings class."""

    def test_default_faiss_paths(self):
        """Test default FAISS index paths are set."""
        from src.config import Settings

        settings = Settings()
        assert settings.faiss_index_fundfacts == "./src/faiss_index_fundfacts"
        assert settings.faiss_index_rrsp == "./src/faiss_index_rrsp"
        assert settings.faiss_index_tfsa == "./src/faiss_index_tfsa"

    def test_get_faiss_index_path(self):
        """Test getting FAISS path by tool name."""
        from src.config import Settings

        settings = Settings()

        assert settings.get_faiss_index_path("fund_facts") == settings.faiss_index_fundfacts
        assert settings.get_faiss_index_path("rrsp") == settings.faiss_index_rrsp
        assert settings.get_faiss_index_path("tfsa") == settings.faiss_index_tfsa

    def test_get_faiss_index_path_unknown(self):
        """Test fallback to fundfacts for unknown tool."""
        from src.config import Settings

        settings = Settings()
        assert settings.get_faiss_index_path("unknown") == settings.faiss_index_fundfacts

    def test_environment_helpers(self):
        """Test environment check methods."""
        from src.config import Settings

        settings = Settings(environment="dev")
        assert settings.is_dev() is True
        assert settings.is_prod() is False
        assert settings.is_workstation() is False
        assert settings.uses_service_account() is False

        settings = Settings(environment="prod")
        assert settings.is_dev() is False
        assert settings.is_prod() is True
        assert settings.uses_service_account() is True

        settings = Settings(environment="workstation")
        assert settings.is_workstation() is True
        assert settings.uses_service_account() is True


class TestConfigurationValidation:
    """Tests for configuration validation."""

    def test_validation_missing_gcp_project(self):
        """Test validation catches missing GCP project."""
        from src.config import Settings

        settings = Settings(gcp_project_id="")
        errors = settings.validate_required()
        assert any("GCP_PROJECT_ID" in e for e in errors)

    def test_validation_missing_api_key_in_dev(self):
        """Test validation catches missing API key in dev."""
        from src.config import Settings

        settings = Settings(
            environment="dev",
            gcp_project_id="test-project",
            google_api_key="",
        )
        errors = settings.validate_required()
        assert any("GOOGLE_API_KEY" in e for e in errors)

    def test_validation_passes_with_service_account(self):
        """Test validation passes for workstation without API key."""
        from src.config import Settings

        settings = Settings(
            environment="workstation",
            gcp_project_id="test-project",
            google_api_key="",  # Not required for workstation
        )
        errors = settings.validate_required()
        assert not any("GOOGLE_API_KEY" in e for e in errors)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_error_formatting(self):
        """Test error message formatting."""
        from src.config import ConfigurationError

        error = ConfigurationError(["Error 1", "Error 2"])
        message = str(error)

        assert "CONFIGURATION ERROR" in message
        assert "Error 1" in message
        assert "Error 2" in message

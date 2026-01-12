# Vertex AI Search Data Store
resource "google_discovery_engine_data_store" "fund_docs" {
  location         = var.vertex_search_location
  data_store_id    = var.data_store_id
  display_name     = "Fund Knowledge Base"
  industry_vertical = "GENERIC"
  content_config   = "CONTENT_REQUIRED"

  document_processing_config {
    default_parsing_config {
      digital_parsing_config {}
    }
  }

  depends_on = [google_project_service.apis]
}

# Vertex AI Search Engine
resource "google_discovery_engine_search_engine" "fund_search" {
  engine_id      = var.engine_id
  collection_id  = "default_collection"
  location       = var.vertex_search_location
  display_name   = "Fund Search Engine"
  data_store_ids = [google_discovery_engine_data_store.fund_docs.data_store_id]

  search_engine_config {
    search_tier    = "SEARCH_TIER_ENTERPRISE"
    search_add_ons = ["SEARCH_ADD_ON_LLM"]
  }

  depends_on = [google_discovery_engine_data_store.fund_docs]
}

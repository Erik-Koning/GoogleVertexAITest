# Quick reference for Cloud Workstation:

# === INSTALL PIP PACKAGES (no internet on workstation) ===

# On local machine (with internet):
./scripts/bundle_packages.sh
# Transfer pip_bundle.zip to workstation

# On workstation:
unzip pip_bundle.zip
python -m venv .venv
source .venv/bin/activate
pip install --no-index --find-links=pip_bundle -r requirements.txt
rm -rf pip_bundle  # cleanup

# === TERRAFORM (first time setup) ===

gcloud auth list # Verify service account
gcloud config set project YOUR_PROJECT_ID
cd infra
terraform init && terraform apply
cd ..

# === CONFIGURE APP ===

./scripts/generate_env.sh
sed -i 's/ENVIRONMENT=dev/ENVIRONMENT=workstation/' .env

# === TEST SERVER ===

# Option A: Direct (for development)

uvicorn src.main:app --reload --port 8080

# Option B: Docker (validates prod)

./scripts/docker_test.sh all

    ┌───────────────────┬──────────────────────────────────────┬────────────────────────┐

│ Environment │ .env │ terraform.tfvars │
├───────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Local Dev │ ENVIRONMENT=dev + GOOGLE_API_KEY │ deploy_cloud_run=false │
├───────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Cloud Workstation │ ENVIRONMENT=workstation (no API key) │ deploy_cloud_run=false │
├───────────────────┼──────────────────────────────────────┼────────────────────────┤
│ Production │ ENVIRONMENT=prod (no API key) │ deploy_cloud_run=true │
└───────────────────┴──────────────────────────────────────┴────────────────────────┘

# Staging environment Terraform configuration

terraform {
  # Use partial configuration with minimal settings
  # Complete settings will be loaded from state.config (gitignored)
  # Run: terraform init -backend-config="state.config"
  backend "remote" {}
}

module "baller" {
  source = "../.."
  
  environment = "staging"
  aws_region  = "us-east-1"
  project     = "baller"
}

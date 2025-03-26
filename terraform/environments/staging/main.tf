# Staging environment Terraform configuration

terraform {
  # Use partial configuration with minimal settings
  # Complete settings will be loaded from state.config (gitignored)
  # Run: terraform init -backend-config="state.config"
  backend "remote" {
    workspaces {
      name = "baller-staging"
    }
  }
  
  # Provider requirements are inherited from the root module
}

module "baller" {
  source = "../.."
  
  # Core settings
  environment = "staging"
  
  # Additional variables can be set in terraform.tfvars
  # Variables not specified here will use root module defaults
}

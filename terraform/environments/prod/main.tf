# Production environment Terraform configuration

terraform {
  # Use partial configuration with minimal settings
  # Complete settings will be loaded from state.config (gitignored)
  # Run: terraform init -backend-config="state.config"
  backend "remote" {
    workspaces {
      name = "baller-prod"
    }
  }
  
  # Provider requirements are inherited from the root module
}

module "baller" {
  source = "../.."
  
  # Core settings
  environment = "prod"
  
  # Additional variables can be set in terraform.tfvars
  # Variables not specified here will use root module defaults
}

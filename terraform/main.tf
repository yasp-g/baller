# Main Terraform configuration file

# Backend configuration for state storage will be configured in environment-specific directories

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.40.0"
    }
  }
  required_version = ">= 1.9.0"
}

# Provider configurations
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = merge(
      var.tags,
      {
        Environment = var.environment
        Project     = var.project
        ManagedBy   = "OpenTofu"
      }
    )
  }
}

# Database module - DynamoDB tables for Baller application
module "database" {
  source = "./modules/database"
  
  # Pass core variables
  environment = var.environment
  project     = var.project
  aws_region  = var.aws_region
  tags        = var.tags
  
  # Pass DynamoDB-specific variables
  table_billing_mode         = var.dynamodb_billing_mode
  enable_encryption          = var.dynamodb_enable_encryption
  enable_point_in_time_recovery = var.dynamodb_enable_point_in_time_recovery
  
  # Other variables will use module defaults or be overridden in environment tfvars
}

# Storage module - S3 buckets for large object storage
module "storage" {
  source = "./modules/storage"
  
  # Pass core variables
  environment = var.environment
  project     = var.project
  aws_region  = var.aws_region
  tags        = var.tags
  
  # Pass S3-specific variables
  versioning_enabled     = var.s3_versioning_enabled
  lifecycle_rules_enabled = var.s3_lifecycle_rules_enabled
  standard_ia_transition_days = var.s3_standard_ia_transition_days
  glacier_transition_days = var.s3_glacier_transition_days
  expiration_days        = var.s3_expiration_days
  
  # Other variables will use module defaults or be overridden in environment tfvars
}

# Search module - OpenSearch for analytics and search
module "search" {
  source = "./modules/search"
  
  # Pass core variables
  environment = var.environment
  project     = var.project
  aws_region  = var.aws_region
  tags        = var.tags
  
  # Pass OpenSearch-specific variables
  opensearch_instance_type = var.opensearch_instance_type
  opensearch_instance_count = var.opensearch_instance_count
  opensearch_ebs_volume_size = var.opensearch_ebs_volume_size
  
  # Other variables will use module defaults or be overridden in environment tfvars
}
